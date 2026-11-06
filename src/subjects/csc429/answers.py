"""Unofficial model answers for real CSC429 past-paper questions.

The owner authorised unofficial model answers for the real-question bank.
Answers are generated once per question, cached by question id and question
fingerprint, and always labelled as unofficial.  They are not an official UTM
marking scheme and must not be presented as one.

    uv run python -m src.subjects.csc429.answers --seed 1
    uv run python -m src.subjects.csc429.answers --all
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from src import config
from src.llm import Usage, chat_json_result

SUBJECT = "CSC429"
PROMPT_VERSION = 1
CACHE_PATH = config.TRACKING_DIR / "csc429" / "model_answers.json"
DEFAULT_MODEL = config.MOCKGEN_MODEL

SYSTEM_PROMPT = """You are an experienced CSC429 Computer Organization and \
Architecture lecturer writing an UNOFFICIAL model answer for a past-paper \
question. Return one JSON object only, with exactly these keys:

{
  "answer": "exam-ready model answer, with a labelled paragraph for every \
subpart that appears in the question",
  "marking": ["1 mark: ...", "2 marks: ..."],
  "confidence": "high" | "medium" | "low",
  "notes": "assumptions or figure/table limitations, or an empty string"
}

Rules:
- Answer every subpart that is present. Do not invent extra blank labels.
- The marking list must allocate the full question mark total.
- Use correct computer-organization terminology and show working where the \
question asks for a calculation, conversion, program or diagram explanation.
- The question may contain OCR errors. Make only conservative corrections and \
state any assumption in notes.
- If a figure or table is needed but only its extracted text is available, \
answer what the text supports and state what must be read from the figure.
- Never claim this is an official marking scheme.
"""


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_cache() -> dict:
    if not CACHE_PATH.exists():
        return {
            "subject": SUBJECT,
            "schema_version": 1,
            "prompt_version": PROMPT_VERSION,
            "model": DEFAULT_MODEL,
            "entries": {},
            "usage": Usage().as_dict(),
        }
    try:
        payload = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        payload = {}
    payload.setdefault("subject", SUBJECT)
    payload.setdefault("schema_version", 1)
    payload.setdefault("prompt_version", PROMPT_VERSION)
    payload.setdefault("model", DEFAULT_MODEL)
    payload.setdefault("entries", {})
    payload.setdefault("usage", Usage().as_dict())
    return payload


def _save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = CACHE_PATH.with_suffix(".tmp.json")
    temporary.write_text(
        json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(CACHE_PATH)


def _table_text(block: dict) -> str:
    table = block.get("table") or {}
    rows = []
    for row in table.get("rows") or []:
        cells = [str(cell.get("text", "")).strip()
                 for cell in row.get("cells") or []]
        rows.append(" | ".join(cells))
    return "\n".join(rows)


def _payload(slot: dict) -> str:
    """Build the stable question payload used for prompting and cache keys."""
    parts = [
        f"Question id: {slot.get('question_id', '')}",
        f"Source paper: {slot.get('paper_id', '')}",
        f"Slot: {slot.get('slot', '')} ({slot.get('marks', '')} marks)",
        f"Topic: {slot.get('topic_label') or slot.get('topic', '')}",
        "",
        "Question text:",
        str(slot.get("text", "")).strip(),
    ]
    subparts = []
    for subpart in slot.get("subparts") or []:
        label = str(subpart.get("label", "")).strip()
        text = str(subpart.get("text", "")).strip()
        marks = subpart.get("marks")
        if not text or label == "main" and text == str(slot.get("text", "")).strip():
            continue
        subparts.append(f"({label}) {text}" + (f" [{marks} marks]" if marks else ""))
    if subparts:
        parts.extend(["", "Subparts:", "\n".join(subparts)])
    tables = []
    figures = []
    for block in slot.get("content") or []:
        if block.get("type") == "table":
            table = _table_text(block)
            if table:
                tables.append(
                    f"{block.get('asset_id', 'table')}:\n{table}")
        elif block.get("type") == "figure":
            figures.append(str(block.get("asset_id", "figure")))
    if figures:
        parts.extend(["", "Figure assets present: " + ", ".join(figures)])
    if tables:
        parts.extend(["", "Extracted table text:", "\n\n".join(tables)])
    parts.extend([
        "",
        "Write the unofficial model answer and marking guide now.",
    ])
    return "\n".join(parts)


def _fingerprint(slot: dict) -> str:
    return _sha(_payload(slot))


def _normalise(result: dict, marks: int) -> dict:
    answer = result.get("answer")
    if isinstance(answer, list):
        answer = "\n".join(str(item) for item in answer)
    answer = str(answer or "").strip()
    marking = result.get("marking")
    if isinstance(marking, str):
        marking = [line.strip(" -•") for line in marking.splitlines()
                   if line.strip()]
    elif isinstance(marking, dict):
        marking = [f"{key}: {value}" for key, value in marking.items()]
    elif not isinstance(marking, list):
        marking = []
    marking = [str(point).strip() for point in marking if str(point).strip()]
    confidence = result.get("confidence")
    if isinstance(confidence, (int, float)):
        confidence = ("high" if confidence >= 0.75
                      else "medium" if confidence >= 0.5 else "low")
    confidence = str(confidence or "medium").lower()
    if confidence not in {"high", "medium", "low"}:
        confidence = "medium"
    return {
        "answer": answer,
        "marking": marking[:20],
        "confidence": confidence,
        "notes": str(result.get("notes") or "").strip(),
        "marks": int(marks),
    }


def _generate(slot: dict, *, model: str) -> tuple[dict, Usage]:
    usage = Usage()
    result = chat_json_result(
        SYSTEM_PROMPT,
        _payload(slot),
        model=model,
        temperature=0.2,
        usage=usage,
        max_tokens=1800,
    )
    return _normalise(result.data, int(slot.get("marks") or 0)), usage


def ensure_answers(slots: list[dict], *, allow_llm: bool = True,
                   strict: bool = True, model: str | None = None,
                   force: bool = False) -> dict:
    """Attach cached or freshly generated unofficial answers to real slots.

    The cache is shared by all seeds and keyed by question id.  A changed
    question fingerprint invalidates the entry.
    """
    cache = _load_cache()
    chosen_model = model or cache.get("model") or DEFAULT_MODEL
    usage = Usage()
    report = {
        "model": chosen_model,
        "prompt_version": PROMPT_VERSION,
        "requested": 0,
        "cache_hits": 0,
        "generated": 0,
        "failed": 0,
        "errors": [],
        "usage": {},
    }
    entries = cache.setdefault("entries", {})
    for slot in slots:
        if slot.get("kind") != "real_bank_question":
            continue
        report["requested"] += 1
        question_id = str(slot.get("question_id") or "")
        fingerprint = _fingerprint(slot)
        entry = entries.get(question_id)
        if (not force and entry
                and entry.get("prompt_version") == PROMPT_VERSION
                and entry.get("fingerprint") == fingerprint
                and entry.get("answer")):
            slot["model_answer"] = {
                key: entry.get(key)
                for key in ("answer", "marking", "confidence", "notes",
                            "model", "generated_at", "usage", "reviewed",
                            "review_note")
            }
            slot["model_answer"]["unofficial"] = True
            report["cache_hits"] += 1
            continue
        if not allow_llm:
            report["failed"] += 1
            report["errors"].append(
                f"{question_id}: no cached answer and LLM disabled")
            continue
        try:
            answer, call_usage = _generate(slot, model=chosen_model)
        except Exception as error:
            report["failed"] += 1
            report["errors"].append(f"{question_id}: {error}")
            continue
        if not answer["answer"]:
            report["failed"] += 1
            report["errors"].append(f"{question_id}: empty model answer")
            continue
        generated_at = datetime.now(timezone.utc).isoformat()
        entry = {
            "question_id": question_id,
            "paper_id": slot.get("paper_id", ""),
            "fingerprint": fingerprint,
            "prompt_version": PROMPT_VERSION,
            "model": chosen_model,
            "generated_at": generated_at,
            "unofficial": True,
            **answer,
            "usage": call_usage.as_dict(),
        }
        entries[question_id] = entry
        slot["model_answer"] = {
            key: entry.get(key)
            for key in ("answer", "marking", "confidence", "notes",
                        "model", "generated_at", "usage", "reviewed",
                        "review_note")
        }
        slot["model_answer"]["unofficial"] = True
        usage.add(call_usage.prompt_tokens, call_usage.completion_tokens,
                  call_usage.total_tokens, model=chosen_model)
        report["generated"] += 1
        # Persist the cost with the answer so an interrupted run cannot lose
        # the spend record.
        previous = cache.get("usage") or {}
        cache["usage"] = {
            "model": chosen_model,
            "calls": int(previous.get("calls", 0)) + call_usage.calls,
            "prompt_tokens": int(previous.get("prompt_tokens", 0))
            + call_usage.prompt_tokens,
            "completion_tokens": int(previous.get("completion_tokens", 0))
            + call_usage.completion_tokens,
            "total_tokens": int(previous.get("total_tokens", 0))
            + call_usage.total_tokens,
            "cost_usd": round(float(previous.get("cost_usd", 0.0))
                              + call_usage.cost_usd, 6),
        }
        cache["model"] = chosen_model
        _save_cache(cache)
    cache["model"] = chosen_model
    _save_cache(cache)
    report["usage"] = usage.as_dict()
    report["cache_usage"] = cache["usage"]
    report["cost_usd"] = round(usage.cost_usd, 6)
    if strict and report["failed"]:
        raise RuntimeError(
            "unofficial model-answer generation failed: "
            + "; ".join(report["errors"][:5]))
    return report


def summary() -> dict:
    cache = _load_cache()
    entries = cache.get("entries") or {}
    return {
        "path": str(CACHE_PATH),
        "model": cache.get("model"),
        "prompt_version": cache.get("prompt_version"),
        "cached_answers": len(entries),
        "usage": cache.get("usage", {}),
        "confidence": {
            level: sum(1 for entry in entries.values()
                       if entry.get("confidence") == level)
            for level in ("high", "medium", "low")
        },
    }


def _load_slots(seed: int | None) -> list[dict]:
    if seed is None:
        from src.subjects.csc429 import build_docx
        bank = build_docx._load(build_docx.BANK_PATH)
        log = build_docx._load(build_docx.LOG_PATH)
        entries = {entry["question_id"]: entry
                   for entry in log["entries"]}
        assets = build_docx.pilot._asset_index(
            build_docx._load(build_docx.ASSETS_PATH))
        layouts = build_docx.pilot._layout_index()
        slots = []
        for question in bank["questions"]:
            entry = entries.get(question["question_id"], {})
            slots.append({
                "kind": "real_bank_question",
                "question_id": question["question_id"],
                "paper_id": question["paper_id"],
                "slot": question.get("slot", ""),
                "marks": question.get("marks", 0),
                "topic": entry.get("topic", ""),
                "topic_label": entry.get("topic_label", ""),
                "text": question.get("text", ""),
                "subparts": question.get("subparts", []),
                "content": build_docx.pilot.build_content(
                    question, assets, layouts),
            })
        return slots
    from src.subjects.csc429 import planner
    from src.subjects.csc429 import build_docx
    plan = planner.build_plan(seed)
    bank = build_docx._load(build_docx.BANK_PATH)
    log = build_docx._load(build_docx.LOG_PATH)
    assets = build_docx.pilot._asset_index(
        build_docx._load(build_docx.ASSETS_PATH))
    layouts = build_docx.pilot._layout_index()
    slots, _ = build_docx._resolved_slots(
        seed, plan, bank, log, assets, layouts)
    return slots


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    slots = _load_slots(None if args.all else (args.seed or 1))
    report = ensure_answers(slots, allow_llm=True, strict=True,
                            force=args.force)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
