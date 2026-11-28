"""V3 format profile and template check for ICT502.

The current format is five questions, 20 marks each, 100 marks, 3 hours.
Every question has lettered parts and nested i/ii items.  The paper uses one
section (no Part A/B), matching all 11 approved papers.

Run:
    uv run python -m src.subjects.ict502.format_v3
"""
from __future__ import annotations

import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

import pymupdf

from src import config
from src.assemble.pdf_export import export_pdf

TRACKING = config.TRACKING_DIR / "ict502"
FORMAT = TRACKING / "format_profile.json"
CHECK = TRACKING / "template_check.json"
PREVIEW = TRACKING / "templates_preview"

PAPER_TEMPLATE = config.subject_reference_dir("ICT502") / "ICT502 TEMPLATE.docx"
SCHEME_TEMPLATE = config.subject_reference_dir("ICT502") / "ICT502 SCHEME.docx"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def format_profile() -> dict:
    profile = {
        "schema_version": 3,
        "playbook_version": "3.0",
        "subject": "ICT502",
        "era": "current",
        "source_papers": ["ICT502-2026-FEB", "ICT502-2025-JUL",
                          "ICT502-2025-FEB"],
        "sections": [{
            "key": "Q",
            "questions": 5,
            "marks_per_slot": [20, 20, 20, 20, 20],
            "numbering": "QUESTION 1..5; a), b), c), d); i), ii), iii)",
        }],
        "slot_roles": {
            "Q1": ["database_concepts", "data_warehouse", "file_system"],
            "Q2": ["relational_model", "erd", "sql"],
            "Q3": ["transaction", "recovery", "concurrency_control"],
            "Q4": ["query_processing", "distributed_db", "relational_model"],
            "Q5": ["database_development", "erd", "normalization",
                   "data_warehouse"],
        },
        "total_marks": 100,
        "duration": "3 HOURS",
        "numbering": {
            "question": "QUESTION n",
            "subparts": "a), b), c), d)",
            "nested": "i), ii), iii)",
        },
        "cover_template": "data/reference/ICT502/ICT502 TEMPLATE.docx",
        "scheme_template": "data/reference/ICT502/ICT502 SCHEME.docx",
        "marks_policy": {
            "selection": "fixed_five_questions",
            "slot_marks": "20 marks per question; total 100",
            "target_total_marks": 100,
            "basis": ("All 11 ICT502 papers use five questions and 100 marks. "
                      "Each question totals 20 marks, so marks do not constrain "
                      "selection."),
        },
        "slot_policy": {
            "question_reuse_within_paper": "never",
            "topic_policy": ("prefer broad topic coverage across Q1-Q5; "
                             "fixed role order is a preference, not a hard "
                             "constraint"),
            "source_paper_distinctness": "prefer five distinct papers",
            "reuse_cap": 4,
        },
        "checked_on": _today(),
    }
    FORMAT.parent.mkdir(parents=True, exist_ok=True)
    FORMAT.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    return profile


def _docx_check(path: Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml")
        ET.fromstring(xml)
        names = archive.namelist()
        text = " ".join("".join(re.findall(
            r"<w:t\b[^>]*>([^<]*)</w:t>",
            xml.decode("utf-8"))).split())
        headers = [name for name in names if name.startswith("word/header")]
        footers = [name for name in names if name.startswith("word/footer")]
        media = [name for name in names if name.startswith("word/media/")]
    return {
        "path": str(path),
        "xml_valid": True,
        "cover_nonempty": "UNIVERSITI TEKNOLOGI MARA" in text,
        "has_ict502": "ICT502" in text,
        "has_database_engineering": "DATABASE ENGINEERING" in text,
        "has_marking_scheme": "MARKING SCHEME" in text,
        "header_or_footer": bool(headers or footers),
        "header_parts": headers,
        "footer_parts": footers,
        "has_crest": any("image" in name for name in media),
        "media": media,
    }


def _render_cover(docx: Path, name: str) -> str:
    PREVIEW.mkdir(parents=True, exist_ok=True)
    pdf = PREVIEW / f"{name}.pdf"
    png = PREVIEW / f"{name}_page_1.png"
    export_pdf(docx, pdf)
    with pymupdf.open(str(pdf)) as document:
        page = document[0]
        page.get_pixmap(dpi=110).save(str(png))
    return str(png)


def template_check() -> dict:
    paper = _docx_check(PAPER_TEMPLATE)
    scheme = _docx_check(SCHEME_TEMPLATE)
    paper["cover_render"] = _render_cover(PAPER_TEMPLATE, "paper_template")
    scheme["cover_render"] = _render_cover(SCHEME_TEMPLATE, "scheme_template")
    problems = []
    for label, row in (("paper", paper), ("scheme", scheme)):
        if not row["xml_valid"]:
            problems.append(f"{label} template XML is invalid")
        if not row["cover_nonempty"]:
            problems.append(f"{label} cover is empty")
        if not row["header_or_footer"]:
            problems.append(f"{label} template has no header/footer")
    if not paper["has_ict502"]:
        problems.append("paper cover is missing ICT502")
    if not paper["has_database_engineering"]:
        problems.append("paper cover is missing DATABASE ENGINEERING")
    if not scheme["has_ict502"]:
        problems.append("scheme cover is missing ICT502")
    if not scheme["has_marking_scheme"]:
        problems.append("scheme cover is missing MARKING SCHEME")
    check = {
        "schema_version": 3,
        "subject": "ICT502",
        "checked_on": _today(),
        "paper": paper,
        "scheme": scheme,
        "format_profile": str(FORMAT),
        "notes": ("Paper cover is derived from UTM_STANDARD_COVERv2.docx with "
                  "the ICT502 course, code, five-question instruction and "
                  "3 HOURS. Scheme cover is derived from "
                  "UTM_STANDARD_MARKING_SCHEME.docx with the ICT502 fields; "
                  "all answers remain model_unofficial."),
        "problems": problems,
    }
    CHECK.parent.mkdir(parents=True, exist_ok=True)
    CHECK.write_text(json.dumps(check, indent=2) + "\n", encoding="utf-8")
    return check


def update_subject() -> dict:
    path = config.PROJECT_ROOT / "subjects" / "ICT502" / "subject.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["template_path"] = "data/reference/ICT502/ICT502 TEMPLATE.docx"
    data["scheme_template_path"] = "data/reference/ICT502/ICT502 SCHEME.docx"
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return {"subject": str(path), "template_path": data["template_path"],
            "scheme_template_path": data["scheme_template_path"]}


def main() -> None:
    profile = format_profile()
    check = template_check()
    subject = update_subject()
    print(json.dumps({
        "format": str(FORMAT),
        "total_marks": profile["total_marks"],
        "slots": profile["sections"][0]["marks_per_slot"],
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
