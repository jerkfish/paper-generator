"""V4 answer objects for the MAT133 v2 bank.

Answers are drafted by the configured DeepSeek model and labelled
``model_unofficial``.  They are cached per question and aggregated into
``bank/answers.json``.  Numeric verification is a separate pass; nothing is
labelled official unless it came from the supplied scheme.

Run a pilot:
    uv run python -m src.subjects.mat133.answers --limit 3
Run the full approved bank:
    uv run python -m src.subjects.mat133.answers --workers 3 --cost-cap 5
Aggregate cached answers only:
    uv run python -m src.subjects.mat133.answers --aggregate-only
"""
from __future__ import annotations

import argparse
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from src import config
from src.bank.store import BankStore, load_json, save_json
from src.llm import Usage, chat_json_result
from src.subjects.mat133.bank_build import _v1_log_entries
from src.subjects.mat133.papers import SUBJECT

BANK = config.TRACKING_DIR / "mat133" / "v2" / "bank"
ANSWERS_DIR = config.TRACKING_DIR / "mat133" / "v2" / "answers"
RAW_DIR = ANSWERS_DIR / "raw"
REPORT = BANK / "answers_report.json"
LEDGER = ANSWERS_DIR / "cost_ledger.json"
MODEL = config.DEEPSEEK_MODEL

SYSTEM = """You are a MAT133 Pre-Calculus examiner writing a marking scheme.
Solve the real past-paper question exactly as printed.

Return one JSON object:
{
  "subparts": [
    {"label": "a", "answer": "final answer with LaTeX", "working": ["step 1", "step 2"], "confidence": "high|medium|low"}
  ],
  "marking_points": ["1 mark: ...", "1 mark: ..."],
  "confidence": "high|medium|low",
  "assumptions": "anything you had to assume, or an empty string"
}

Rules:
- Cover every printed subpart exactly once, using its printed label.
- Keep the printed marks; do not add or remove subparts.
- Show concise mathematical working, not prose.
- If a figure is needed but not fully readable, state the assumption explicitly.
- Do not invent a figure or a value that is not in the question.
- Do not wrap the JSON in markdown fences.
"""


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _hints(question: dict) -> list[dict]:
    entries = _v1_log_entries(
        str(question.get("source_file") or ""),
        int(question.get("question_no") or 0))
    hints = []
    for label, entry in sorted(entries.items()):
        hints.append({
            "part": label,
            "topic": entry.get("topic", ""),
            "subtopic": entry.get("subtopic", ""),
            "blueprint": entry.get("solution_blueprint") or [],
            "evidence": entry.get("evidence", ""),
            "confidence": entry.get("confidence", ""),
        })
    return hints


def _prompt(question: dict) -> str:
    parts = []
    for part in question.get("parts") or []:
        parts.append({
            "label": part.get("label") or "",
            "marks": part.get("marks"),
            "text": part.get("text") or "",
        })
    payload = {
        "question_id": question["id"],
        "source_paper": question["source_paper"],
        "question_no": question.get("question_no"),
        "marks": question.get("marks"),
        "parts": parts,
        "question_text": question.get("native_text") or "",
        "v1_hints": _hints(question),
    }
    return (
        "Solve this MAT133 question. The printed parts and marks are the "
        "contract; do not add or remove them.\n\n"
        + json.dumps(payload, indent=2, ensure_ascii=False))


def _normalise_labels(value: str) -> str:
    return str(value or "").strip().strip("()").strip().lower()


def _normalise_subparts(question: dict, subparts: list) -> list[dict]:
    """Collapse nested labels (ai, bii, ...) to the printed a/b/c/d parts."""
    expected = [str(part.get("label") or "").lower()
                for part in question.get("parts") or []]
    buckets = {label: {"answers": [], "working": [], "confidence": []}
               for label in expected}
    current = expected[0] if expected else ""
    for row in subparts:
        if not isinstance(row, dict):
            continue
        raw = _normalise_labels(row.get("label"))
        if raw and raw[0] in buckets:
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
    got = [_normalise_labels(row.get("label")) for row in subparts
           if isinstance(row, dict)]
    if got != expected:
        errors.append(f"subpart labels {got} do not match {expected}")
    for row in subparts:
        if not isinstance(row, dict):
            errors.append("subpart is not an object")
            continue
        if not str(row.get("answer") or "").strip():
            errors.append(f"subpart {row.get('label')} has no answer")
        if not row.get("working"):
            errors.append(f"subpart {row.get('label')} has no working")
    if not data.get("marking_points"):
        errors.append("marking_points is empty")
    return errors


