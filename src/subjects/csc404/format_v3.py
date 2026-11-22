"""V3 format profile and template check for CSC404.

The current format is the 2023-2026 shape: 3 hours, Part A (4 questions),
Part B (2 questions), 100 printed marks.  Slot marks vary between the two
2025/2026-style papers, so the assembler will use the fixed role order and
carry each question's printed marks, targeting 100 marks per seed.  The owner
confirms this policy at Gate B.

Run:
    uv run python -m src.subjects.csc404.format_v3
"""
from __future__ import annotations

import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pymupdf

from src import config
from src.assemble.pdf_export import export_pdf
from src.subjects.templates import check_template

TRACKING = config.TRACKING_DIR / "csc404"
FORMAT = TRACKING / "format_profile.json"
CHECK = TRACKING / "template_check.json"
PREVIEW = TRACKING / "templates_preview"

PAPER_TEMPLATE = config.subject_reference_dir("CSC404") / "CSC404 TEMPLATE.docx"
SCHEME_TEMPLATE = config.subject_reference_dir("CSC404") / "CSC404 SCHEME.docx"

SLOT_ROLES = {
    "A1": {
        "role": "pointers_and_functions",
        "topics": ["pointers", "functions"],
        "observed_marks": [20, 20, 20, 15, 15],
        "source_examples": ["CSC404-2026-FEB-Q1", "CSC404-2025-JUL-Q1"],
    },
    "A2": {
        "role": "arrays_and_2d_arrays",
        "topics": ["arrays"],
        "observed_marks": [10, 10, 10, 20, 20],
        "source_examples": ["CSC404-2026-FEB-Q2", "CSC404-2025-JUL-Q2"],
    },
    "A3": {
        "role": "arrays_and_functions",
        "topics": ["arrays", "functions"],
        "observed_marks": [20, 20, 20, 15, 15],
        "source_examples": ["CSC404-2026-FEB-Q3", "CSC404-2025-JUL-Q3"],
    },
    "A4": {
        "role": "structs_and_file_io",
        "topics": ["structs", "file_io"],
        "observed_marks": [20, 20, 20, 20, 20],
        "source_examples": ["CSC404-2026-FEB-Q4", "CSC404-2025-JUL-Q4"],
    },
    "B1": {
        "role": "file_io_and_pointers",
        "topics": ["file_io", "pointers", "structs"],
        "observed_marks": [15, 15, 15, 15, 15],
        "source_examples": ["CSC404-2026-FEB-Q1-2", "CSC404-2025-JUL-Q1-2"],
    },
    "B2": {
        "role": "functions_structs_arrays",
        "topics": ["functions", "structs", "arrays", "pointers"],
        "observed_marks": [15, 15, 15, 15, 15],
        "source_examples": ["CSC404-2026-FEB-Q2-2", "CSC404-2025-JUL-Q2-2"],
    },
}


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def format_profile() -> dict:
    profile = {
        "schema_version": 2,
        "playbook_version": "2.0",
        "subject": "CSC404",
        "era": "current",
        "source_papers": ["CSC404-2026-FEB", "CSC404-2025-JUL"],
        "sections": [
            {
                "key": "A",
                "questions": 4,
                "numbering": "PART A; QUESTION 1..4; a), b), c); i., ii.",
                "slots": ["A1", "A2", "A3", "A4"],
            },
            {
                "key": "B",
                "questions": 2,
                "numbering": "PART B; QUESTION 1..2; a), b), c); i., ii.",
                "slots": ["B1", "B2"],
            },
        ],
        "slot_roles": SLOT_ROLES,
        "total_marks": 100,
        "duration": "3 HOURS",
        "numbering": {
            "part": "PART A / PART B",
            "question": "QUESTION n (restarts in Part B)",
            "subparts": "a), b), c), d)",
            "nested": "i), ii), iii)",
        },
        "cover_template": "data/reference/CSC404/CSC404 TEMPLATE.docx",
        "scheme_template": "data/reference/CSC404/CSC404 SCHEME.docx",
        "marks_policy": {
            "selection": "role_order",
            "slot_marks": "printed marks travel; not a fixed slot constraint",
            "target_total_marks": 100,
            "basis": (
                "The five current papers total 100 marks, but slot marks vary "
                "(Q1 15/20, Q2 10/20, Q3 15/20). Exact slot matching leaves "
                "only one question per role for the 2025/2026 papers. The "
                "assembler carries each question's printed marks and targets "
                "100 per seed. The owner confirms this policy at Gate B."),
            "owner_review": "Gate B",
        },
        "slot_policy": {
            "question_reuse_within_paper": "never",
            "topic_policy": "fixed A/B role order; marks carried from source",
            "source_paper_distinctness": "prefer distinct source papers",
        },
        "older_era": {
            "note": ("The 2014-2019 papers use Part A True/False, Part B MCQ "
                     "and Part C/D structured questions. They are not banked "
                     "for the current 4+2 format."),
            "examples": ["CSC404-2019-DEC", "CSC404-2014-DEC"],
        },
        "checked_on": _today(),
    }
    FORMAT.parent.mkdir(parents=True, exist_ok=True)
    FORMAT.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    return profile


