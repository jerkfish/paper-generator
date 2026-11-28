"""V4 answer objects for the ICT502 bank.

Answers are drafted by the configured DeepSeek model and labelled
``model_unofficial``.  They are cached per question and aggregated into
``bank/answers.json``.  No official ICT502 scheme was supplied.

Run a pilot:
    uv run python -m src.subjects.ict502.answers --limit 3
Run the full approved bank:
    uv run python -m src.subjects.ict502.answers --workers 3 --cost-cap 5
Aggregate cached answers only:
    uv run python -m src.subjects.ict502.answers --aggregate-only
"""
from __future__ import annotations

import argparse
import html
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from src import config
from src.bank.store import BankStore, load_json, save_json
from src.llm import chat_json_result

BANK = config.TRACKING_DIR / "ict502" / "bank"
ANSWERS_DIR = config.TRACKING_DIR / "ict502" / "answers"
RAW_DIR = ANSWERS_DIR / "raw"
REPORT = BANK / "answers_report.json"
LEDGER = ANSWERS_DIR / "cost_ledger.json"
MARKING_OVERRIDES = BANK / "marking_points_overrides.json"
MARKING_REPORT = ANSWERS_DIR / "marking_points_repair.json"
MODEL = config.DEEPSEEK_MODEL
SUBJECT = "ICT502"

SYSTEM = """You are an ICT502 Database Engineering examiner writing a
marking scheme. Solve the real past-paper question exactly as printed.  The
syllabus covers database concepts, data warehouses, the relational model, ERD,
normalization, SQL, query processing, distributed databases, transactions,
concurrency control, recovery and the database development life cycle.

Return one JSON object:
{
  "subparts": [
    {"label": "a", "answer": "final answer", "working": ["step 1", "step 2"], "confidence": "high|medium|low"}
  ],
  "marking_points": ["1 mark: ...", "1 mark: ..."],
  "confidence": "high|medium|low",
  "assumptions": "anything you had to assume, or an empty string"
}

Rules:
- Use only the top-level printed part labels a, b, c, d.  A part that contains
  nested i), ii), iii) items must be answered as one parent part; include the
  nested item answers inside that parent answer.
- If the question has no lettered parts, return one subpart with an empty
  label "".
- Cover every printed part exactly once.  Do not add or remove parts.
- Keep the printed marks; allocate marks to the printed parts only.
- For SQL, give complete runnable SQL.  For relational algebra, use the
  printed operator notation.  For ERD/ROLAP drawings, describe the entities,
  relationships, cardinalities, modalities and keys precisely; use an ASCII
  diagram when it helps.
- Use the supplied asset text for tables, figures and schedules.  If a figure
  is not supplied, state the assumption explicitly instead of inventing data.
- Do not invent a month, a mark, a table value or a figure value.
- Marking points must sum to the question's printed total.
- Do not wrap the JSON in markdown fences.
"""


def _asset_text(asset: dict) -> str:
    name = str(asset.get("owner_recreation_html") or "")
    if name:
        path = BANK / "review" / "owner_recreations" / name
        if path.is_file():
            raw = path.read_text(encoding="utf-8")
            raw = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
            raw = re.sub(r"(?i)</t[dh]>", " | ", raw)
            raw = re.sub(r"(?i)</tr>", "\n", raw)
            raw = re.sub(r"(?s)<[^>]+>", " ", raw)
            text = html.unescape(raw)
            lines = [" ".join(line.split()) for line in text.splitlines()]
            return "\n".join(line for line in lines if line)
    table = str(asset.get("table_html") or "")
    if table:
        text = html.unescape(re.sub(r"<[^>]+>", " ", table))
        return " ".join(text.split())
    parts = [str(asset.get("label") or ""), str(asset.get("caption") or "")]
    return " - ".join(part for part in parts if part)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _prompt(question: dict) -> str:
    parts = [{
        "label": part.get("label") or "",
        "marks": part.get("marks"),
        "text": part.get("text") or "",
        "nested": part.get("nested_labels") or [],
    } for part in question.get("parts") or []]
    payload = {
        "question_id": question["id"],
        "source_paper": question["source_paper"],
        "question_no": question.get("question_no"),
        "marks": question.get("marks"),
        "topic_tags": question.get("topic_tags") or [],
        "parts": parts,
        "question_text": question.get("native_text") or "",
        "assets": [{
            "id": asset.get("id"),
            "kind": asset.get("kind"),
            "label": asset.get("label"),
            "caption": asset.get("caption"),
            "page": asset.get("source_page"),
            "text": _asset_text(asset),
        } for asset in question.get("_asset_records") or []],
    }
    return (
        "Solve this ICT502 Database Engineering question. The printed parts "
        "and marks are the contract; do not add or remove them.\n\n"
        + json.dumps(payload, indent=2, ensure_ascii=False))


