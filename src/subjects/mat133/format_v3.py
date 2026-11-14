"""V3 format profile and template check for MAT133.

The current format comes from the two newest papers: four questions,
10 + 10 + 10 + 25 marks, 2 hours.  The Jul 2025 paper has the same four-question
shape with a 5-mark Q3 variant (total 50); the Feb 2026 paper is the full
55-mark shape used here.

Run:
    uv run python -m src.subjects.mat133.format_v3
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
from src.assemble.build_docx_paper import export_pdf

TRACKING = config.TRACKING_DIR / "mat133" / "v2"
FORMAT = TRACKING / "format_profile.json"
CHECK = TRACKING / "template_check.json"
PREVIEW = TRACKING / "templates_preview"

PAPER_TEMPLATE = config.subject_reference_dir("MAT133") / "MAT133 TEMPLATE.docx"
SCHEME_TEMPLATE = (config.REFERENCE_DIR / "standard" /
                   "UTM_STANDARD_MARKING_SCHEME.docx")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def format_profile() -> dict:
    profile = {
        "schema_version": 2,
        "playbook_version": "2.0",
        "subject": "MAT133",
        "era": "current",
        "source_papers": ["MAT133-2026-FEB", "MAT133-2025-JUL"],
        "sections": [{
            "key": "Q",
            "questions": 4,
            "marks_per_slot": [10, 10, 10, 25],
            "numbering": "QUESTION 1..4; a), b), c), d); i., ii.",
        }],
        "total_marks": 55,
        "duration": "2 HOURS",
        "numbering": {
            "question": "QUESTION n",
            "subparts": "a), b), c), d)",
            "nested": "i., ii., iii.",
        },
        "cover_template": "data/reference/MAT133/MAT133 TEMPLATE.docx",
        "scheme_template": ("data/reference/standard/"
                            "UTM_STANDARD_MARKING_SCHEME.docx"),
        "slot_policy": {
            "marks_tolerance": 0,
            "question_reuse_within_paper": "never",
            "topic_policy": ("no fixed quota; prefer distinct topics across "
                             "the four selected questions"),
        },
        "marks_basis": (
            "The two newest papers define the current format. Both have four "
            "questions and a 2-hour duration. Feb 2026 is 10+10+10+25 = 55; "
            "Jul 2025 is 50 because its Q3 is a 5-mark variant. V3 uses the "
            "full 55-mark shape with exact slot marks and no tolerance."),
        "older_era": {
            "note": ("Five-question, 3-hour papers remain in the bank for "
                     "topic choice and provenance, but are not the current "
                     "format."),
            "examples": ["MAT133-2024-JUL", "MAT133-2025-FEB"],
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
        text = "".join(re.findall(
            r"<w:t\b[^>]*>([^<]*)</w:t>", xml.decode("utf-8")))
        headers = [name for name in names
                   if name.startswith("word/header")]
        footers = [name for name in names
                   if name.startswith("word/footer")]
        media = [name for name in names if name.startswith("word/media/")]
    return {
        "path": str(path),
        "xml_valid": True,
        "cover_nonempty": "UNIVERSITI TEKNOLOGI MARA" in text,
        "has_mat133": "MAT133" in text,
        "has_marking_scheme": "MARKING SCHEME" in text,
        "header_or_footer": bool(headers or footers),
        "header_parts": headers,
        "footer_parts": footers,
        "has_crest": any("image1" in name for name in media),
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
    check = {
        "schema_version": 2,
        "subject": "MAT133",
        "checked_on": _today(),
        "paper": paper,
        "scheme": scheme,
        "format_profile": str(FORMAT),
        "notes": (
            "The paper uses the approved MAT133 template. The scheme uses the "
            "standard UTM marking-scheme cover required by AGENTS.md; its "
            "fields are patched during assembly, not replaced with a bespoke "
            "cover."),
        "problems": [],
    }
    if not paper["xml_valid"] or not paper["cover_nonempty"]:
        check["problems"].append("paper template cover/XML check failed")
    if not paper["header_or_footer"]:
        check["problems"].append("paper template has no header/footer")
    if not scheme["xml_valid"] or not scheme["cover_nonempty"]:
        check["problems"].append("scheme template cover/XML check failed")
    if not scheme["header_or_footer"]:
        check["problems"].append("scheme template has no header/footer")
    CHECK.parent.mkdir(parents=True, exist_ok=True)
    CHECK.write_text(json.dumps(check, indent=2) + "\n", encoding="utf-8")
    return check


def main() -> None:
    profile = format_profile()
    check = template_check()
    print(json.dumps({
        "format": str(FORMAT),
        "total_marks": profile["total_marks"],
        "slots": profile["sections"][0]["marks_per_slot"],
        "template_check": str(CHECK),
        "problems": check["problems"],
        "paper_cover": check["paper"]["cover_render"],
        "scheme_cover": check["scheme"]["cover_render"],
    }, indent=2))


if __name__ == "__main__":
    main()
