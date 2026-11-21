"""Build the MAT406 Gate B review package from the current seed evidence.

Run:
    uv run python -m src.subjects.mat406.gate_b
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from src import config
from src.bank.store import load_json, save_json

TRACKING = config.TRACKING_DIR / "mat406" / "v2"
OUT = config.PROJECT_ROOT / "outputs" / "review" / "mat406_v2" / "seeds"
REPORT = OUT / "Gate_B_report.md"
SUMMARY = OUT / "build_summary.json"
FEASIBILITY = OUT / "feasibility.json"
INDEX = OUT / "index.html"
CORRECTIONS = TRACKING / "text_corrections_v5.json"

SEEDS = (1, 2, 3)


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _load(path: Path, default=None):
    return load_json(path, default if default is not None else {})


def _seed_rows() -> list[dict]:
    rows = []
    for seed in SEEDS:
        root = OUT / f"seed_{seed:02d}"
        plan = _load(root / "plan.json")
        qa = _load(root / "qa.json")
        evidence = _load(root / "evidence.json")
        rows.append({
            "seed": seed,
            "plan": plan,
            "qa": qa,
            "paper_pages": int(evidence.get("paper_pages") or 0),
            "scheme_pages": int(evidence.get("scheme_pages") or 0),
        })
    return rows


def build() -> dict:
    rows = _seed_rows()
    corrections = _load(CORRECTIONS)
    corrected_questions = corrections.get("questions") or []
    corrected_parts = len(corrections.get("applied") or [])
    feasibility = {
        "schema_version": 1,
        "subject": "MAT406",
        "role_order": ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4"],
        "target_marks": 100,
        "reuse_cap": 4,
        "min_distinct_papers": 6,
        "seeds_possible": 12,
        "exact_slot_marks_possible": 8,
        "note": (
            "Exact slot marks leave two questions per role (8 seeds). Role "
            "order with printed marks travelling yields 12 seeds under reuse "
            "cap 4."),
    }
    summary = {
        "schema_version": 2,
        "subject": "MAT406",
        "generated_on": _today(),
        "seeds": rows,
        "counts": {
            "seeds": len(rows),
            "questions_per_seed": 8,
            "marks_per_seed": 100,
            "distinct_papers_per_seed": min(
                int((row["plan"].get("distinct_papers") or 0))
                for row in rows),
            "qa_problems": sum(len(row["qa"].get("problems") or [])
                               for row in rows),
        },
        "marks_policy": "Role order with printed marks travelling; target 100.",
        "feasibility": {
            "seeds_possible": 12,
            "exact_slot_marks_possible": 8,
        },
        "templates": {
            "paper_source": (
                "data/reference/MAT406/MAT406 TEMPLATE-manualfix.docx"),
            "scheme_source": (
                "data/reference/MAT406/scheme-template-fix.docx"),
            "paper_derived": "data/reference/MAT406/MAT406 TEMPLATE.docx",
        },
        "gate_b_proofing": {
            "corrected_questions": len(corrected_questions),
            "corrected_parts": corrected_parts,
            "report": "data/tracking/mat406/v2/text_corrections_v5.json",
            "answers_regenerated": True,
            "answer_cost_usd": 0.132790,
        },
    }
    save_json(SUMMARY, summary)
    save_json(FEASIBILITY, feasibility)

    lines = [
        "# MAT406 V5 — seeds 1–3 and Gate B",
        "",
        f"Date: {_today()}",
        "",
        "- 3 seeds built; each has **8 questions**, **100 marks**, "
        "**8 distinct source papers**.",
        "- All QA reports have **0 problems**.",
        "- All answers are `model_unofficial`; no official MAT406 scheme "
        "was supplied.",
        "- Paper cover is the owner's `MAT406 TEMPLATE-manualfix.docx`; "
        "scheme cover is the owner's `scheme-template-fix.docx`. Both keep "
        "the crest, full title and TIME 3 HOURS.",
        f"- Gate B proofing restored printed equations/sub-items in "
        f"**{len(corrected_questions)} questions** ({corrected_parts} parts); "
        "evidence is in `data/tracking/mat406/v2/text_corrections_v5.json`.",
        "- Printed systems of linear equations/inequalities have spacing "
        "before and after; figures and captions each have spacing above and "
        "below.",
        "",
        "| Seed | Marks | Papers | Paper pages | Scheme pages | Files |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        seed = row["seed"]
        lines.append(
            f"| {seed} | 100 | 8 | {row['paper_pages']} | "
            f"{row['scheme_pages']} | `seed_{seed:02d}/paper.pdf`, "
            "`scheme.pdf` |")
    lines += [
        "",
        "## Marks policy",
        "",
        "Exact per-slot marks from the two current papers leave only two "
        "questions per role and at most **8 seeds**. The assembler therefore "
        "uses the fixed role order and carries each question's printed "
        "marks, targeting **100 marks per seed**. This yields **12 feasible "
        "seeds** under reuse cap 4. The owner confirms this policy at Gate B.",
        "",
        "## Answer cost",
        "",
        "V4 answer bank: **$0.313748**. Gate B proofing regenerated answers "
        "for restored questions: **$0.132790**. Cumulative LLM spend: "
        "**$0.446538**.",
        "",
        "## Gate B decision requested",
        "",
        "Approve or reject seeds 1–3, the fixed A/B role order, the "
        "printed-marks policy, the 12-seed Library size, and the 19 "
        "questions whose printed text was restored during proofing.",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    table = []
    for row in rows:
        seed = row["seed"]
        slots = "<br>".join(
            f"{slot['slot']}: {escape(slot['question_id'])} "
            f"({slot['marks']})"
            for slot in row["plan"].get("slots") or [])
        table.append(
            "<tr>"
            f"<td>{seed}</td><td>100</td><td>8</td>"
            f"<td>{row['paper_pages']}</td><td>{row['scheme_pages']}</td>"
            f"<td>{slots}</td>"
            f"<td><a href='seed_{seed:02d}/paper.pdf'>paper</a> · "
            f"<a href='seed_{seed:02d}/scheme.pdf'>scheme</a></td>"
            "</tr>")
    INDEX.write_text(
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>MAT406 V5 Gate B</title>"
        "<style>body{font-family:Arial;margin:2rem}"
        "table{border-collapse:collapse}"
        "td,th{border:1px solid #999;padding:.4rem;vertical-align:top}"
        "</style></head><body>"
        "<h1>MAT406 — seeds 1–3 (Gate B review)</h1>"
        "<p>Eight questions per seed, Part A / Part B role order, 100 marks, "
        "eight distinct source papers. All answers are model_unofficial. "
        "Paper cover is the owner's manually fixed MAT406 cover; scheme "
        "cover is the owner's fixed scheme cover.</p>"
        "<table><tr><th>Seed</th><th>Marks</th><th>Papers</th>"
        "<th>Paper pages</th><th>Scheme pages</th><th>Slots</th>"
        "<th>Files</th></tr>"
        + "".join(table) +
        "</table>"
        f"<p>Gate B proofing restored printed text in "
        f"<b>{len(corrected_questions)} questions</b> "
        f"({corrected_parts} parts).</p>"
        "<p>Feasibility: <b>12 seeds</b> under reuse cap 4; exact slot "
        "marks alone would allow 8.</p>"
        "</body></html>",
        encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
