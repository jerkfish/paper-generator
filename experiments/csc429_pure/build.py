"""CSC429 pure-extraction experiment.

This is deliberately outside the production pipeline.  It reads the supplied
papers/templates, crops the original figures, recreates tables/formulas as
native Word content, and builds one test seed paper + scheme.

    uv run python experiments/csc429_pure/build.py --stage all
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import docx
import pymupdf
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from PIL import Image, ImageDraw

from src import config
from src.assemble.pdf_export import export_pdf
from src.ingest.ocr import win_ocr

EXP = ROOT / "outputs" / "experiments" / "csc429_pure_20261106"
INPUTS = EXP / "inputs"
PAGES = EXP / "pages"
ASSETS = EXP / "assets"
SEED = EXP / "seed_01"
QUESTIONS = Path(__file__).with_name("questions.json")
ANSWERS = EXP / "answers.json"

PAPER_TEMPLATE = Path(
    r"C:\Users\Ahmad\AppData\Roaming\CherryStudio\Data\Files"
    r"\01a1afd0-ae6e-776b-9875-4e14b0258644.docx")
SCHEME_TEMPLATE = Path(
    r"C:\Users\Ahmad\AppData\Roaming\CherryStudio\Data\Files"
    r"\01a1afd0-ae72-762c-b8a0-edefe981eb9b.docx")
PDF_FILES = {
    "CSC429 (12).PDF": Path(r"C:\Users\Ahmad\AppData\Roaming\CherryStudio\Data\Files\01a1afd0-ae72-762c-b8a0-f05e1e77f575.pdf"),
    "CSC429 (22).pdf": Path(r"C:\Users\Ahmad\AppData\Roaming\CherryStudio\Data\Files\01a1afd0-ae72-762c-b8a0-f4fb3dcefee7.pdf"),
    "CSC429 (19).pdf": Path(r"C:\Users\Ahmad\AppData\Roaming\CherryStudio\Data\Files\01a1afd0-ae73-71d8-a73f-3d3f10bed1f3.pdf"),
    "CSC429 (17).pdf": Path(r"C:\Users\Ahmad\AppData\Roaming\CherryStudio\Data\Files\01a1afd0-ae73-71d8-a73f-452dc9e65f59.pdf"),
    "CSC429 (15).pdf": Path(r"C:\Users\Ahmad\AppData\Roaming\CherryStudio\Data\Files\01a1afd0-ae73-71d8-a73f-4dcabd240ca9.pdf"),
    "CSC429 (14).pdf": Path(r"C:\Users\Ahmad\AppData\Roaming\CherryStudio\Data\Files\01a1afd0-ae73-71d8-a73f-53b6b8047d35.pdf"),
    "CSC429 (13).PDF": Path(r"C:\Users\Ahmad\AppData\Roaming\CherryStudio\Data\Files\01a1afd0-ae73-71d8-a73f-54a27df9b4f6.pdf"),
}


def load_questions() -> dict:
    data = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    manifest_path = EXP / "asset_manifest.json"
    if manifest_path.exists():
        rows = json.loads(manifest_path.read_text(
            encoding="utf-8")).get("assets", [])
        index = {(row["slot"], row["label"]): row for row in rows}
        for question in data.get("questions", []):
            for asset in question.get("assets") or []:
                row = index.get((question["slot"], asset["label"]))
                if row:
                    asset["path"] = row["path"]
                    asset["ocr_text"] = row.get("ocr_text", "")
                    asset["sha256"] = row.get("sha256", "")
    return data


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_inputs() -> None:
    INPUTS.mkdir(parents=True, exist_ok=True)
    for name, source in PDF_FILES.items():
        target = INPUTS / name
        if source.is_file() and not target.is_file():
            shutil.copy2(source, target)
    for source, target_name in (
            (PAPER_TEMPLATE, "paper_template.docx"),
            (SCHEME_TEMPLATE, "scheme_template.docx")):
        target = INPUTS / target_name
        if source.is_file() and not target.is_file():
            shutil.copy2(source, target)


def _page_image(paper: str, page_no: int) -> Path:
    stem = Path(paper).stem
    return PAGES / stem / f"page_{page_no:03d}.png"


def render_pages() -> None:
    PAGES.mkdir(parents=True, exist_ok=True)
    questions = load_questions()["questions"]
    needed: dict[str, set[int]] = {}
    for question in questions:
        needed.setdefault(question["paper"], set()).add(int(question["page"]))
        for asset in question.get("assets") or []:
            needed.setdefault(question["paper"], set()).add(int(asset["page"]))
    for paper, pages in needed.items():
        source = INPUTS / paper
        document = pymupdf.open(str(source))
        try:
            for page_no in sorted(pages):
                target = _page_image(paper, page_no)
                if target.is_file():
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                page = document[page_no - 1]
                pix = page.get_pixmap(
                    dpi=300, colorspace=pymupdf.csRGB, alpha=False)
                target.write_bytes(pix.tobytes("png"))
        finally:
            document.close()


def crop_assets() -> dict:
    ASSETS.mkdir(parents=True, exist_ok=True)
    questions = load_questions()["questions"]
    rows = []
    for question in questions:
        for asset in question.get("assets") or []:
            paper = question["paper"]
            page_no = int(asset["page"])
            page_path = _page_image(paper, page_no)
            document = pymupdf.open(str(INPUTS / paper))
            try:
                page = document[page_no - 1]
                page_points = (page.rect.width, page.rect.height)
            finally:
                document.close()
            with Image.open(page_path) as source:
                image = source.convert("RGB")
                sx = image.width / page_points[0]
                sy = image.height / page_points[1]
                box = [float(v) for v in asset["bbox"]]
                crop = image.crop((
                    max(0, int(box[0] * sx)),
                    max(0, int(box[1] * sy)),
                    min(image.width, int(box[2] * sx)),
                    min(image.height, int(box[3] * sy)),
                ))
            target = ASSETS / f"{question['slot']}_{asset['label'].replace(' ', '_')}.png"
            crop.save(target, "PNG", dpi=(300, 300))
            ocr = ""
            try:
                ocr = win_ocr(target)
            except Exception:
                pass
            rows.append({
                "slot": question["slot"],
                "paper": paper,
                "paper_label": question["paper_label"],
                "page": page_no,
                "kind": asset["kind"],
                "label": asset["label"],
                "bbox_pdf": box,
                "caption": asset.get("caption", ""),
                "path": _rel(target),
                "sha256": _sha(target),
                "width_px": crop.width,
                "height_px": crop.height,
                "ocr_text": ocr,
            })
    manifest = {
        "subject": "CSC429",
        "experiment": "pure_extraction_v1",
        "assets": rows,
        "counts": {
            "assets": len(rows),
            "pictures": sum(1 for r in rows if r["kind"] == "picture"),
            "diagrams": sum(1 for r in rows if r["kind"] == "diagram"),
            "formulas": sum(1 for r in rows if r["kind"] == "formula"),
        },
    }
    (EXP / "asset_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    return manifest


# ---------------------------------------------------------------------------
# Word helpers
# ---------------------------------------------------------------------------


def _clear_body(document: docx.Document) -> None:
    body = document.element.body
    children = list(body)
    cut = None
    for index, child in enumerate(children):
        if child.tag != qn("w:p"):
            continue
        ppr = child.find(qn("w:pPr"))
        if ppr is not None and ppr.find(qn("w:sectPr")) is not None:
            cut = index
            break
    if cut is None:
        raise RuntimeError("template has no section break")
    for child in children[cut + 1:]:
        if child.tag == qn("w:sectPr"):
            continue
        body.remove(child)


def _para(document, text: str = "", *, bold: bool = False,
          italic: bool = False, size: float = 11, align=None,
          before: float = 0, after: float = 4,
          indent: float = 0, hanging: float = 0,
          spacing: float = 1.5, keep_with_next: bool = False):
    paragraph = document.add_paragraph()
    if align is not None:
        paragraph.alignment = align
    paragraph.paragraph_format.line_spacing = spacing
    paragraph.paragraph_format.space_before = Pt(before)
    paragraph.paragraph_format.space_after = Pt(after)
    if indent:
        paragraph.paragraph_format.left_indent = Cm(indent)
    if hanging:
        paragraph.paragraph_format.first_line_indent = Cm(-hanging)
    if keep_with_next:
        paragraph.paragraph_format.keep_with_next = True
    run = paragraph.add_run(text)
    run.font.name = "Arial"
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    return paragraph


def _question_heading(document, slot: str, marks: int) -> None:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.line_spacing = 1.5
    paragraph.paragraph_format.space_before = Pt(12)
    paragraph.paragraph_format.space_after = Pt(4)
    paragraph.paragraph_format.keep_with_next = True
    section = document.sections[-1]
    text_width = (section.page_width - section.left_margin
                  - section.right_margin)
    paragraph.paragraph_format.tab_stops.add_tab_stop(
        text_width, WD_TAB_ALIGNMENT.RIGHT)
    run = paragraph.add_run(f"QUESTION {slot}")
    run.bold = True
    run.font.name = "Arial"
    run.font.size = Pt(11)
    tab = paragraph.add_run("\t")
    tab.font.name = "Arial"
    tab.font.size = Pt(11)
    mark = paragraph.add_run(f"({marks} marks)")
    mark.font.name = "Arial"
    mark.font.size = Pt(11)


def _picture(document, path: Path, max_width_cm: float = 16.2,
             max_height_cm: float = 18.0) -> None:
    with Image.open(path) as image:
        width_px, height_px = image.width, image.height
    width_cm = max_width_cm
    if width_px and height_px:
        if width_cm * height_px / width_px > max_height_cm:
            width_cm = max_height_cm * width_px / height_px
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(4)
    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.paragraph_format.keep_with_next = True
    paragraph.add_run().add_picture(str(path), width=Cm(width_cm))


def _caption(document, text: str) -> None:
    _para(document, text, italic=True, size=9,
          align=WD_ALIGN_PARAGRAPH.CENTER, after=6, spacing=1.0,
          keep_with_next=True)


def _cell_text(cell, text: str, *, bold: bool = False) -> None:
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.line_spacing = 1.0
    paragraph.paragraph_format.space_before = Pt(1)
    paragraph.paragraph_format.space_after = Pt(1)
    run = paragraph.add_run(text)
    run.font.name = "Arial"
    run.font.size = Pt(9.5)
    run.bold = bold



def _table_borders(table) -> None:
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "6")
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), "000000")
        borders.append(element)
    tbl_pr.append(borders)


def _table(document, table_spec: dict) -> None:
    if table_spec.get("caption"):
        _caption(document, table_spec["caption"])
    columns = table_spec["columns"]
    rows = table_spec["rows"]
    table = document.add_table(rows=1 + len(rows), cols=len(columns))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    _table_borders(table)
    for index, header in enumerate(columns):
        _cell_text(table.rows[0].cells[index], header, bold=True)
    for r_index, row in enumerate(rows, start=1):
        for c_index, value in enumerate(row):
            _cell_text(table.rows[r_index].cells[c_index], value)
    _para(document, "", after=4)


def _add_asset(document, asset: dict) -> None:
    path = ROOT / asset["path"]
    _picture(document, path, max_width_cm=float(asset.get("max_width_cm", 16.2)))
    if asset.get("caption"):
        _caption(document, asset["caption"])


def _add_subpart(document, subpart: dict) -> None:
    _para(
        document,
        f"{subpart['label']})\t{subpart['text']}",
        size=11, after=3, indent=1.0, hanging=0.55,
    )


def build_paper() -> Path:
    SEED.mkdir(parents=True, exist_ok=True)
    target = SEED / "paper.docx"
    shutil.copy2(INPUTS / "paper_template.docx", target)
    document = docx.Document(str(target))
    document.styles["Normal"].font.name = "Arial"
    document.styles["Normal"].font.size = Pt(11)
    _clear_body(document)
    _para(document, "PART A (80 MARKS)", bold=True, size=11, after=4)
    _para(document, "Answer ALL questions in this part.", size=11, after=8)
    questions = load_questions()["questions"]
    for question in questions:
        if question["slot"].startswith("B"):
            continue
        if question.get("page_break_before"):
            document.add_page_break()
        _question_heading(document, question["slot"], question["marks"])
        if question.get("text"):
            _para(document, question["text"], size=11, after=4,
                  keep_with_next=bool(question.get("assets")
                                      or question.get("figure_text")
                                      or question.get("tables")))
        for asset in question.get("assets") or []:
            _add_asset(document, asset)
        if question.get("figure_text"):
            paragraph = document.add_paragraph()
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.line_spacing = 1.0
            paragraph.paragraph_format.space_before = Pt(4)
            paragraph.paragraph_format.space_after = Pt(2)
            paragraph.paragraph_format.keep_with_next = True
            run = paragraph.add_run(question["figure_text"])
            run.font.name = "Courier New"
            run.font.size = Pt(9.5)
            _caption(document, question.get("figure_label", "Figure 1"))
        for subpart in question.get("subparts") or []:
            _add_subpart(document, subpart)
        for table_spec in question.get("tables") or []:
            _table(document, table_spec)
    document.add_page_break()
    _para(document, "PART B (20 MARKS)", bold=True, size=11, after=4)
    _para(document, "Answer the question in this part.", size=11, after=8)
    for question in questions:
        if not question["slot"].startswith("B"):
            continue
        _question_heading(document, question["slot"], question["marks"])
        if question.get("text"):
            _para(document, question["text"], size=11, after=4,
                  keep_with_next=bool(question.get("assets")
                                      or question.get("figure_text")
                                      or question.get("tables")))
        for asset in question.get("assets") or []:
            _add_asset(document, asset)
        for table_spec in question.get("tables") or []:
            _table(document, table_spec)
        for subpart in question.get("subparts") or []:
            _add_subpart(document, subpart)
    document.save(str(target))
    return target


def _patch_scheme_notes(document: docx.Document) -> None:
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text.startswith("This marking scheme accompanies"):
            paragraph.text = (
                "This marking scheme accompanies the CSC429 pure-extraction "
                "test paper (November 2026).")
        elif text.startswith("Generated answers show working"):
            paragraph.text = (
                "Answers are reference answers for the extraction test. They "
                "are not official UTM marking schemes.")
        elif text.startswith("Generated marking points state"):
            paragraph.text = (
                "Marking points are reference guidance; check the answer "
                "against the source paper and the original figure.")
        elif text.startswith("Generated slots:"):
            paragraph.text = (
                "Extraction test: 11 real questions; 7 asset-bearing "
                "questions; 0 placeholders.")
        elif text.startswith("Structure derived from"):
            paragraph.text = (
                "Questions are reproduced from the supplied CSC429 papers; "
                "figures are cropped from the source page and captions are "
                "native text.")
        elif text.startswith("This marking scheme consists of"):
            paragraph.text = "This marking scheme consists of 1 printed page"


def _scheme_question_text(question: dict) -> str:
    lines = []
    if question.get("text"):
        lines.append(question["text"])
    if question.get("figure_text"):
        lines.append(question["figure_text"])
        lines.append(question.get("figure_label", "Figure 1"))
    for subpart in question.get("subparts") or []:
        lines.append(f"{subpart['label']}) {subpart['text']}")
    return "\n".join(lines)


def build_scheme() -> Path:
    SEED.mkdir(parents=True, exist_ok=True)
    target = SEED / "scheme.docx"
    shutil.copy2(INPUTS / "scheme_template.docx", target)
    document = docx.Document(str(target))
    document.styles["Normal"].font.name = "Arial"
    document.styles["Normal"].font.size = Pt(10)
    _patch_scheme_notes(document)
    _clear_body(document)
    answers = json.loads(ANSWERS.read_text(encoding="utf-8")) if ANSWERS.exists() else {}
    questions = load_questions()["questions"]
    _para(document, "PART A — MARKING GUIDE", bold=True, size=12,
          align=WD_ALIGN_PARAGRAPH.CENTER, before=8, after=8)
    for question in questions:
        if question["slot"].startswith("B"):
            continue
        _scheme_entry(document, question, answers)
    document.add_page_break()
    _para(document, "PART B — MARKING GUIDE", bold=True, size=12,
          align=WD_ALIGN_PARAGRAPH.CENTER, before=8, after=8)
    for question in questions:
        if not question["slot"].startswith("B"):
            continue
        _scheme_entry(document, question, answers)
    _para(document, "END OF MARKING SCHEME", italic=True, size=9,
          align=WD_ALIGN_PARAGRAPH.CENTER, before=12, after=4)
    document.save(str(target))
    return target


def _scheme_entry(document, question: dict, answers: dict) -> None:
    _question_heading(document, question["slot"], question["marks"])
    _para(document, f"Source: {question['paper_label']}, page {question['page']}",
          italic=True, size=9, after=3)
    answer = answers.get(question["slot"], {})
    if answer.get("answer"):
        _para(document, "Reference answer:", bold=True, size=9, after=2)
        for block in str(answer["answer"]).split("\n\n"):
            if block.strip():
                _para(document, block.strip(), size=9.5, after=2)
    if answer.get("marking"):
        _para(document, "Marking points:", bold=True, size=9, after=2)
        for point in answer["marking"]:
            _para(document, f"• {point}", size=9, italic=True, after=1)
    if answer.get("notes"):
        _para(document, f"Note: {answer['notes']}", italic=True, size=8,
              after=4)
    if not answer:
        _para(document, "Reference answer pending.", italic=True, size=9, after=4)


def _patch_page_count(path: Path, pages: int, kind: str) -> None:
    document = docx.Document(str(path))
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if kind == "paper" and text.startswith(
                "This examination paper consists"):
            paragraph.text = (
                f"This examination paper consists of {pages} printed pages.")
            break
        if kind == "scheme" and text.startswith(
                "This marking scheme consists"):
            paragraph.text = (
                f"This marking scheme consists of {pages} printed pages")
            break
    document.save(str(path))


def _export(docx_path: Path, pdf_path: Path) -> int:
    temporary = pdf_path.with_name(f"{pdf_path.stem}.tmp.pdf")
    pages = export_pdf(docx_path, temporary)
    temporary.replace(pdf_path)
    return pages


def build_pdf() -> dict:
    result = {}
    for kind in ("paper", "scheme"):
        docx_path = SEED / f"{kind}.docx"
        pdf_path = SEED / f"{kind}.pdf"
        pages = _export(docx_path, pdf_path)
        _patch_page_count(docx_path, pages, kind)
        pages = _export(docx_path, pdf_path)
        _patch_page_count(docx_path, pages, kind)
        result[kind] = {"pages": pages, "pdf": _rel(pdf_path)}
    return result


def qa() -> dict:
    result = {"paper": {}, "scheme": {}, "problems": []}
    for kind in ("paper", "scheme"):
        path = SEED / f"{kind}.pdf"
        with pymupdf.open(str(path)) as pdf:
            pages = [page.get_text() for page in pdf]
            info = {
                "pages": len(pdf),
                "images": sum(len(page.get_images(full=True)) for page in pdf),
                "right_overflow": [],
            }
            for index, page in enumerate(pdf):
                width = page.rect.width
                for block in page.get_text("dict")["blocks"]:
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            if span.get("bbox") and span["bbox"][2] > width - 30:
                                info["right_overflow"].append({
                                    "page": index + 1,
                                    "text": span.get("text", "")[:50]})
            text = "\n".join(pages)
            if kind == "paper":
                info["has_part_a"] = "PART A (80 MARKS)" in text
                info["has_part_b"] = "PART B (20 MARKS)" in text
            else:
                info["has_part_a"] = "PART A — MARKING GUIDE" in text
                info["has_part_b"] = "PART B — MARKING GUIDE" in text
            info["questions"] = [
                f"{slot}" for slot in
                ("A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9",
                 "A10", "B1")
                if f"QUESTION {slot}" in text
            ]
            if info["right_overflow"]:
                result["problems"].append(f"{kind}: right overflow")
            result[kind] = info
    if result["paper"].get("questions") != [
            "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10",
            "B1"]:
        result["problems"].append("paper is missing a question heading")
    if result["paper"].get("images", 0) < 8:
        result["problems"].append("paper has fewer than 8 asset images")
    if not result["scheme"].get("has_part_a"):
        result["problems"].append("scheme Part A heading missing")
    (SEED / "qa.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    return result


def comparison_report() -> Path:
    questions = load_questions()["questions"]
    assets = json.loads((EXP / "asset_manifest.json").read_text(
        encoding="utf-8"))["assets"]
    by_slot: dict[str, list[dict]] = {}
    for asset in assets:
        by_slot.setdefault(asset["slot"], []).append(asset)
    lines = [
        "# CSC429 pure-extraction comparison report",
        "",
        "One test seed. Each question is copied from the named source paper; "
        "figures are cropped from the source page; captions are native text; "
        "tables are native Word tables.",
        "",
        "| Slot | Source | Marks | Content | Asset verification |",
        "|---|---|---:|---|---|",
    ]
    for question in questions:
        kinds = []
        for asset in by_slot.get(question["slot"], []):
            kinds.append(
                f"{asset['kind']} {asset['width_px']}x{asset['height_px']}px")
        if question.get("figure_text"):
            kinds.append("native bit string")
        if question.get("tables"):
            kinds.append("native table")
        verification = ("asset SHA recorded in asset_manifest.json"
                        if by_slot.get(question["slot"])
                        else "native text; no asset")
        lines.append(
            f"| {question['slot']} | {question['paper_label']} p{question['page']} "
            f"| {question['marks']} | {', '.join(kinds) or 'native text'} "
            f"| {verification} |")
    lines.extend([
        "",
        "## Source and extraction notes",
        "",
        "- A1/A2 use native snippet text plus a captured portrait/photo; the "
        "picture is not OCR-dependent.",
        "- A3's 40-bit string is native text, not an image.",
        "- A4/A6 formulas are native text with Unicode subscripts.",
        "- A5/A7/A8/B1 figures are cropped from the source page at 300 dpi; "
        "captions are native text below the image. A9 is text-only.",
        "- B1's instruction table is recreated as a native Word table from the "
        "source layout.",
        "",
    ])
    target = EXP / "comparison_report.md"
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target



def _page_crop(pdf_path: Path, page_no: int, bbox: list[float],
               *, margin: float = 18.0) -> Image.Image:
    document = pymupdf.open(str(pdf_path))
    try:
        page = document[page_no - 1]
        rect = pymupdf.Rect(
            max(0, bbox[0] - margin), max(0, bbox[1] - margin),
            min(page.rect.width, bbox[2] + margin),
            min(page.rect.height, bbox[3] + margin))
        pix = page.get_pixmap(clip=rect, dpi=220)
        return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    finally:
        document.close()


def _side_by_side(source: Image.Image, generated: Image.Image,
                  left_label: str, right_label: str) -> Image.Image:
    target_height = 520
    def scale(image):
        ratio = target_height / max(1, image.height)
        return image.resize((max(1, int(image.width * ratio)), target_height))
    source, generated = scale(source), scale(generated)
    width = source.width + generated.width + 30
    sheet = Image.new("RGB", (width, target_height + 34), "white")
    sheet.paste(source, (10, 26))
    sheet.paste(generated, (source.width + 20, 26))
    draw = ImageDraw.Draw(sheet)
    draw.text((10, 6), left_label, fill="black")
    draw.text((source.width + 20, 6), right_label, fill="black")
    return sheet


def comparison_visuals() -> Path:
    from PIL import ImageDraw
    out_dir = EXP / "comparisons"
    out_dir.mkdir(parents=True, exist_ok=True)
    questions = load_questions()["questions"]
    assets = json.loads((EXP / "asset_manifest.json").read_text(
        encoding="utf-8"))["assets"]
    by_slot = {row["slot"]: row for row in assets}
    paper_pdf = SEED / "paper.pdf"
    mapping = {
        "A1": (2, 0), "A2": (3, 0), "A5": (4, 0), "A7": (5, 0),
        "A8": (6, 0), "A10": (6, 1), "B1": (8, 0),
    }
    pages = {}
    document = pymupdf.open(str(paper_pdf))
    try:
        for page_no in set(value[0] for value in mapping.values()):
            pages[page_no] = list(document[page_no - 1].get_image_info())
    finally:
        document.close()
    images = []
    for slot, (page_no, index) in mapping.items():
        source_row = by_slot[slot]
        image = Image.open(ROOT / source_row["path"]).convert("RGB")
        info = pages[page_no][index]
        generated = _page_crop(paper_pdf, page_no, info["bbox"])
        sheet = _side_by_side(
            image, generated,
            f"Source crop: {slot} {source_row['label']}",
            f"Generated paper: page {page_no}")
        target = out_dir / f"{slot}_source_vs_paper.png"
        sheet.save(target)
        images.append(sheet)
    # B1 native table: source table region vs generated table page region.
    source_page = _page_crop(INPUTS / "CSC429 (22).pdf", 6,
                             [35.0, 355.0, 545.0, 470.0])
    generated_page = _page_crop(paper_pdf, 8, [55.0, 330.0, 545.0, 500.0])
    table_sheet = _side_by_side(
        source_page, generated_page,
        "Source table: CSC429-2026-02 p6",
        "Generated native table: paper page 7")
    table_path = out_dir / "B1_table_source_vs_paper.png"
    table_sheet.save(table_path)
    images.append(table_sheet)
    pdf_path = EXP / "comparisons.pdf"
    images[0].save(pdf_path, save_all=True, append_images=images[1:])
    return pdf_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage", default="all",
        choices=("inputs", "assets", "paper", "scheme", "pdf", "qa",
                 "all"))
    args = parser.parse_args()
    copy_inputs()
    if args.stage in {"assets", "all"}:
        render_pages()
        crop_assets()
    if args.stage in {"paper", "all"}:
        build_paper()
    if args.stage in {"scheme", "all"}:
        build_scheme()
    if args.stage in {"pdf", "qa", "all"}:
        build_pdf()
        print(json.dumps(qa(), indent=2, ensure_ascii=False))
        if args.stage == "all":
            print(comparison_report())
            print(comparison_visuals())


if __name__ == "__main__":
    main()
