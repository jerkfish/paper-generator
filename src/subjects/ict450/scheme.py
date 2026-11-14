"""Build ICT450 marking-scheme DOCX/PDF proofs from the V4 answer bank."""
from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path

import docx
import pymupdf
from PIL import Image
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

from src import config
from src.assemble.pdf_export import export_pdf
from src.bank.store import BankStore, save_json
from src.subjects import forbidden
from src.subjects.ict450.assemble import (
    BANK,
    _library_markdown,
    build_category_plans,
)
from src.subjects.ict450.diagrams import render_erd

TEMPLATE = (config.PROJECT_ROOT / "data/reference/ICT450/"
            "ICT450_SCHEME_TEMPLATE_CLEAN.docx")
OUT = config.PROJECT_ROOT / "outputs/review/ICT450/schemes_v1"
CONTENT_WIDTH_CM = 16.4
MAX_IMAGE_HEIGHT_CM = 18.0


def _para(document, text: str = "", *, size: float = 10,
          bold: bool = False, italic: bool = False, align=None,
          before: float = 0, after: float = 4, keep_next: bool = False,
          indent_cm: float = 0, mono: bool = False, shading: str = ""):
    paragraph = document.add_paragraph()
    if align is not None:
        paragraph.alignment = align
    paragraph.paragraph_format.space_before = Pt(before)
    paragraph.paragraph_format.space_after = Pt(after)
    paragraph.paragraph_format.keep_with_next = keep_next
    paragraph.paragraph_format.line_spacing = 1.08
    if indent_cm:
        paragraph.paragraph_format.left_indent = Cm(indent_cm)
    if shading:
        ppr = paragraph._p.get_or_add_pPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), shading)
        ppr.append(shd)
    run = paragraph.add_run(text)
    run.font.name = "Consolas" if mono else "Arial"
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    return paragraph


def _multiline(document, lines: list[str], *, size: float = 8.5,
               mono: bool = True, shading: str = "", after: float = 6,
               indent_cm: float = 0.3):
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(1)
    paragraph.paragraph_format.space_after = Pt(after)
    paragraph.paragraph_format.line_spacing = 1.05
    paragraph.paragraph_format.left_indent = Cm(indent_cm)
    if shading:
        ppr = paragraph._p.get_or_add_pPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), shading)
        ppr.append(shd)
    run = paragraph.add_run()
    run.font.name = "Consolas" if mono else "Arial"
    run.font.size = Pt(size)
    for index, line in enumerate(lines):
        if index:
            run.add_break()
        run.add_text(line)
    return paragraph


def _bullet(document, text: str, *, size: float = 9.5,
            indent_cm: float = 0.6) -> None:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.left_indent = Cm(indent_cm)
    paragraph.paragraph_format.first_line_indent = Cm(-0.35)
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.paragraph_format.line_spacing = 1.05
    run = paragraph.add_run("•  " + text)
    run.font.name = "Arial"
    run.font.size = Pt(size)


def _set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def _set_table_borders(table) -> None:
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "4")
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), "94A3B8")
        borders.append(element)
    tbl_pr.append(borders)


def _add_table(document, block: dict) -> None:
    if block.get("caption"):
        _para(document, str(block["caption"]), size=8.5, italic=True,
              align=WD_ALIGN_PARAGRAPH.CENTER, after=2,
              keep_next=True)
    columns = [str(col) for col in block.get("columns") or []]
    rows = block.get("rows") or []
    table = document.add_table(rows=1, cols=len(columns))
    try:
        table.style = "Table Grid"
    except KeyError:
        _set_table_borders(table)
    table.autofit = False
    header = table.rows[0].cells
    for index, column in enumerate(columns):
        header[index].text = column
        _set_cell_shading(header[index], "1F3864")
        for paragraph in header[index].paragraphs:
            for run in paragraph.runs:
                run.font.name = "Arial"
                run.font.size = Pt(8)
                run.bold = True
                run.font.color.rgb = docx.shared.RGBColor(0xFF, 0xFF, 0xFF)
    for row in rows:
        cells = table.add_row().cells
        for index, value in enumerate(row):
            if index >= len(cells):
                break
            cells[index].text = str(value)
            for paragraph in cells[index].paragraphs:
                paragraph.paragraph_format.space_after = Pt(0)
                for run in paragraph.runs:
                    run.font.name = "Arial"
                    run.font.size = Pt(8)
    cell_width = Cm(CONTENT_WIDTH_CM / max(len(columns), 1))
    for row in table.rows:
        tr_pr = row._tr.get_or_add_trPr()
        tr_pr.append(OxmlElement("w:cantSplit"))
        for cell in row.cells:
            cell.width = cell_width
    _para(document, "", size=4, after=2)