def _normalise_labels(value: str) -> str:
    return str(value or "").strip().strip("()").strip().lower()


def _normalise_subparts(question: dict, subparts: list) -> list[dict]:
    expected = [str(part.get("label") or "").lower()
                for part in question.get("parts") or []]
    buckets = {label: {"answers": [], "working": [], "confidence": []}
               for label in expected}
    whole = expected == [""]
    current = expected[0] if expected else ""
    for row in subparts:
        if not isinstance(row, dict):
            continue
        raw = _normalise_labels(row.get("label"))
        if whole:
            current = ""
        elif raw and raw[0] in buckets:
            current = raw[0]
        if current not in buckets:
            continue
        buckets[current]["answers"].append(str(row.get("answer") or "").strip())
        buckets[current]["working"].extend(
            str(line) for line in (row.get("working") or []) if str(line))
        if row.get("confidence"):
            buckets[current]["confidence"].append(str(row["confidence"]))
    normalised = []
    for label in expected:
        bucket = buckets[label]
        answers = [value for value in bucket["answers"] if value]
        normalised.append({
            "label": label,
            "answer": " | ".join(answers),
            "working": bucket["working"],
            "confidence": (bucket["confidence"][0]
                           if bucket["confidence"] else ""),
        })
    return normalised


def _validate(question: dict, data: dict) -> list[str]:
    errors = []
    expected = [str(part.get("label") or "").lower()
                for part in question.get("parts") or []]
    subparts = data.get("subparts")
    if not isinstance(subparts, list) or not subparts:
        return ["model returned no subparts"]
    if expected == [""]:
        got = [""]
    else:
        got = [_normalise_labels(row.get("label")) for row in subparts
               if isinstance(row, dict)]
        if got != expected:
            errors.append(f"subpart labels {got} do not match {expected}")
    by_label = {row.get("label"): row for row in data.get("subparts") or []
                if isinstance(row, dict)}
    for label in expected:
        row = by_label.get(label) or {}
        if not str(row.get("answer") or "").strip():
            errors.append(f"subpart {label or 'whole question'} has no answer")
        if not row.get("working"):
            errors.append(
                f"subpart {label or 'whole question'} has no working")
    if not data.get("marking_points"):
        errors.append("marking_points is empty")
    return errors


def _answer_unusable(value) -> bool:
    text = " ".join(str(value or "").lower().split())
    if text.startswith(("cannot determine", "cannot be determined",
                        "insufficient information", "not enough information")):
        return True
    return any(phrase in text for phrase in (
        "is missing", "are missing", "missing from", "assuming the missing",
        "assumed the missing", "not fully printed", "is not printed",
        "not printed in", "not provided", "not supplied",
        "not fully readable", "unreadable", "cannot specify",
    ))


