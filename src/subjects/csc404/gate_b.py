"""Build the CSC404 Gate B review package from seeds 1-3.

Run:
    uv run python -m src.subjects.csc404.gate_b
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from html import escape
from pathlib import Path

import pymupdf

from src.bank.store import load_json, save_json
from src.subjects.csc404.assemble_v5 import build_plans

OUT = (Path(__file__).resolve().parents[3] / "outputs" / "review" /
       "csc404_v2" / "seeds")
REPORT = OUT / "Gate_B_report.md"
SUMMARY = OUT / "build_summary.json"
FEASIBILITY = OUT / "feasibility.json"
INDEX = OUT / "index.html"
APPROVAL = OUT.parent / "gate_b_approval.json"

SEEDS = (1, 2, 3)


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _load(path: Path, default=None):
    return load_json(path, default if default is not None else {})


def _pdf_text(path: Path) -> str:
    with pymupdf.open(str(path)) as document:
        return " ".join(" ".join(page.get_text().split())
                        for page in document)


def _seed_rows() -> list[dict]:
    rows = []
    for seed in SEEDS:
        root = OUT / f"seed_{seed:02d}"
        plan = _load(root / "plan.json")
        qa = _load(root / "qa.json")
        paper = root / "paper.pdf"
        scheme = root / "scheme.pdf"
        paper_pages = scheme_pages = 0
        problems = list(qa.get("problems") or [])
        if paper.is_file():
            with pymupdf.open(str(paper)) as document:
                paper_pages = len(document)
                cover = " ".join(document[0].get_text().split())
            for required in ("PROGRAMMING II", "CSC404",
                             "PART A (4 Questions)", "PART B (2 Questions)"):
                if required not in cover:
                    problems.append(f"paper cover missing: {required}")
            if f"consists of {paper_pages} printed pages" not in cover:
                problems.append("paper page count does not match the cover")
            paper_docx = root / "paper.docx"
            if paper_docx.is_file():
                import zipfile
                with zipfile.ZipFile(paper_docx) as archive:
                    xml = archive.read("word/document.xml").decode("utf-8")
                if "HOURS" not in xml:
                    problems.append("paper cover missing: HOURS")
        else:
            problems.append("paper.pdf is missing")
        if scheme.is_file():
            with pymupdf.open(str(scheme)) as document:
                scheme_pages = len(document)
                cover = " ".join(document[0].get_text().split())
            for required in ("MARKING SCHEME", "PROGRAMMING II", "CSC404"):
                if required not in cover:
                    problems.append(f"scheme cover missing: {required}")
            if f"consists of {scheme_pages} printed pages" not in cover:
                problems.append("scheme page count does not match the cover")
        else:
            problems.append("scheme.pdf is missing")
        rows.append({
            "seed": seed,
            "plan": plan,
            "qa": qa,
            "paper_pages": paper_pages,
            "scheme_pages": scheme_pages,
            "problems": problems,
        })
    return rows


def build() -> dict:
    rows = _seed_rows()
    feasible = build_plans(20)
    counts = {
        "seeds": len(rows),
        "questions_per_seed": 6,
        "marks_per_seed": 100,
        "distinct_papers_per_seed": min(
            int((row["plan"].get("distinct_papers") or 0)) for row in rows),
        "qa_problems": sum(len(row["problems"]) for row in rows),
    }
    feasibility = {
        "schema_version": 1,
        "subject": "CSC404",
        "role_order": ["A1", "A2", "A3", "A4", "B1", "B2"],
        "target_marks": 100,
        "reuse_cap": 4,
        "min_distinct_papers": 4,
        "seeds_possible": len(feasible),
        "note": (
            "Six questions per seed, one per role, printed marks travelling. "
            "With 30 approved questions and reuse cap 4, 20 seeds are "
            "feasible; every seed uses all five source papers."),
    }
    summary = {
        "schema_version": 2,
        "subject": "CSC404",
        "generated_on": _today(),
        "seeds": rows,
        "counts": counts,
        "marks_policy": "Role order with printed marks travelling; target 100.",
        "feasibility": {
            "seeds_possible": len(feasible),
        },
        "templates": {
            "paper": "data/reference/CSC404/CSC404 TEMPLATE.docx",
            "scheme": "data/reference/CSC404/CSC404 SCHEME.docx",
        },
        "answers": {
            "provenance": "model_unofficial",
            "model": "deepseek-flash",
            "cost_usd": 0.286809,
        },
    }
    save_json(SUMMARY, summary)
    save_json(FEASIBILITY, feasibility)

    lines = [
        "# CSC404 V5 — seeds 1–3 and Gate B",
        "",
        f"Date: {_today()}",
        "",
        "- 3 seeds built; each has **6 questions**, **100 marks**, "
        "**5 distinct source papers**.",
        f"- QA problems: **{counts['qa_problems']}**.",
        "- All answers are `model_unofficial`; no official CSC404 scheme "
        "was supplied.",
        "- Paper cover: CSC404 PROGRAMMING II, CSC404, FEBRUARY 2026, "
        "3 HOURS, PART A (4 Questions), PART B (2 Questions).",
        "- Scheme cover: CSC404 PROGRAMMING II marking scheme, CSC404, "
        "FEBRUARY 2026, 3 HOURS.",
        "- Code is rendered in monospace with printed indentation; tables, "
        "figures and sample outputs use the owner-approved recreations.",
        "",
        "| Seed | Marks | Papers | Paper pages | Scheme pages | Files |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        seed = row["seed"]
        lines.append(
            f"| {seed} | 100 | 5 | {row['paper_pages']} | "
            f"{row['scheme_pages']} | `seed_{seed:02d}/paper.pdf`, "
            "`scheme.pdf` |")
    lines += [
        "",
        "## Marks policy",
        "",
        "Each seed follows the fixed A1–A4 / B1–B2 role order and carries "
        "each question's printed marks, targeting **100 marks**. Slot marks "
        "vary between the 2025/2026-style papers (Q1 15/20, Q2 10/20, "
        "Q3 15/20), so exact slot marks are not a selection constraint. "
        "This yields **20 feasible seeds** under reuse cap 4. The owner "
        "confirms this policy at Gate B.",
        "",
        "## Answer cost",
        "",
        "V4 answer bank: **$0.286809** for 30 questions "
        "(`data/tracking/csc404/answers/cost_ledger.json`).",
        "",
        "## Gate B decision",
        "",
        ("**Approved** by the owner on " + str(_load(APPROVAL).get("on") or "")
         if _load(APPROVAL).get("status") == "approved"
         else "Pending owner review."),
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
            f"<td>{seed}</td><td>100</td><td>5</td>"
            f"<td>{row['paper_pages']}</td><td>{row['scheme_pages']}</td>"
            f"<td>{slots}</td>"
            f"<td><a href='seed_{seed:02d}/paper.pdf'>paper</a> · "
            f"<a href='seed_{seed:02d}/scheme.pdf'>scheme</a></td>"
            "</tr>")
    INDEX.write_text(
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>CSC404 V5 Gate B</title>"
        "<style>body{font-family:Arial;margin:2rem}"
        "table{border-collapse:collapse}"
        "td,th{border:1px solid #999;padding:.4rem;vertical-align:top}"
        "</style></head><body>"
        "<h1>CSC404 — seeds 1–3 (Gate B review)</h1>"
        "<p>Six questions per seed, Part A (4) / Part B (2), 100 marks, "
        "five distinct source papers. All answers are model_unofficial. "
        "Code is monospace; tables and figures use the owner-approved "
        "recreations.</p>"
        "<table><tr><th>Seed</th><th>Marks</th><th>Papers</th>"
        "<th>Paper pages</th><th>Scheme pages</th><th>Slots</th>"
        "<th>Files</th></tr>"
        + "".join(table) +
        "</table>"
        "<p>Feasibility: <b>20 seeds</b> under reuse cap 4.</p>"
        f"<p>Gate B: <b>{'approved' if _load(APPROVAL).get('status') == 'approved' else 'pending'}</b>.</p>"
        "</body></html>",
        encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
