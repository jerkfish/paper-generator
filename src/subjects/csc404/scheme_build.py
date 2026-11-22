"""Build the CSC404 scheme template from the standard UTM scheme cover.

The source is the owner-supplied
``data/reference/standard/UTM_STANDARD_MARKING_SCHEME.docx``.  This module
patches the course fields and notes for CSC404 and leaves the cover layout
intact.  The source template is never modified.

Run:
    uv run python -m src.subjects.csc404.scheme_build --apply
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

import docx
import pymupdf

from src import config
from src.assemble.pdf_export import export_pdf
from src.subjects.templates import check_template

SOURCE = (config.subject_reference_dir("CSC404") /
          "scheme-coverpage-fix.docx")
TARGET = config.subject_reference_dir("CSC404") / "CSC404 SCHEME.docx"
TRACKING = config.TRACKING_DIR / "csc404"

TEXT_REPLACEMENTS = {
    "CS/MOCK": "CS/FEB",
    "OCTOBER 2026 (MOCK)": "FEBRUARY 2026",
    "OCT": "",
    "COMPUTER SECURITY": "PROGRAMMING II",
    "CSC662": "CSC404",
}

PARAGRAPH_REPLACEMENTS = {
    "This marking scheme accompanies": (
        "This marking scheme accompanies the CSC404 v2 recycled papers "
        "(current format, 2023-2026)."),
    "Computed answers show working": (
        "Answers are model_unofficial; no official CSC404 marking scheme "
        "was supplied."),
    "Supported theory marking points": (
        "Each answer is generated from the approved past-paper question and "
        "carries its source paper and page."),
    "Part A =": (
        "Part A = 4 questions; Part B = 2 questions; total = 100 marks."),
    "Computed:": (
        "Questions and answers are recycled study material, not marked by "
        "a lecturer."),
    "Near-copy rejection": (
        "Questions are recycled from the five current-format CSC404 papers."),
}
PAGE_COUNT_TEXT = "This marking scheme consists of 8 printed pages"


def _replace_text_nodes(xml: str) -> str:
    pattern = re.compile(r"(<w:t\b[^>]*>)(.*?)(</w:t>)", re.S)

    def replace(match: re.Match) -> str:
        text = match.group(2)
        for old, new in TEXT_REPLACEMENTS.items():
            text = text.replace(old, new)
        return match.group(1) + text + match.group(3)

    xml = pattern.sub(replace, xml)
    return xml.replace("CS/FEB  2026", "CS/FEB 2026")


def _rewrite_docx_xml(source: Path, target: Path) -> None:
    with zipfile.ZipFile(source) as zin, zipfile.ZipFile(
            target, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if (item.filename.startswith("word/")
                    and item.filename.endswith(".xml")):
                data = _replace_text_nodes(
                    data.decode("utf-8")).encode("utf-8")
            zout.writestr(item, data)


def _set_paragraph_text(paragraph, text: str) -> None:
    runs = paragraph.runs
    if runs:
        runs[0].text = text
        for run in runs[1:]:
            run.text = ""
    else:
        paragraph.add_run(text)


def build_candidate(source: Path = SOURCE, target: Path = TARGET,
                    apply: bool = False) -> dict:
    source = Path(source)
    target = Path(target)
    if not source.is_file():
        raise SystemExit(f"scheme source not found: {source}")
    result = {
        "source": str(source),
        "target": str(target),
        "applied": bool(apply),
        "replacements": TEXT_REPLACEMENTS,
    }
    if not apply:
        result["would_write"] = True
        return result

    target.parent.mkdir(parents=True, exist_ok=True)
    if source.name.endswith("fix.docx"):
        # Owner-supplied fixed cover: copy verbatim so the manual layout is
        # preserved; do not re-patch or re-typeset it.
        shutil.copy2(source, target)
    else:
        with tempfile.TemporaryDirectory() as tmp:
            rewritten = Path(tmp) / "rewritten.docx"
            _rewrite_docx_xml(source, rewritten)
            document = docx.Document(str(rewritten))
            for paragraph in list(document.paragraphs):
                text = paragraph.text.strip()
                for prefix, replacement in PARAGRAPH_REPLACEMENTS.items():
                    if text.startswith(prefix):
                        _set_paragraph_text(paragraph, replacement)
                        break
                if text.startswith("This marking scheme consists of"):
                    _set_paragraph_text(paragraph, PAGE_COUNT_TEXT)
            document.save(str(target))

    check = check_template(target)
    pdf_path = target.with_suffix(".pdf")
    pages = export_pdf(target, pdf_path)
    page1_text = ""
    with pymupdf.open(str(pdf_path)) as pdf:
        if len(pdf):
            page1_text = " ".join(pdf[0].get_text().split())[:900]
    cover_png = TRACKING / "scheme_cover.png"
    TRACKING.mkdir(parents=True, exist_ok=True)
    with pymupdf.open(str(pdf_path)) as pdf:
        if len(pdf):
            pdf[0].get_pixmap(dpi=110, alpha=False).save(str(cover_png))
    report = {
        **result,
        "check": check,
        "pdf": str(pdf_path),
        "pages": pages,
        "page1_text": page1_text,
        "cover_png": str(cover_png),
        "problems": check.get("problems", []),
    }
    (TRACKING / "scheme_check.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    result.update(report)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=str(SOURCE))
    parser.add_argument("--out", default=str(TARGET))
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    result = build_candidate(Path(args.source), Path(args.out),
                             apply=args.apply)
    print(json.dumps(result, indent=2))
    if not args.apply:
        print("dry run only; pass --apply to write the candidate template")
    elif result.get("problems"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