def _apply_overrides(by_qid: dict[str, dict]) -> tuple[dict, list[dict]]:
    data = load_json(BANK / "answer_overrides.json", {})
    applied = []
    for correction in data.get("corrections") or []:
        qid = str(correction.get("question_id") or "")
        answer = by_qid.get(qid)
        if not answer:
            continue
        label = str(correction.get("subpart") or "").lower()
        row = next((item for item in answer.get("subparts") or []
                    if str(item.get("label") or "").lower() == label), None)
        if row is None:
            continue
        row["answer"] = str(correction.get("answer") or "")
        if correction.get("working") is not None:
            row["working"] = list(correction.get("working") or [])
        answer["reviewed_by"] = str(
            correction.get("reviewed_by") or "assistant consistency review")
        answer["reviewed_on"] = str(
            correction.get("reviewed_on") or _today())
        note = str(correction.get("note") or "").strip()
        if note:
            answer["review_note"] = note
        answer["usable"] = not (
            answer.get("validation_errors")
            or any(_answer_unusable(item.get("answer"))
                   for item in answer.get("subparts") or []))
        applied.append({"question_id": qid, "subpart": label, "note": note})
    return by_qid, applied


def _marking_value(point: str) -> int:
    match = re.search(r"(\d+)\s*marks?", str(point), re.I)
    return int(match.group(1)) if match else 0


def _marking_total(points: list) -> int:
    return sum(_marking_value(point) for point in points)


def _normalise_marking_points(points: list, target: int) -> list[str]:
    """Keep one explicit mark value per point and make the total exact.

    Model-drafted points sometimes contain a second mark phrase ("1 mark each
    (5 marks)" or "— total 4 marks").  Those embedded values make the printed
    scheme ambiguous, so they are removed and the leading values are balanced
    to the question's printed total.
    """
    label_patterns = (
        r"^(part\s*\([a-h]\)(?:\s*\([ivx]+\))?)\s*[:\-—]?\s*",
        r"^(\([a-h]\)(?:\s*\([ivx]+\))?)\s*[:\-—]?\s*",
        r"^([a-h]\s+[ivx]+\))\s*[:\-—]?\s*",
        r"^([a-h]\))\s*[:\-—]?\s*",
        r"^([a-h])\s*:\s*",
    )
    rows: list[list] = []
    for point in points:
        raw = str(point or "").strip()
        body = raw
        prefix = ""
        for pattern in label_patterns:
            match = re.match(pattern, body, re.I)
            if match:
                prefix = match.group(1).strip()
                body = body[match.end():]
                break
        marks = re.search(r"(\d+)\s*marks?", raw, re.I)
        value = int(marks.group(1)) if marks else 1
        body = re.sub(r"^\s*\d+\s*marks?\s*:?\s*", "", body, flags=re.I)
        body = re.sub(r"\(\s*\d+\s*marks?\s*\)", "", body, flags=re.I)
        body = re.sub(r"\b\d+\s*marks?\b", "", body, flags=re.I)
        body = re.sub(r"\s*[—–-]?\s*total\s*[^.]*", "", body, flags=re.I)
        body = " ".join(body.split()).strip(" -—:;,")
        if prefix:
            body = f"{prefix} {body}".strip()
        rows.append([max(1, value), body or "marking point"])
    total = sum(row[0] for row in rows)
    if total < target:
        index = len(rows) - 1
        while total < target and rows:
            rows[index][0] += 1
            total += 1
            index = (index - 1) % len(rows)
    elif total > target:
        for index in range(len(rows) - 1, -1, -1):
            if total <= target:
                break
            cut = min(rows[index][0] - 1, total - target)
            rows[index][0] -= cut
            total -= cut
        while total > target and rows:
            rows.pop()
            total -= 1
    return [
        f"{value} mark{'s' if value != 1 else ''}: {body}"
        for value, body in rows
    ]


def _apply_marking_overrides(by_qid: dict[str, dict]) -> list[dict]:
    data = load_json(MARKING_OVERRIDES, {})
    applied = []
    for qid, points in (data.get("by_qid") or {}).items():
        answer = by_qid.get(qid)
        if not answer or not isinstance(points, list):
            continue
        answer["marking_points"] = [str(point) for point in points]
        applied.append({"question_id": qid,
                        "marks": _marking_total(points)})
    return applied


