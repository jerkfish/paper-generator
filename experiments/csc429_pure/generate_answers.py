"""Generate reference answers for the CSC429 pure-extraction test seed."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import config
from src.llm import Usage, chat_json_result

EXP = Path(__file__).resolve().parents[2] / "outputs" / "experiments" / "csc429_pure_20261106"
QUESTIONS = Path(__file__).with_name("questions.json")
ANSWERS = EXP / "answers.json"
USAGE = EXP / "answer_usage.json"

SYSTEM = """You are a CSC429 Computer Organization and Architecture lecturer.
Write a concise reference answer for the supplied past-paper question. Return
one JSON object with exactly:
{
  "answer": "reference answer with a labelled paragraph per subpart",
  "marking": ["mark allocation point", "..."],
  "notes": "assumptions, especially where the figure/table is only OCR text"
}
Allocate the full marks. Use correct terminology. Do not claim this is an
official UTM marking scheme. If a figure is supplied only as OCR text, state
the assumption; do not invent unseen arrows or labels.
"""


def main() -> None:
    data = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    assets = json.loads((EXP / "asset_manifest.json").read_text(
        encoding="utf-8"))["assets"]
    by_slot: dict[str, list[dict]] = {}
    for asset in assets:
        by_slot.setdefault(asset["slot"], []).append(asset)
    answers = json.loads(ANSWERS.read_text(encoding="utf-8")) if ANSWERS.exists() else {}
    usage = Usage()
    for question in data["questions"]:
        slot = question["slot"]
        if slot in answers and answers[slot].get("answer"):
            continue
        parts = [
            f"Slot {slot}; {question['marks']} marks; source {question['paper_label']} page {question['page']}.",
            "Question text:",
            question.get("text", ""),
        ]
        if question.get("figure_text"):
            parts.append("Native figure text: " + question["figure_text"])
        for subpart in question.get("subparts") or []:
            parts.append(f"{subpart['label']}) [{subpart['marks']} marks] {subpart['text']}")
        for asset in by_slot.get(slot, []):
            parts.append(
                f"Asset {asset['label']} ({asset['kind']}): caption={asset['caption']!r}; "
                f"OCR={asset['ocr_text']!r}")
        for table in question.get("tables") or []:
            parts.append("Table: " + json.dumps(table, ensure_ascii=False))
        result = chat_json_result(
            SYSTEM, "\n".join(parts), model=config.MOCKGEN_MODEL,
            temperature=0.2, usage=usage, max_tokens=1800)
        payload = result.data
        answers[slot] = {
            "answer": str(payload.get("answer", "")).strip(),
            "marking": [str(x).strip() for x in (payload.get("marking") or []) if str(x).strip()],
            "notes": str(payload.get("notes", "")).strip(),
        }
        ANSWERS.write_text(
            json.dumps(answers, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
    USAGE.write_text(json.dumps(usage.as_dict(), indent=2) + "\n",
                     encoding="utf-8")
    print(json.dumps({"answers": len(answers), "usage": usage.as_dict()}, indent=2))


if __name__ == "__main__":
    main()