def _image_width(path: Path) -> float:
    with Image.open(path) as image:
        width, height = image.size
    aspect = height / max(width, 1)
    width_cm = CONTENT_WIDTH_CM
    if width_cm * aspect > MAX_IMAGE_HEIGHT_CM:
        width_cm = MAX_IMAGE_HEIGHT_CM / aspect
    return width_cm


def _add_picture(document, path: Path, caption: str = "") -> bool:
    if not path.is_file():
        return False
    width = _image_width(path)
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(4)
    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.add_run().add_picture(str(path), width=Cm(width))
    if caption:
        _para(document, caption, size=8.5, italic=True,
              align=WD_ALIGN_PARAGRAPH.CENTER, after=4)
    return True


def _render_block(document, block: dict) -> None:
    kind = block.get("type")
    if kind == "p":
        _para(document, str(block.get("text") or ""), after=4)
    elif kind == "h":
        _para(document, str(block.get("text") or ""), size=10, bold=True,
              before=5, after=2, keep_next=True)
    elif kind == "callout":
        paragraph = _para(document, str(block.get("text") or ""), size=9,
                          italic=True, after=5, shading="FFF7ED")
        ppr = paragraph._p.get_or_add_pPr()
        borders = OxmlElement("w:pBdr")
        left = OxmlElement("w:left")
        left.set(qn("w:val"), "single")
        left.set(qn("w:sz"), "18")
        left.set(qn("w:space"), "6")
        left.set(qn("w:color"), "F59E0B")
        borders.append(left)
        ppr.append(borders)
    elif kind == "bullets":
        for item in block.get("items") or []:
            _bullet(document, str(item))
    elif kind == "sub":
        label = str(block.get("label") or "")
        marks = block.get("marks")
        head = f"({label})"
        if block.get("text"):
            head += f"  {block['text']}"
        if marks:
            head += f"   [{marks} marks]"
        _para(document, head, size=10, bold=True, before=4, after=2,
              keep_next=True)
        for item in block.get("items") or []:
            _bullet(document, str(item))
        for nested in block.get("blocks") or []:
            _render_block(document, nested)
    elif kind == "sql":
        if block.get("caption"):
            _para(document, str(block["caption"]), size=8.5, italic=True,
                  after=1, keep_next=True)
        _multiline(document, str(block.get("code") or "").splitlines(),
                   size=8.3, mono=True, shading="F1F5F9")
    elif kind == "schema":
        if block.get("caption"):
            _para(document, str(block["caption"]), size=8.5, italic=True,
                  after=1, keep_next=True)
        _multiline(document, [str(line) for line in block.get("lines") or []],
                   size=8.3, mono=True, shading="F8FAFC")
    elif kind == "table":
        _add_table(document, block)
    elif kind == "erd":
        path = Path(str(block.get("path") or ""))
        if not path.is_file() and block.get("spec"):
            path = Path(str(render_erd(block["spec"], path)))
        _add_picture(document, path, str(block.get("caption") or ""))
    else:
        return


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
        raise RuntimeError("scheme template has no section break")
    for child in children[cut + 1:]:
        if child.tag == qn("w:sectPr"):
            continue
        body.remove(child)


def _patch_notes(document) -> None:
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text.startswith("Generated answers show working"):
            paragraph.text = (
                "Answers are unofficial model answers, not official UTM "
                "marking schemes.")
        elif text.startswith("Generated marking points state"):
            paragraph.text = (
                "Marking points state the expected answer and the allocation "
                "of marks; every question retains its source paper and page "
                "reference.")
        elif text.startswith("This marking scheme accompanies"):
            paragraph.text = (
                "This marking scheme accompanies the ICT450 mock paper "
                "(November 2026).")


def _question_heading(document, number: int, marks: int) -> None:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(6)
    paragraph.paragraph_format.keep_with_next = True
    section = document.sections[-1]
    width = section.page_width - section.left_margin - section.right_margin
    paragraph.paragraph_format.tab_stops.add_tab_stop(
        width, WD_TAB_ALIGNMENT.RIGHT)
    run = paragraph.add_run(f"QUESTION {number}\t({marks} marks)")
    run.font.name = "Arial"
    run.font.size = Pt(12)
    run.bold = True