def _part_level_points(question: dict, answer: dict) -> list[str]:
    """Exact per-part marking allocation when model points do not balance."""
    subparts = {str(row.get("label") or "").lower(): row
                for row in answer.get("subparts") or []}
    points = []
    for part in question.get("parts") or []:
        label = str(part.get("label") or "")
        marks = int(part.get("marks") or 0)
        row = subparts.get(label.lower()) or {}
        text = " ".join(str(row.get("answer") or "").split())
        first = re.split(r"(?<=[.!?])\s+", text, maxsplit=1)[0] if text else ""
        first = first[:220].strip()
        if not first:
            first = "complete correct answer covering the printed part"
        points.append(
            f"{marks} marks: part {label or 'whole question'} — {first}")
    return points


def repair_marking_points(question_ids: list[str] | None = None) -> dict:
    store = BankStore(BANK)
    questions = {str(row["id"]): row for row in store.questions()
                 if row.get("status") == "approved"}
    wanted = {code.upper() for code in question_ids or []}
    overrides = load_json(MARKING_OVERRIDES, {}).get("by_qid") or {}
    repaired = []
    failed = []
    total_cost = 0.0
    for qid in sorted(questions):
        if wanted and qid.upper() not in wanted:
            continue
        path = _raw_path(qid)
        if not path.is_file():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        answer = payload.get("answer") or {}
        points = list(answer.get("marking_points") or [])
        target = int(questions[qid].get("marks") or 0)
        if qid in overrides:
            if _marking_total(overrides[qid]) == target:
                continue
            points = list(overrides[qid])
        elif _marking_total(points) == target:
            continue
        question = questions[qid]
        prompt = json.dumps({
            "question_id": qid,
            "marks": target,
            "parts": [{"label": part.get("label"),
                       "marks": part.get("marks"),
                       "text": part.get("text")}
                      for part in question.get("parts") or []],
            "subparts": answer.get("subparts") or [],
            "current_marking_points": points,
        }, indent=2, ensure_ascii=False)
        system = """You reconcile marking points for an ICT502 Database
Engineering marking scheme. Return one JSON object:
{"marking_points": ["2 marks: ...", "1 mark: ..."]}
Rules:
- Every item starts with an integer mark value and the word mark/marks.
- The leading integer values must sum exactly to the question's printed total.
- Allocate the points across the printed parts; each part's points must sum
  to that part's printed marks.
- Use 1-mark or 2-mark items only.  Do not write any other number followed by
  "mark"/"marks" inside the item text (no "total N marks" phrases).
- Preserve the substance of the current points; split or merge points when
  needed to make the total exact.
- Do not introduce new facts or change the answer.
- Do not wrap the JSON in markdown fences."""
        try:
            result = chat_json_result(
                system, prompt, model=MODEL, temperature=0.0, max_tokens=3000)
            new_points = [str(point) for point in
                          (result.data.get("marking_points") or [])]
            total_cost += result.usage.cost_usd
            if not new_points or _marking_total(new_points) != target:
                raise ValueError(
                    f"marking points total {_marking_total(new_points)} "
                    f"!= {target}")
            overrides[qid] = new_points
            repaired.append({"question_id": qid, "marks": target,
                             "points": len(new_points),
                             "cost_usd": round(result.usage.cost_usd, 6)})
        except Exception as error:
            failed.append({"question_id": qid,
                           "error": f"{type(error).__name__}: {error}",
                           "current_total": _marking_total(points)})
    save_json(MARKING_OVERRIDES, {"subject": SUBJECT,
                                  "generated_on": _now(),
                                  "by_qid": overrides})
    report = {"subject": SUBJECT, "repaired": repaired,
              "failed": failed, "cost_usd": round(total_cost, 6)}
    save_json(MARKING_REPORT, report)
    return report


def _raw_path(qid: str, raw_dir: Path | None = None) -> Path:
    return (raw_dir or RAW_DIR) / f"{qid}.json"