def _apply_overrides(by_qid: dict[str, dict]) -> tuple[dict, list[dict]]:
    """Apply reviewed answer corrections kept outside the raw model output.

    Corrections are recorded separately so a cached raw draft is never
    rewritten and every change keeps an audit note.
    """
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
        applied.append({
            "question_id": qid,
            "subpart": label,
            "note": note,
        })
    return by_qid, applied


def _answer_unusable(value) -> bool:
    text = " ".join(str(value or "").lower().split())
    if text.startswith(("cannot determine", "cannot be determined",
                        "insufficient information", "not enough information",
                        "the printed text for part")):
        return True
    return any(phrase in text for phrase in (
        "is missing", "are missing", "missing from", "assuming the missing",
        "assumed the missing", "missing inequality", "missing equation",
        "missing function", "not fully printed", "is not printed",
        "not printed in", "not provided", "not supplied",
        "not fully readable", "unreadable",
    ))


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
        # Long 25-mark answers can exhaust the reasoning budget before the
        # JSON closes.  Retry the same question without thinking so the bank
        # still has a draft; the comparison report marks the weaker source.
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
    answer = {
        "answer_id": f"ANS-{qid}",
        "question_id": qid,
        "subparts": [
            {
                "label": _normalise_labels(row.get("label")),
                "answer": str(row.get("answer") or "").strip(),
                "working": list(row.get("working") or []),
                "marks": next((part.get("marks") for part in
                               question.get("parts") or []
                               if str(part.get("label") or "").lower()
                               == _normalise_labels(row.get("label"))), None),
                "confidence": str(row.get("confidence") or confidence),
            }
            for row in data.get("subparts") or [] if isinstance(row, dict)
        ],
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
    questions = [row for row in store.questions()
                 if row.get("status") == "approved"]
    if question_ids:
        wanted = {code.upper() for code in question_ids}
        questions = [row for row in questions
                     if str(row.get("id")).upper() in wanted]
    questions.sort(key=lambda row: str(row.get("id")))
    if limit is not None:
        questions = questions[:int(limit)]
    return questions


def _targets(tag: str) -> dict[str, Path]:
    if tag == "think":
        return {
            "raw": ANSWERS_DIR / "raw_think",
            "report": BANK / "answers_think_report.json",
            "answers": BANK / "answers_think.json",
            "ledger": ANSWERS_DIR / "cost_ledger_think.json",
        }
    return {"raw": RAW_DIR, "report": REPORT,
            "answers": BANK / "answers.json", "ledger": LEDGER}


def generate(*, limit: int | None = None, workers: int = 3,
             cost_cap: float = 5.0, force: bool = False,
             question_ids: list[str] | None = None,
             thinking: bool = False, tag: str = "") -> dict:
    questions = _questions(limit=limit, question_ids=question_ids)
    paths = _targets(tag)
    paths["raw"].mkdir(parents=True, exist_ok=True)
    total_cost = 0.0
    done = []
    failed = []
    with ThreadPoolExecutor(max_workers=max(1, int(workers))) as pool:
        futures = {pool.submit(generate_one, question, force=force,
                               thinking=thinking, raw_dir=paths["raw"]):
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
    report = aggregate(tag=tag)
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
    save_json(paths["report"], report)
    return report


def aggregate(*, tag: str = "") -> dict:
    paths = _targets(tag)
    store = BankStore(BANK)
    approved = {str(row["id"]): row for row in store.questions()
                if row.get("status") == "approved"}
    by_qid = {}
    usage_total = 0.0
    errors = []
    for qid in sorted(approved):
        path = _raw_path(qid, paths["raw"])
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
        "cost_usd": round(usage_total, 6),
        "model": MODEL,
    }
    save_json(paths["answers"], {
        "schema_version": 2, "subject": SUBJECT, "by_qid": by_qid})
    save_json(paths["report"], report)
    save_json(paths["ledger"], {
        "subject": SUBJECT,
        "model": MODEL,
        "tag": tag or "default",
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
    parser.add_argument("--tag", default="")
    parser.add_argument("--aggregate-only", action="store_true")
    args = parser.parse_args()
    if args.aggregate_only:
        print(json.dumps(aggregate(tag=args.tag), indent=2))
        return
    print(json.dumps(generate(
        limit=args.limit, workers=args.workers, cost_cap=args.cost_cap,
        force=args.force, question_ids=args.questions,
        thinking=args.thinking, tag=args.tag), indent=2))


if __name__ == "__main__":
    main()
