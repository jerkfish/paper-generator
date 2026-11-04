"""Build a CSC402 template candidate from the standard-cover-derived DOCX.

This is subject-specific stage-3 code.  It copies the clean MAT133 template
(which is itself derived from ``data/reference/standard/UTM_STANDARD_COVER.docx``),
replaces the subject/title/month text, removes MAT133-only pack items and adds
a CSC402 footer.  The source template is never modified.

The result is a *candidate*: stage 3 remains [HUMAN] until the cover and
page-2 transition are approved.

    uv run python -m src.subjects.csc402.template_build --apply
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
from docx.enum.text import WD_ALIGN_PARAGRAPH

from src import config
from src.assemble.pdf_export import export_pdf
from src.subjects.templates import check_template

SOURCE = (config.subject_reference_dir("MAT133") / "MAT133 TEMPLATE.docx")
TARGET = (config.subject_reference_dir("CSC402") / "CSC402 TEMPLATE.docx")
TRACKING = config.TRACKING_DIR / "csc402"

# Exact text-node values in the MAT133 cover.
EXACT_REPLACEMENTS = {
    "PRE": "PROGRAMMING",
    "CALCULUS": "I",
    "FEB": "NOV",
}
SUBSTRING_REPLACEMENTS = (
    ("MAT133", "CSC402"),
    ("CS/FEB", "CS/NOV"),
    ("FEBRUARI", "NOVEMBER"),
)
QUESTION_INSTRUCTION = (
    "This question paper consists of the questions printed in this booklet.")


def _replace_text_nodes(xml: str) -> str:
    pattern = re.compile(r"(<w:t\b[^>]*>)(.*?)(</w:t>)", re.S)

    def replace(match: re.Match) -> str:
        text = match.group(2)
        stripped = text.strip()
        if stripped in EXACT_REPLACEMENTS:
            text = text.replace(stripped, EXACT_REPLACEMENTS[stripped])
        for old, new in SUBSTRING_REPLACEMENTS:
            text = text.replace(old, new)
        return match.group(1) + text + match.group(3)

    return pattern.sub(replace, xml)


def _widen_title_box(xml: str) -> str:
    # The MAT133 box only fits "PRE CALCULUS".  Widen it slightly so
    # "PROGRAMMING I" does not wrap inside the word.
    return xml.replace(
        'left:3275;top:524;width:1873;height:1549',
        'left:3275;top:524;width:2250;height:1549')


def _set_duration_hours(xml: str, hours: str = "3") -> str:
    # Only the text node immediately before HOURS in the cover text box.
    pattern = re.compile(
        r"(<w:t[^>]*>)2(</w:t>)(?=(?:(?!</w:p>).)*?<w:t[^>]*>HOURS</w:t>)",
        re.S)
    return pattern.sub(lambda m: m.group(1) + hours + m.group(2), xml)


def _rewrite_docx_xml(source: Path, target: Path) -> None:
    with zipfile.ZipFile(source) as zin, zipfile.ZipFile(
            target, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                xml = _replace_text_nodes(data.decode("utf-8"))
                xml = _widen_title_box(xml)
                xml = _set_duration_hours(xml)
                data = xml.encode("utf-8")
            elif item.filename.startswith("word/footer") and item.filename.endswith(".xml"):
                # The source footer says "Opta"; the intended word is "Cipta".
                data = data.replace(b"Opta", b"Cipta")
            zout.writestr(item, data)


def _delete_paragraph(paragraph) -> None:
    element = paragraph._element
    element.getparent().remove(element)


def _delete_run(run) -> None:
    element = run._r
    element.getparent().remove(element)


def _set_paragraph_text(paragraph, text: str) -> None:
    """Replace a paragraph's text while keeping the first run's formatting."""
    runs = paragraph.runs
    if runs:
        runs[0].text = text
        for run in runs[1:]:
            run.text = ""
    else:
        paragraph.add_run(text)


def _add_footer(document) -> None:
    for section in document.sections:
        footer = section.footer
        paragraph = footer.add_paragraph("CSC402 PROGRAMMING I")
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER


def build_candidate(source: Path = SOURCE, target: Path = TARGET,
                    apply: bool = False) -> dict:
    source = Path(source)
    target = Path(target)
    if not source.is_file():
        raise SystemExit(f"template source not found: {source}")
    result = {
        "source": str(source),
        "target": str(target),
        "applied": bool(apply),
        "replacements": {
            "exact": EXACT_REPLACEMENTS,
            "substring": dict(SUBSTRING_REPLACEMENTS),
        },
    }
    if not apply:
        result["would_write"] = True
        return result

    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        rewritten = Path(tmp) / "rewritten.docx"
        _rewrite_docx_xml(source, rewritten)
        document = docx.Document(str(rewritten))

        # Remove MAT133-only pack items and generalise the question count.
        for paragraph in list(document.paragraphs):
            text = paragraph.text.strip()
            if (text.startswith("a one - page Append") or
                    text.startswith("a graph paper") or text == "/"):
                _delete_paragraph(paragraph)
            elif text.startswith("INSTRUCTIONS TO CANDIDATES"):
                # The source splits the first "I" into a tightly-spaced run
                # that is clipped on the rendered cover.  Move it into the
                # normal heading run.
                runs = paragraph.runs
                if runs and runs[0].text.strip() == "I" and len(runs) > 1:
                    runs[1].text = "I" + runs[1].text
                    _delete_run(runs[0])
                # Nudge the heading off the left clip edge.
                if paragraph.runs:
                    paragraph.runs[0].text = "   " + paragraph.runs[0].text
            elif text.startswith("This question paper consists of"):
                _set_paragraph_text(paragraph, QUESTION_INSTRUCTION)
            elif text.startswith("This examination paper consists of"):
                _set_paragraph_text(
                    paragraph,
                    "This examination paper consists of the printed pages "
                    "shown in the generated paper.")

        _add_footer(document)
        document.save(str(target))

    check = check_template(target)
    pdf_path = target.with_suffix(".pdf")
    pages = export_pdf(target, pdf_path)
    page1_text = ""
    with pymupdf.open(str(pdf_path)) as pdf:
        if len(pdf):
            page1_text = " ".join(pdf[0].get_text().split())[:800]
    cover_png = TRACKING / "template_cover.png"
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
    (TRACKING / "template_check.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    result.update(report)
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=str(SOURCE))
    ap.add_argument("--out", default=str(TARGET))
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    result = build_candidate(Path(args.source), Path(args.out),
                             apply=args.apply)
    print(json.dumps(result, indent=2))
    if not args.apply:
        print("dry run only; pass --apply to write the candidate template")
    elif result.get("problems"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