def generate_one(question: dict, *, force: bool = False,
                 thinking: bool = False,
                 raw_dir: Path | None = None) -> dict:
    qid = question["id"]
    path = _raw_path(qid, raw_dir)
    if path.is_file() and not force:
        try:
            cached = json.loads(path.read_text(encoding="utf-8"))
            if cached.get("answer"):
                return cached
        except Exception:
            pass
    try:
        result = chat_json_result(
            SYSTEM, _prompt(question), model=MODEL, temperature=0.1,
            max_tokens=12000 if thinking else 6000, thinking=thinking)
    except Exception:
        if not thinking:
            raise
        result = chat_json_result(
            SYSTEM, _prompt(question), model=MODEL, temperature=0.1,
            max_tokens=8000, thinking=False)
    data = result.data
    data["subparts"] = _normalise_subparts(
        question, data.get("subparts") or [])
    errors = _validate(question, data)
    confidence = str(data.get("confidence") or "low").lower()
    if confidence not in {"high", "medium", "low"}:
        confidence = "low"
    part_marks = {str(part.get("label") or "").lower(): part.get("marks")
                  for part in question.get("parts") or []}
    answer = {
        "answer_id": f"ANS-{qid}",
        "question_id": qid,
        "subparts": [{
            "label": _normalise_labels(row.get("label")),
            "answer": str(row.get("answer") or "").strip(),
            "working": list(row.get("working") or []),
            "marks": part_marks.get(_normalise_labels(row.get("label"))),
            "confidence": str(row.get("confidence") or confidence),
        } for row in data.get("subparts") or [] if isinstance(row, dict)],
        "marking_points": list(data.get("marking_points") or []),
        "provenance": "model_unofficial",
        "confidence": confidence,
        "source": f"model: {result.model}; cached {_today()}",
        "assumptions": str(data.get("assumptions") or "").strip(),
        "reviewed_by": "",
        "reviewed_on": "",
        "validation_errors": errors,
    }
    unusable = bool(errors) or any(
        _answer_unusable(row.get("answer")) for row in answer["subparts"])
    answer["usable"] = not unusable
    answer["usable_reason"] = (
        "incomplete question text or invalid answer" if unusable else "")
    usage = result.usage.as_dict()
    payload = {
        "schema_version": 1,
        "subject": SUBJECT,
        "question_id": qid,
        "generated_on": _now(),
        "model": result.model,
        "attempts": result.attempts,
        "usage": usage,
        "answer": answer,
        "raw": result.raw,
    }
    save_json(path, payload)
    return payload


def _questions(*, limit: int | None = None,
               question_ids: list[str] | None = None) -> list[dict]:
    store = BankStore(BANK)
    assets = {str(row["id"]): row for row in store.assets()}
    questions = []
    for row in store.questions():
        if row.get("status") != "approved":
            continue
        row = dict(row)
        row["_asset_records"] = [assets[aid] for aid in row.get("assets") or []
                                 if aid in assets]
        questions.append(row)
    if question_ids:
        wanted = {code.upper() for code in question_ids}
        questions = [row for row in questions
                     if str(row.get("id")).upper() in wanted]
    questions.sort(key=lambda row: str(row.get("id")))
    if limit is not None:
        questions = questions[:int(limit)]
    return questions


def generate(*, limit: int | None = None, workers: int = 3,
             cost_cap: float = 5.0, force: bool = False,
             question_ids: list[str] | None = None,
             thinking: bool = False) -> dict:
    questions = _questions(limit=limit, question_ids=question_ids)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    total_cost = 0.0
    done = []
    failed = []
    with ThreadPoolExecutor(max_workers=max(1, int(workers))) as pool:
        futures = {pool.submit(generate_one, question, force=force,
                               thinking=thinking, raw_dir=RAW_DIR):
                   question for question in questions}
        for future in as_completed(futures):
            question = futures[future]
            try:
                payload = future.result()
                cost = float((payload.get("usage") or {}).get("cost_usd") or 0)
                total_cost += cost
                done.append(question["id"])
                print(f"{question['id']}: ${cost:.4f}", flush=True)
            except Exception as error:
                failed.append({"question_id": question["id"],
                               "error": f"{type(error).__name__}: {error}"})
                print(f"{question['id']}: FAILED {error}", flush=True)
            if total_cost > cost_cap:
                for pending in futures:
                    pending.cancel()
                break
    report = aggregate()
    report["run"] = {
        "requested": len(questions),
        "done": len(done),
        "failed": failed,
        "run_cost_usd": round(total_cost, 6),
        "cost_cap_usd": cost_cap,
        "workers": workers,
        "thinking": thinking,
        "finished_on": _now(),
    }
    save_json(REPORT, report)
    return report


