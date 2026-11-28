"""Build the ICT502 paper template from the standard UTM cover v2.

The source is ``UTM_STANDARD_COVERv2.docx``.  This module patches the course,
code, five-question instruction and page-count fields, then removes the sample
body so only the cover remains.  The source template is never modified.

Run:
    uv run python -m src.subjects.ict502.template_build --apply
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import tempfile
import zipfile
from pathlib import Path

import docx
import pymupdf
from docx.oxml.ns import qn

from src import config
from src.assemble.pdf_export import export_pdf
from src.subjects.templates import check_template

SOURCE = config.REFERENCE_DIR / "standard" / "UTM_STANDARD_COVERv2.docx"
TARGET = config.subject_reference_dir("ICT502") / "ICT502 TEMPLATE.docx"
TRACKING = config.TRACKING_DIR / "ict502"

TEXT_REPLACEMENTS = {
    "COMPUTER ": "DATABASE ",
    "SECURITY": "ENGINEERING",
    "CSC662": "ICT502",
}
COVER_MARKER = "DO NOT TURN THIS PAGE UNTIL YOU ARE TOLD TO DO SO"
SOURCE_PAGE_COUNT = "6"
PAGE_COUNT = "8"


def _replace_text_nodes(xml: str) -> str:
    pattern = re.compile(r"(<w:t\b[^>]*>)(.*?)(</w:t>)", re.S)

    def replace(match: re.Match) -> str:
        text = match.group(2)
        for old, new in TEXT_REPLACEMENTS.items():
            text = text.replace(old, new)
        text = text.replace("-provided", "- provided")
        return match.group(1) + text + match.group(3)

    xml = pattern.sub(replace, xml)
    xml = re.sub(
        r"(<w:t\b[^>]*>)" + SOURCE_PAGE_COUNT
        + r"(</w:t>)(?=(?:(?!</w:p>).)*?"
        r"<w:t\b[^>]*>printed</w:t>)",
        r"\g<1>" + PAGE_COUNT + r"\g<2>", xml, count=1)
    return xml


def _rewrite_docx_xml(source: Path, target: Path) -> None:
    with zipfile.ZipFile(source) as zin, zipfile.ZipFile(
            target, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
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


def _truncate_after_cover(document, marker: str) -> None:
    body = document.element.body
    children = list(body.iterchildren())
    keep_until = None
    seen = False
    for index, child in enumerate(children):
        if child.tag == qn("w:p"):
            text = "".join(node.text or "" for node in child.iter(qn("w:t")))
            if marker in text:
                seen = True
            if seen:
                ppr = child.find(qn("w:pPr"))
                if ppr is not None and ppr.find(qn("w:sectPr")) is not None:
                    keep_until = index
                    break
    if keep_until is None:
        raise RuntimeError(f"cover section break not found after {marker!r}")
    cover_sect = children[keep_until].find(qn("w:pPr")).find(qn("w:sectPr"))
    final_sect = body.find(qn("w:sectPr"))
    if final_sect is None:
        raise RuntimeError("final section properties are missing")
    replacement = copy.deepcopy(cover_sect)
    break_type = replacement.find(qn("w:type"))
    if break_type is not None:
        replacement.remove(break_type)
    body.replace(final_sect, replacement)
    for child in children[keep_until + 1:]:
        if child.tag == qn("w:sectPr"):
            continue
        body.remove(child)
    body.remove(children[keep_until])


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
        "replacements": TEXT_REPLACEMENTS,
        "page_count": PAGE_COUNT,
    }
    if not apply:
        result["would_write"] = True
        return result

    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        rewritten = Path(tmp) / "rewritten.docx"
        _rewrite_docx_xml(source, rewritten)
        document = docx.Document(str(rewritten))
        _truncate_after_cover(document, COVER_MARKER)
        for paragraph in list(document.paragraphs):
            text = paragraph.text.strip()
            if text.startswith("This question paper consists"):
                _set_paragraph_text(
                    paragraph,
                    "This question paper consists of five (5) questions.")
            elif text.upper().startswith("PART B"):
                _set_paragraph_text(paragraph, "")
            elif text.startswith("Answer") and "English" in text:
                _set_paragraph_text(
                    paragraph, "Answer ALL questions in English.")
        document.save(str(target))

    check = check_template(target)
    pdf_path = target.with_suffix(".pdf")
    pages = export_pdf(target, pdf_path)
    page1_text = ""
    with pymupdf.open(str(pdf_path)) as pdf:
        if len(pdf):
            page1_text = " ".join(pdf[0].get_text().split())[:900]
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