def _scheme_entry(document, question: dict, answer: dict, number: int,
                  *, page_break: bool) -> None:
    if page_break:
        document.add_page_break()
    _question_heading(document, number, int(question.get("marks") or 0))
    _para(document, f"Source: {question.get('source_paper')} · page "
          f"{question.get('pages')} · bank id {question.get('id')}",
          size=8.5, italic=True, after=3)
    _para(document, "Reference answer", size=10, bold=True, before=2,
          after=3, keep_next=True)
    for block in answer.get("blocks") or []:
        _render_block(document, block)
    marking = answer.get("marking") or []
    if marking:
        _para(document, "Marking guide", size=10, bold=True, before=8,
              after=3, keep_next=True)
        for point in marking:
            _bullet(document, str(point), size=9, indent_cm=0.5)
    _para(document, f"Provenance: {answer.get('provenance')} · confidence "
          f"{answer.get('confidence')} · {answer.get('source', '')}",
          size=7.8, italic=True, before=6, after=1)
    if answer.get("kb_sources"):
        _para(document, "Knowledge base basis: " +
              "; ".join(str(source) for source in answer["kb_sources"]),
              size=7.8, italic=True, after=2)
    if answer.get("assumptions"):
        _para(document, "Assumptions / notes", size=8.5, bold=True,
              before=4, after=2)
        for item in answer["assumptions"]:
            _bullet(document, str(item), size=8.3, indent_cm=0.5)


def _patch_page_count(path: Path, pages: int) -> None:
    document = docx.Document(str(path))
    for paragraph in document.paragraphs:
        if paragraph.text.strip().startswith(
                "This marking scheme consists"):
            for run in paragraph.runs:
                if "consists" in run.text or "printed" in run.text:
                    run.text = f"This marking scheme consists of {pages} " \
                               "printed pages."
            paragraph.text = f"This marking scheme consists of {pages} " \
                             "printed pages."
            break
    document.save(str(path))


def _pdf_info(path: Path) -> dict:
    with pymupdf.open(str(path)) as pdf:
        text = "\n".join(page.get_text() for page in pdf)
        right = []
        bottom = []
        for index, page in enumerate(pdf):
            width, height = page.rect.width, page.rect.height
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        bbox = span.get("bbox")
                        if not bbox:
                            continue
                        if bbox[2] > width - 20:
                            right.append({"page": index + 1,
                                          "text": span.get("text", "")[:60]})
                        if bbox[3] > height - 20:
                            bottom.append({"page": index + 1,
                                           "text": span.get("text", "")[:60]})
        return {
            "path": str(path),
            "pages": len(pdf),
            "images": sum(len(page.get_images(full=True)) for page in pdf),
            "text": text,
            "right_overflow": right,
            "bottom_overflow": bottom,
        }


def build_scheme(seed: int, plan: dict, answers: dict,
                 *, force: bool = False) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    docx_path = OUT / f"seed_{seed:02d}_scheme.docx"
    pdf_path = OUT / f"seed_{seed:02d}_scheme.pdf"
    if docx_path.exists() and not force:
        return {"seed": seed, "cached": True, "path": str(docx_path)}
    shutil.copy2(TEMPLATE, docx_path)
    document = docx.Document(str(docx_path))
    document.styles["Normal"].font.name = "Arial"
    document.styles["Normal"].font.size = Pt(10)
    _patch_notes(document)
    _clear_body(document)
    _para(document, "MARKING GUIDE", size=12, bold=True,
          align=WD_ALIGN_PARAGRAPH.CENTER, after=8)
    store = BankStore(BANK)
    for index, slot in enumerate(plan["slots"], start=1):
        question = store.load_question(slot["question_id"])
        answer = answers.get(question["id"])
        if not answer:
            raise RuntimeError(f"missing answer for {question['id']}")
        _scheme_entry(document, question, answer, index,
                      page_break=index > 1)
    document.save(str(docx_path))
    pages = export_pdf(docx_path, pdf_path)
    _patch_page_count(docx_path, pages)
    pages = export_pdf(docx_path, pdf_path)
    info = _pdf_info(pdf_path)
    problems = []
    for number in range(1, 6):
        if f"QUESTION {number}" not in info["text"]:
            problems.append(f"missing QUESTION {number}")
    if info["right_overflow"]:
        problems.append(f"{len(info['right_overflow'])} right-margin spans")
    if info["bottom_overflow"]:
        problems.append(f"{len(info['bottom_overflow'])} bottom-margin spans")
    scan = forbidden.scan([docx_path, pdf_path], "ICT450")
    if scan["hits"]:
        problems.append("forbidden tokens")
    result = {
        "seed": seed,
        "pages": pages,
        "images": info["images"],
        "questions": [slot["question_id"] for slot in plan["slots"]],
        "right_overflow": info["right_overflow"],
        "bottom_overflow": info["bottom_overflow"],
        "forbidden_hits": scan["hits"],
        "problems": problems,
        "files": {"scheme_docx": str(docx_path),
                  "scheme_pdf": str(pdf_path)},
    }
    save_json(OUT / f"seed_{seed:02d}_qa.json", result)
    if problems:
        raise RuntimeError(f"seed {seed} scheme QA failed: {problems}")
    return result


