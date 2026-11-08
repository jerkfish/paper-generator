"""P5: cached unofficial reference answers for approved Type D questions."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from src import config
from src.llm import Usage, chat_json_result
from src.subjects.csc429 import pure_usage

TRACKING = config.TRACKING_DIR / "csc429"
BANK = TRACKING / "bank"
QUESTIONS = BANK / "questions"
ASSETS = BANK / "assets"
PLANS = BANK / "plans"
ANSWERS = BANK / "answers.json"
REPORT = BANK / "answers_report.json"

SYSTEM = """You are an experienced CSC429 Computer Organization and Architecture
lecturer writing an UNOFFICIAL model answer for a real past-paper question.
Return one JSON object with exactly:
{
  "answer": "exam-ready answer with a labelled paragraph per subpart",
  "marking": ["1 mark: ...", "..."],
  "confidence": "high" | "medium" | "low",
  "notes": "assumptions, figure/table limitations, or an empty string"
}
Answer every subpart. Allocate the full question mark total. Use correct
computer-organization terminology. If a figure or table is supplied only by
its caption or extracted text, answer what is supported and state the
limitation. Never claim this is an official UTM marking scheme.
"""


def _load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _save(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _payload(question: dict, assets: dict[str, dict]) -> str:
    parts = [
        f"Question id: {question['id']}",
        f"Source paper: {question['source_paper']} page {question['pages']}",
        f"Part: {question['part']}; marks: {question['marks']}",
        f"Topic: {question['topic_primary']}",
        "",
        "Question text:",
        question.get("native_text_blocks", [{}])[0].get("text", ""),
    ]
    for aid in question.get("assets") or []:
        asset = assets.get(aid, {})
        parts.append(
            f"Asset {aid}: kind={asset.get('kind')}; label={asset.get('label')}; "
            f"caption={asset.get('caption')!r}; treatment={asset.get('treatment')}")
        if asset.get("native_table"):
            rows = []
            for row in asset["native_table"].get("rows") or []:
                rows.append(" | ".join(str(cell.get("text", ""))
                                       for cell in row.get("cells") or []))
            parts.append("Native table:\n" + "\n".join(rows))
    parts.extend([
        "",
        "Write the unofficial reference answer and marking points now.",
    ])
    return "\n".join(parts)


def generate(seeds: list[int]) -> dict:
    assets = {path.stem: _load(path, {})
              for path in ASSETS.glob("*.json")}
    selected = []
    seen = set()
    for seed in seeds:
        plan = _load(PLANS / f"seed_{seed:02d}.json", {})
        for slot in plan.get("slots") or []:
            qid = slot["question_id"]
            if qid not in seen:
                seen.add(qid)
                selected.append(qid)
    cache = _load(ANSWERS, {
        "schema_version": 1,
        "subject": "CSC429",
        "unofficial": True,
        "by_qid": {},
    })
    usage = Usage()
    generated = 0
    cached = 0
    flagged = []
    for qid in selected:
        question = _load(QUESTIONS / f"{qid}.json", {})
        fingerprint = str(question.get("content_hash", ""))
        entry = (cache.setdefault("by_qid", {})).get(qid)
        if (entry and entry.get("content_hash") == fingerprint
                and entry.get("answer")):
            cached += 1
            continue
        pure_usage.check()
        call_usage = Usage()
        result = chat_json_result(
            SYSTEM,
            _payload(question, assets),
            model=config.MOCKGEN_MODEL,
            temperature=0.2,
            usage=call_usage,
            max_tokens=1800,
        )
        usage.add(call_usage.prompt_tokens, call_usage.completion_tokens,
                  call_usage.total_tokens, model=call_usage.model)
        data = result.data
        answer = data.get("answer")
        if isinstance(answer, list):
            answer = "\n".join(str(item) for item in answer)
        marking = data.get("marking")
        if isinstance(marking, str):
            marking = [line.strip(" -•") for line in marking.splitlines()
                       if line.strip()]
        elif not isinstance(marking, list):
            marking = []
        marking = [str(point).strip() for point in marking
                   if str(point).strip()]
        entry = {
            "question_id": qid,
            "content_hash": fingerprint,
            "official": False,
            "unofficial": True,
            "model": config.MOCKGEN_MODEL,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "answer": str(answer or "").strip(),
            "marking": marking[:20],
            "confidence": str(data.get("confidence") or "medium").lower(),
            "notes": str(data.get("notes") or "").strip(),
            "needs_human_check": (
                question.get("topic_primary") == "data_representation"),
            "usage": call_usage.as_dict(),
        }
        if not entry["answer"]:
            raise RuntimeError(f"{qid}: empty answer")
        if entry["needs_human_check"]:
            flagged.append(qid)
        cache["by_qid"][qid] = entry
        generated += 1
        _save(ANSWERS, cache)
        pure_usage.record(
            "P5", cost_usd=float(result.usage.cost_usd),
            llm=int(result.usage.calls))
    _save(ANSWERS, cache)
    report = {
        "schema_version": 1,
        "subject": "CSC429",
        "stage": "P5",
        "seeds": seeds,
        "selected_questions": len(selected),
        "generated": generated,
        "cached": cached,
        "flagged_human_check": sorted(flagged),
        "usage": usage.as_dict(),
        "cost_usd": round(usage.cost_usd, 6),
        "official": False,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    _save(REPORT, report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", default="1-3")
    args = parser.parse_args()
    if "-" in args.seeds:
        a, b = args.seeds.split("-")
        seeds = list(range(int(a), int(b) + 1))
    else:
        seeds = [int(value) for value in args.seeds.split(",")]
    print(json.dumps(generate(seeds), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