def aggregate() -> dict:
    store = BankStore(BANK)
    approved = {str(row["id"]): row for row in store.questions()
                if row.get("status") == "approved"}
    by_qid = {}
    usage_total = 0.0
    errors = []
    for qid in sorted(approved):
        path = _raw_path(qid)
        if not path.is_file():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append({"question_id": qid, "error": str(exc)})
            continue
        answer = payload.get("answer") or {}
        if not answer:
            continue
        answer["usable"] = not (
            answer.get("validation_errors")
            or any(_answer_unusable(row.get("answer"))
                   for row in answer.get("subparts") or []))
        answer["usable_reason"] = (
            "incomplete question text or invalid answer"
            if not answer["usable"] else "")
        by_qid[qid] = answer
        usage_total += float((payload.get("usage") or {}).get("cost_usd") or 0)
        for item in answer.get("validation_errors") or []:
            errors.append({"question_id": qid, "error": item})
    by_qid, overrides = _apply_overrides(by_qid)
    marking_overrides = _apply_marking_overrides(by_qid)
    unbalanced = []
    for qid, answer in by_qid.items():
        target = int(approved[qid].get("marks") or 0)
        detailed = list(answer.get("marking_points") or [])
        if _marking_total(detailed) != target:
            unbalanced.append(qid)
            answer["marking_guidance"] = detailed
            answer["marking_points"] = _part_level_points(
                approved[qid], answer)
            answer["marking_points_source"] = "part_allocation"
        else:
            answer["marking_points_source"] = "model_detailed"
        answer["marking_points_total"] = _marking_total(
            answer.get("marking_points") or [])
        answer["marking_points_balanced"] = (
            answer["marking_points_total"] == target)
        answer["marking_allocation"] = [
            {"label": part.get("label"),
             "marks": part.get("marks")}
            for part in approved[qid].get("parts") or []]
    missing = sorted(set(approved) - set(by_qid))
    unusable = sorted(qid for qid, answer in by_qid.items()
                      if not answer.get("usable", True))
    report = {
        "schema_version": 2,
        "subject": SUBJECT,
        "generated_on": _now(),
        "questions": len(approved),
        "answered": len(by_qid),
        "usable": len(by_qid) - len(unusable),
        "unusable": unusable,
        "missing": missing,
        "provenance": {
            "official": 0,
            "solver_verified": 0,
            "model_unofficial": len(by_qid),
            "human_checked": 0,
        },
        "validation_errors": errors,
        "overrides_applied": overrides,
        "marking_point_overrides": marking_overrides,
        "marking_points_replaced_with_part_allocation": unbalanced,
        "cost_usd": round(usage_total, 6),
        "model": MODEL,
    }
    save_json(BANK / "answers.json", {
        "schema_version": 2, "subject": SUBJECT, "by_qid": by_qid})
    save_json(REPORT, report)
    save_json(LEDGER, {
        "subject": SUBJECT,
        "model": MODEL,
        "generated_on": _now(),
        "cost_usd": round(usage_total, 6),
        "questions": len(by_qid),
    })
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--questions", nargs="*", default=None)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--cost-cap", type=float, default=5.0)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--thinking", action="store_true")
    parser.add_argument("--aggregate-only", action="store_true")
    parser.add_argument("--repair-marking-points", action="store_true")
    args = parser.parse_args()
    if args.repair_marking_points:
        print(json.dumps(repair_marking_points(args.questions), indent=2))
        print(json.dumps(aggregate(), indent=2))
        return
    if args.aggregate_only:
        print(json.dumps(aggregate(), indent=2))
        return
    print(json.dumps(generate(
        limit=args.limit, workers=args.workers, cost_cap=args.cost_cap,
        force=args.force, question_ids=args.questions,
        thinking=args.thinking), indent=2))


if __name__ == "__main__":
    main()
