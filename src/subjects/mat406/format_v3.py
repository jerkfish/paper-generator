"""V3 format profile and template check for MAT406.

The current format is the 2026 FEB / 2025 JUL shape: 3 hours, two parts of
four questions, 100 printed marks.  Individual slot marks vary across the two
papers, so the assembler will use the role order and carry each question's
printed marks; it targets 100 marks per seed.  The owner confirms this policy
at Gate B.

Run:
    uv run python -m src.subjects.mat406.format_v3
"""
from __future__ import annotations

import json
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pymupdf

from src import config
from src.assemble.build_docx_paper import export_pdf
from src.subjects.templates import check_template

TRACKING = config.TRACKING_DIR / "mat406" / "v2"
FORMAT = TRACKING / "format_profile.json"
CHECK = TRACKING / "template_check.json"
PREVIEW = TRACKING / "templates_preview"

SOURCE_TEMPLATE = (config.subject_reference_dir("MAT406") /
                   "MAT406 TEMPLATE-manualfix.docx")
PAPER_TEMPLATE = config.subject_reference_dir("MAT406") / "MAT406 TEMPLATE.docx"
SCHEME_TEMPLATE = (config.subject_reference_dir("MAT406") /
                   "scheme-template-fix.docx")

SLOT_ROLES = {
    "A1": {
        "role": "coordinate_geometry",
        "topics": ["coordinate_geometry"],
        "observed_marks": [11, 9],
        "source_examples": ["MAT406-2026-FEB-Q1", "MAT406-2025-JUL-Q1"],
    },
    "A2": {
        "role": "trigonometry",
        "topics": ["trigonometry"],
        "observed_marks": [10],
        "source_examples": ["MAT406-2026-FEB-Q2", "MAT406-2025-JUL-Q2"],
    },
    "A3": {
        "role": "vectors",
        "topics": ["vectors"],
        "observed_marks": [8],
        "source_examples": ["MAT406-2026-FEB-Q3", "MAT406-2025-JUL-Q3"],
    },
    "A4": {
        "role": "matrices",
        "topics": ["matrices"],
        "observed_marks": [13],
        "source_examples": ["MAT406-2026-FEB-Q4", "MAT406-2025-JUL-Q4"],
    },
    "B1": {
        "role": "coordinate_geometry_circles",
        "topics": ["coordinate_geometry", "circles"],
        "observed_marks": [16, 18],
        "source_examples": ["MAT406-2026-FEB-Q1-2",
                            "MAT406-2025-JUL-Q1-2"],
    },
    "B2": {
        "role": "trigonometry",
        "topics": ["trigonometry"],
        "observed_marks": [14],
        "source_examples": ["MAT406-2026-FEB-Q2-2",
                            "MAT406-2025-JUL-Q2-2"],
    },
    "B3": {
        "role": "vectors",
        "topics": ["vectors"],
        "observed_marks": [19],
        "source_examples": ["MAT406-2026-FEB-Q3-2",
                            "MAT406-2025-JUL-Q3-2"],
    },
    "B4": {
        "role": "matrices_systems",
        "topics": ["matrices", "systems_of_equations"],
        "observed_marks": [9],
        "source_examples": ["MAT406-2026-FEB-Q4-2",
                            "MAT406-2025-JUL-Q4-2"],
    },
}


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _patch_template() -> dict:
    """Use the owner's manually fixed MAT406 cover.

    The supplied MAT406 TEMPLATE-manualfix.docx already has the correct
    course, code, month, duration, crest, part instructions and Appendix
    alignment.  Copy it verbatim; do not re-patch or re-typeset it, so the
    owner's manual layout is preserved.
    """
    if not SOURCE_TEMPLATE.is_file():
        raise SystemExit(f"manual MAT406 template not found: {SOURCE_TEMPLATE}")
    PAPER_TEMPLATE.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_TEMPLATE, PAPER_TEMPLATE)
    with zipfile.ZipFile(PAPER_TEMPLATE) as source:
        xml = source.read("word/document.xml").decode("utf-8")
        media = [name for name in source.namelist()
                 if name.startswith("word/media/")]
    for required in ("FOUNDATION", "MATHEMATICS", "MAT406", "HOURS"):
        if required not in xml:
            raise SystemExit(
                f"manual template is missing required cover text: {required}")
    if not re.search(r"<w:t[^>]*>3</w:t>", xml):
        raise SystemExit("manual template is missing the TIME value 3")
    for forbidden in ("CSC662", "COMPUTER", "SECURITY"):
        if forbidden in xml:
            raise SystemExit(
                f"manual template still contains old course text: {forbidden}")
    if not media:
        raise SystemExit("manual template has no crest image")
    return {"source": str(SOURCE_TEMPLATE), "target": str(PAPER_TEMPLATE),
            "media": media}