def attach_to_library(seeds: list[int]) -> dict:
    """Attach approved scheme documents to the local Library cache."""
    from src.app.jobs import cache_path

    answers = BankStore(BANK).answers_by_question()
    manifest_path = (config.WEB_CACHE_DIR / "ICT450" /
                     "library_manifest.json")
    if not manifest_path.is_file():
        raise SystemExit("run the V6 library build before attaching schemes")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = {int(row["seed"]): row for row in manifest.get("seeds") or []}
    attached = []
    for seed in seeds:
        out = cache_path("realistic", seed, None, subject="ICT450")
        plan_path = out / "plan.json"
        if not plan_path.is_file():
            raise SystemExit(f"seed {seed}: no library plan at {plan_path}")
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        missing = [slot["question_id"] for slot in plan["slots"]
                   if slot["question_id"] not in answers]
        if missing:
            raise SystemExit(
                f"seed {seed}: missing V4 answers for {', '.join(missing)}")
        scheme_docx = OUT / f"seed_{seed:02d}_scheme.docx"
        scheme_pdf = OUT / f"seed_{seed:02d}_scheme.pdf"
        if not scheme_docx.is_file() or not scheme_pdf.is_file():
            build_scheme(seed, plan, answers, force=True)
        shutil.copy2(scheme_docx, out / "scheme.docx")
        shutil.copy2(scheme_pdf, out / "scheme.pdf")
        qa_path = OUT / f"seed_{seed:02d}_qa.json"
        qa = (json.loads(qa_path.read_text(encoding="utf-8"))
              if qa_path.is_file() else {})
        pages = int(qa.get("pages") or 0)
        meta_path = out / "meta.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta.update({
            "paper_only": False,
            "v4_answers": "approved_model_unofficial",
            "answers_approved": True,
            "answers_approved_on": "2026-11-11",
            "scheme_provenance": "model_unofficial",
            "scheme_pages": pages,
        })
        files = dict(meta.get("files") or {})
        files["scheme_docx"] = str(out / "scheme.docx")
        files["scheme_pdf"] = str(out / "scheme.pdf")
        meta["files"] = files
        meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False)
                             + "\n", encoding="utf-8")
        row = rows.get(seed)
        if row is not None:
            row["files"] = dict(files)
            row["scheme_pages"] = pages
            row["scheme_provenance"] = "model_unofficial"
            row["answers_approved"] = True
        attached.append(seed)
    manifest["schemes_attached"] = sorted(
        set(manifest.get("schemes_attached") or []) | set(attached))
    manifest["scheme_status"] = (
        "seeds 1–3 attached from owner-approved V4 models; seeds 4–20 "
        "remain paper-only until V4 is complete")
    save_json(manifest_path, manifest)
    (manifest_path.parent / "library_manifest.md").write_text(
        _library_markdown(manifest), encoding="utf-8")
    return {"attached": attached, "manifest": str(manifest_path)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", default="1-3")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--attach-library", action="store_true")
    args = parser.parse_args()
    if "-" in args.seeds:
        first, last = args.seeds.split("-")
        seeds = list(range(int(first), int(last) + 1))
    else:
        seeds = [int(value) for value in args.seeds.split(",")]
    if args.attach_library:
        print(attach_to_library(seeds), flush=True)
        return
    store = BankStore(BANK)
    questions = list(store.approved_questions())
    plans = build_category_plans(questions, seed_count=max(seeds),
                                 reuse_cap=4)
    answers = store.answers_by_question()
    for seed in seeds:
        print(build_scheme(seed, plans[seed - 1], answers,
                           force=args.force), flush=True)


if __name__ == "__main__":
    main()
