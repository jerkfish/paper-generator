"""Build the ICT502 scheme template from the standard UTM scheme cover.

The source is ``UTM_STANDARD_MARKING_SCHEME.docx`` required by AGENTS.md.
This module patches the course/code/session fields and notes, and leaves the
cover layout intact.  The source template is never modified.

Run:
    uv run python -m src.subjects.ict502.scheme_build --apply
"""
from __future__ import annotations

import argparse
import json
import re
import tempfile
import zipfile
from pathlib import Path

import docx
import pymupdf

from src import config
from src.assemble.pdf_export import export_pdf
from src.subjects.templates import check_template

SOURCE = (config.REFERENCE_DIR / "standard" /
          "UTM_STANDARD_MARKING_SCHEME.docx")
TARGET = config.subject_reference_dir("ICT502") / "ICT502 SCHEME.docx"
TRACKING = config.TRACKING_DIR / "ict502"

TEXT_REPLACEMENTS = {
    "OCTOBER 2026 (MOCK)": "FEBRUARY 2026",
    "CS/MOCK": "CS/FEB",
    "OCT": "",
    "COMPUTER SECURITY": "DATABASE ENGINEERING",
    "CSC662": "ICT502",
}

PARAGRAPH_REPLACEMENTS = {
    "This marking scheme accompanies": (
        "This marking scheme accompanies the ICT502 recycled mock papers "
        "(five questions, 20 marks each)."),
    "Computed answers show working": (
        "Answers are model_unofficial; no official ICT502 marking scheme "
        "was supplied."),
    "Supported theory marking points": (
        "Each answer is generated from the approved past-paper question and "
        "carries its source paper and page."),
    "Part A =": (
        "Five questions x 20 marks; total = 100 marks."),
    "Computed:": (
        "All 55 approved bank questions have model_unofficial answers."),
    "Near-copy rejection": (
        "Questions are recycled from the 11 approved ICT502 past papers."),
}
PAGE_COUNT_TEXT = "This marking scheme consists of 10 printed pages"


def _replace_text_nodes(xml: str) -> str:
    pattern = re.compile(r"(<w:t\b[^>]*>)(.*?)(</w:t>)", re.S)

    def replace(match: re.Match) -> str:
        text = match.group(2)
        for old, new in TEXT_REPLACEMENTS.items():
            text = text.replace(old, new)
        text = re.sub(r"[ \xa0]{2,}", " ", text)
        return match.group(1) + text + match.group(3)

    return pattern.sub(replace, xml)


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
            if text.startswith("Answers are model_unofficial"):
                paragraph.alignment = None
                paragraph.paragraph_format.left_indent = 0
                paragraph.paragraph_format.right_indent = 0
                paragraph.paragraph_format.first_line_indent = 0
        # The standard cover box was sized for "COMPUTER SECURITY".  The
        # longer ICT502 title needs a slightly smaller run so it stays on one
        # line and does not push "3 HOURS" out of the box.
        from docx.oxml.ns import qn
        for node in document.element.body.iter(qn("w:t")):
            text = str(node.text or "").strip()
            if text == "DATABASE ENGINEERING":
                run = node.getparent()
                rpr = run.find(qn("w:rPr")) if run is not None else None
                if rpr is None:
                    continue
                for tag in ("w:sz", "w:szCs"):
                    size = rpr.find(qn(tag))
                    if size is not None:
                        size.set(qn("w:val"), "18")
            if text.startswith("Answers are model_unofficial"):
                paragraph = node.getparent().getparent()
                ppr = paragraph.find(qn("w:pPr"))
                ind = ppr.find(qn("w:ind")) if ppr is not None else None
                if ind is not None:
                    ind.set(qn("w:left"), "775")
                    for attr in ("w:leftChars", "w:hanging",
                                 "w:hangingChars"):
                        if ind.get(qn(attr)) is not None:
                            ind.set(qn(attr), "0")
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