def format_profile() -> dict:
    profile = {
        "schema_version": 2,
        "playbook_version": "2.0",
        "subject": "MAT406",
        "era": "current",
        "source_papers": ["MAT406-2026-FEB", "MAT406-2025-JUL"],
        "sections": [
            {
                "key": "A",
                "questions": 4,
                "numbering": "PART A; QUESTION 1..4; a), b), c); i), ii)",
                "slots": ["A1", "A2", "A3", "A4"],
            },
            {
                "key": "B",
                "questions": 4,
                "numbering": "PART B; QUESTION 1..4; a), b), c); i), ii)",
                "slots": ["B1", "B2", "B3", "B4"],
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
        "cover_template": "data/reference/MAT406/MAT406 TEMPLATE.docx",
        "scheme_template": ("data/reference/MAT406/"
                            "scheme-template-fix.docx"),
        "marks_policy": {
            "selection": "role_order",
            "slot_marks": "printed marks travel; not a fixed slot constraint",
            "target_total_marks": 100,
            "basis": (
                "Both current papers total 100 marks, but slot marks vary "
                "(A1 11/9; B1 16/18). Exact slot matching leaves only two "
                "questions per role and at most 8 seeds. The assembler will "
                "carry each question's printed marks and target 100 per seed. "
                "The owner confirms this policy at Gate B."),
            "owner_review": "Gate B",
        },
        "slot_policy": {
            "question_reuse_within_paper": "never",
            "topic_policy": "fixed A/B role order; marks carried from source",
            "source_paper_distinctness": "prefer distinct source papers",
        },
        "older_era": {
            "note": ("Six-question 100-mark papers (2022-2025 FEB) remain in "
                     "the bank for topic choice and provenance, but are not "
                     "the current format."),
            "examples": ["MAT406-2025-FEB", "MAT406-2024-JAN"],
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


def template_check() -> dict:
    paper = check_template(PAPER_TEMPLATE)
    scheme = check_template(SCHEME_TEMPLATE)
    paper["cover_render"] = _render_cover(PAPER_TEMPLATE, "paper_template")
    scheme["cover_render"] = _render_cover(SCHEME_TEMPLATE, "scheme_template")
    problems = list(paper.get("problems") or []) + list(
        scheme.get("problems") or [])
    check = {
        "schema_version": 2,
        "subject": "MAT406",
        "checked_on": _today(),
        "paper": paper,
        "scheme": scheme,
        "format_profile": str(FORMAT),
        "notes": (
            "Paper template is the owner-supplied "
            "MAT406 TEMPLATE-manualfix.docx, copied verbatim with the crest, "
            "course title, code, month, TIME 3 HOURS and Appendix alignment "
            "already fixed manually. The scheme template is the owner-supplied "
            "scheme-template-fix.docx, copied verbatim with its fixed crest, "
            "course fields and notes."),
        "problems": problems,
    }
    CHECK.parent.mkdir(parents=True, exist_ok=True)
    CHECK.write_text(json.dumps(check, indent=2) + "\n", encoding="utf-8")
    return check


def update_subject() -> dict:
    path = config.PROJECT_ROOT / "subjects" / "MAT406" / "subject.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["template_path"] = "data/reference/MAT406/MAT406 TEMPLATE.docx"
    data["scheme_template_path"] = (
        "data/reference/MAT406/scheme-template-fix.docx")
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return {"subject": str(path), "template_path": data["template_path"]}


def main() -> None:
    _patch_template()
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


if __name__ == "__main__":
    main()
