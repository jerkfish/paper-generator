"""Compare the two MAT133 answer drafts question by question.

The ordinary V4 run uses the model with thinking disabled; the review run
uses the same model with thinking enabled.  Agreement is evidence, not proof:
disagreements are listed for manual review before assembly.

Run:
    uv run python -m src.subjects.mat133.answers_compare
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from src import config
from src.bank.store import load_json, save_json

BANK = config.TRACKING_DIR / "mat133" / "v2" / "bank"
OUT = BANK / "answers_compare.json"
REPORT = BANK / "answers_compare.md"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _clean(value: str) -> str:
    text = str(value or "")
    text = re.sub(r"\\\(|\\\)|\\\[|\\\]", "", text)
    text = text.replace("$", "")
    text = re.sub(r"\\left|\\right", "", text)
    text = re.sub(r"\\dfrac|\\tfrac", r"\\frac", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def _numbers(value: str) -> list[str]:
    return re.findall(r"-?\d+(?:\.\d+)?", _clean(value))


def _agree(left: str, right: str) -> bool:
    a, b = _clean(left), _clean(right)
    if not a or not b:
        return False
    if a == b:
        return True
    if a in b or b in a:
        return True
    na, nb = _numbers(left), _numbers(right)
    return bool(na) and na == nb


def compare() -> dict:
    flash = load_json(BANK / "answers.json", {}).get("by_qid") or {}
    think = load_json(BANK / "answers_think.json", {}).get("by_qid") or {}
    rows = []
    agree = 0
    differ = 0
    missing = []
    for qid in sorted(set(flash) | set(think)):
        a = flash.get(qid) or {}
        b = think.get(qid) or {}
        if not a or not b:
            missing.append(qid)
            continue
        a_parts = {str(row.get("label")): row.get("answer") or ""
                   for row in a.get("subparts") or []}
        b_parts = {str(row.get("label")): row.get("answer") or ""
                   for row in b.get("subparts") or []}
        labels = sorted(set(a_parts) | set(b_parts))
        part_rows = []
        for label in labels:
            same = _agree(a_parts.get(label, ""), b_parts.get(label, ""))
            if same:
                agree += 1
            else:
                differ += 1
            part_rows.append({
                "label": label,
                "agree": same,
                "flash": a_parts.get(label, ""),
                "think": b_parts.get(label, ""),
            })
        rows.append({
            "question_id": qid,
            "flash_usable": bool(a.get("usable")),
            "think_usable": bool(b.get("usable")),
            "agree": all(row["agree"] for row in part_rows),
            "parts": part_rows,
        })
    report = {
        "schema_version": 1,
        "generated_on": _now(),
        "questions": len(rows),
        "fully_agree": sum(1 for row in rows if row["agree"]),
        "questions_with_disagreement": sum(
            1 for row in rows if not row["agree"]),
        "parts_agree": agree,
        "parts_differ": differ,
        "missing": missing,
        "rows": rows,
    }
    save_json(OUT, report)
    lines = [
        "# MAT133 answer draft comparison",
        "",
        f"Generated: {_now()}",
        "",
        f"- Questions compared: {len(rows)}",
        f"- Full agreement: {report['fully_agree']}",
        f"- With disagreement: {report['questions_with_disagreement']}",
        f"- Parts agree: {agree}, differ: {differ}",
        "",
        "Agreement is supporting evidence only. Disagreements must be",
        "resolved before a question enters a reviewed seed.",
        "",
        "## Disagreements",
        "",
    ]
    for row in rows:
        if row["agree"]:
            continue
        lines.append(f"### {row['question_id']}")
        for part in row["parts"]:
            if part["agree"]:
                continue
            lines += [
                f"- **{part['label']}**",
                f"  - flash: {part['flash']}",
                f"  - think: {part['think']}",
            ]
        lines.append("")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    report = compare()
    print(json.dumps({
        "questions": report["questions"],
        "fully_agree": report["fully_agree"],
        "questions_with_disagreement":
            report["questions_with_disagreement"],
        "parts_agree": report["parts_agree"],
        "parts_differ": report["parts_differ"],
        "report": str(REPORT),
    }, indent=2))


if __name__ == "__main__":
    main()