def _render_cover(docx_path: Path, name: str) -> str:
    PREVIEW.mkdir(parents=True, exist_ok=True)
    pdf = PREVIEW / f"{name}.pdf"
    png = PREVIEW / f"{name}_page_1.png"
    export_pdf(docx_path, pdf)
    with pymupdf.open(str(pdf)) as document:
        page = document[0]
        page.get_pixmap(dpi=110).save(str(png))
    return str(png)


def _pdf_text(path: Path) -> str:
    with pymupdf.open(str(path)) as document:
        if not len(document):
            return ""
        return " ".join(document[0].get_text().split())


def template_check() -> dict:
    paper = check_template(PAPER_TEMPLATE)
    scheme = check_template(SCHEME_TEMPLATE)
    paper["cover_render"] = _render_cover(PAPER_TEMPLATE, "paper_template")
    scheme["cover_render"] = _render_cover(SCHEME_TEMPLATE, "scheme_template")
    text = _pdf_text(PREVIEW / "paper_template.pdf")
    scheme_text = _pdf_text(PREVIEW / "scheme_template.pdf")
    problems = list(paper.get("problems") or []) + list(
        scheme.get("problems") or [])
    for required in ("PROGRAMMING II", "CSC404", "FEBRUARY 2026",
                     "PART A (4 Questions)", "PART B (2 Questions)"):
        if required not in text:
            problems.append(f"paper cover is missing: {required}")
    with zipfile.ZipFile(PAPER_TEMPLATE) as archive:
        paper_xml = archive.read("word/document.xml").decode("utf-8")
    if "HOURS" not in paper_xml:
        problems.append("paper cover is missing: HOURS")
    if not re.search(r">\s*3\s*<(?:(?!</w:p>).)*?HOURS", paper_xml, re.S):
        problems.append("paper cover is missing: TIME 3")
    for required in ("MARKING SCHEME", "PROGRAMMING II", "CSC404",
                     "FEBRUARY 2026", "3 HOURS"):
        if required not in scheme_text:
            problems.append(f"scheme cover is missing: {required}")
    if paper.get("images", 0) < 1:
        problems.append("paper cover has no crest image")
    if scheme.get("images", 0) < 1:
        problems.append("scheme cover has no crest image")
    check = {
        "schema_version": 2,
        "subject": "CSC404",
        "checked_on": _today(),
        "paper": paper,
        "scheme": scheme,
        "format_profile": str(FORMAT),
        "notes": (
            "Paper cover is derived from UTM_STANDARD_COVERv2.docx with the "
            "CSC404 course, code, two-part instruction, 9 printed pages and "
            "3 HOURS. Scheme cover is derived from "
            "UTM_STANDARD_MARKING_SCHEME.docx with the CSC404 fields and "
            "notes."),
        "problems": problems,
    }
    CHECK.parent.mkdir(parents=True, exist_ok=True)
    CHECK.write_text(json.dumps(check, indent=2) + "\n", encoding="utf-8")
    return check


def update_subject() -> dict:
    path = config.PROJECT_ROOT / "subjects" / "CSC404" / "subject.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["template_path"] = "data/reference/CSC404/CSC404 TEMPLATE.docx"
    data["scheme_template_path"] = "data/reference/CSC404/CSC404 SCHEME.docx"
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return {"subject": str(path), "template_path": data["template_path"]}


def main() -> None:
    profile = format_profile()
    check = template_check()
    subject = update_subject()
    print(json.dumps({
        "format": str(FORMAT),
        "total_marks": profile["total_marks"],
        "sections": [section["key"] for section in profile["sections"]],
        "template_check": str(CHECK),
        "problems": check["problems"],
        "paper_cover": check["paper"]["cover_render"],
        "scheme_cover": check["scheme"]["cover_render"],
        "subject": subject,
    }, indent=2))
    if check["problems"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
