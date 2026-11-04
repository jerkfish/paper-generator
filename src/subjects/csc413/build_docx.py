"""CSC413 stage-7 paper and marking-scheme builder.

The paper starts from the approved CSC413 cover template and appends
PART A/B/C/D.  The scheme uses the owner-supplied standard marking-scheme
template and appends answer keys and worked answers.  PDF export uses the
shared Word/LibreOffice exporter.

    uv run python -m src.subjects.csc413.build_docx --seed 1 --apply
"""
from __future__ import annotations

import argparse
import json
import tempfile
import time
import zipfile
from pathlib import Path

import docx
import pymupdf
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

from src import config
from src.app.filenames import utc_year
from src.assemble.pdf_export import export_pdf
from src.subjects.csc413.generators import generate_paper
from src.subjects.csc413.planner import build_plan

SUBJECT = "CSC413"
TRACKING = config.TRACKING_DIR / "csc413"
TEMPLATE = config.subject_reference_dir("CSC413") / "CSC413 TEMPLATE.docx"
SCHEME_TEMPLATE = (config.subject_reference_dir("CSC413") /
                   "CSC413 MARKING SCHEME TEMPLATE.docx")
DEFAULT_OUT = TRACKING / "build_sample"
FORBIDDEN = ("CSC662", "MAT133", "CSC402", "TODO", "placeholder",
             "data/reference")


def _run(paragraph, text: str, *, size: float = 10.5, bold: bool = False,
         italic: bool = False) -> None:
    run = paragraph.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.name = "Arial"
    run.font.size = Pt(size)


def _para(doc, text: str = "", *, size: float = 10.5, bold: bool = False,
          italic: bool = False, align=None, before: float = 0,
          after: float = 4, keep: bool = False):
    paragraph = doc.add_paragraph()
    if align is not None:
        paragraph.alignment = align
    pf = paragraph.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.keep_with_next = keep
    if text:
        _run(paragraph, text, size=size, bold=bold, italic=italic)
    return paragraph


def _marks(doc, marks: int, *, keep: bool = False) -> None:
    _para(doc, f"({marks} mark{'s' if marks != 1 else ''})", size=9.5,
          italic=True, align=WD_ALIGN_PARAGRAPH.RIGHT, after=3, keep=keep)


def _part_heading(doc, text: str) -> None:
    _para(doc, text, size=12, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT,
          before=10, after=6, keep=True)


def _question_heading(doc, number: str) -> None:
    _para(doc, f"QUESTION {number[1:]}", size=11.5, bold=True,
          before=10, after=4, keep=True)


def _numbered_para(doc, number: int, text: str, *, size: float = 11,
                   before: float = 2, after: float = 2,
                   bold_number: bool = True):
    paragraph = doc.add_paragraph()
    pf = paragraph.paragraph_format
    pf.left_indent = Inches(0.35)
    pf.first_line_indent = Inches(-0.35)
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.keep_with_next = True
    pf.tab_stops.add_tab_stop(Inches(0.35))
    _run(paragraph, f"{number}.\t", size=size, bold=bold_number)
    _run(paragraph, text, size=size)
    return paragraph


def _set_table_borders(table) -> None:
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement(f"w:{side}")
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "4")
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), "808080")
        borders.append(element)
    tbl_pr.append(borders)


def _set_cell_margins(table) -> None:
    tbl_pr = table._tbl.tblPr
    margins = OxmlElement("w:tblCellMar")
    for side, width in (("top", "50"), ("left", "70"),
                        ("bottom", "50"), ("right", "70")):
        element = OxmlElement(f"w:{side}")
        element.set(qn("w:w"), width)
        element.set(qn("w:type"), "dxa")
        margins.append(element)
    tbl_pr.append(margins)


def _no_split(table) -> None:
    for row in table.rows:
        tr_pr = row._tr.get_or_add_trPr()
        if tr_pr.find(qn("w:cantSplit")) is None:
            tr_pr.append(OxmlElement("w:cantSplit"))


def _no_borders(table) -> None:
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement(f"w:{side}")
        element.set(qn("w:val"), "nil")
        borders.append(element)
    tbl_pr.append(borders)


def _option_line(doc, left: str, right: str, *, keep: bool = True) -> None:
    paragraph = doc.add_paragraph()
    pf = paragraph.paragraph_format
    pf.left_indent = Inches(0.65)
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.keep_with_next = keep
    pf.tab_stops.add_tab_stop(Inches(3.35))
    _run(paragraph, f"{left}\t{right}", size=10.5)


def _option_lines(doc, options: list[str]) -> None:
    _option_line(doc, f"A. {options[0]}", f"B. {options[1]}", keep=True)
    _option_line(doc, f"C. {options[2]}", f"D. {options[3]}", keep=False)


def _matching_table(doc, options: list[dict]) -> None:
    _para(doc, "Table A", size=11, bold=True,
          align=WD_ALIGN_PARAGRAPH.CENTER, before=3, after=3, keep=True)
    rows = 3
    cols = 5
    table = doc.add_table(rows=rows, cols=cols)
    table.autofit = False
    _set_table_borders(table)
    _set_cell_margins(table)
    width = Inches(1.25)
    for index, option in enumerate(options):
        cell = table.rows[index // cols].cells[index % cols]
        cell.width = width
        cell.text = ""
        cell.paragraphs[0].paragraph_format.space_after = Pt(1)
        _run(cell.paragraphs[0], f"{option['label']}. {option['text']}",
             size=10.5)
    _no_split(table)
    _para(doc, "", after=3)


def _build_paper_docx(paper: dict, out_docx: Path,
                      template: Path = TEMPLATE) -> Path:
    doc = docx.Document(str(template))
    section = doc.sections[-1]
    section.left_margin = Inches(0.9)
    section.right_margin = Inches(0.9)
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    doc.add_page_break()

    _part_heading(doc, "PART A (15 MARKS)")
    _para(doc, "State TRUE (T) or FALSE (F) for the following statements.",
          size=11, after=8)
    for index, question in enumerate(
            [q for q in paper["questions"] if q["part"] == "A"], start=1):
        _numbered_para(doc, index, question["stem"])

    _part_heading(doc, "PART B (15 MARKS)")
    _para(doc, "Select the most appropriate answer from Table A for each of "
          "the following questions.", size=11, after=4)
    _matching_table(doc, paper["matching_options"])
    for index, question in enumerate(
            [q for q in paper["questions"] if q["part"] == "B"], start=1):
        _numbered_para(doc, index, question["stem"])

    doc.add_page_break()
    _part_heading(doc, "PART C (30 MARKS)")
    _para(doc, "Choose the correct answer for each question.",
          size=11, after=8)
    for index, question in enumerate(
            [q for q in paper["questions"] if q["part"] == "C"], start=1):
        _numbered_para(doc, index, question["stem"], before=3, after=1)
        _option_lines(doc, question["options"])

    _part_heading(doc, "PART D (40 MARKS)")
    for question in [q for q in paper["questions"] if q["part"] == "D"]:
        _question_heading(doc, question["number"])
        _para(doc, question["stem"], size=10.5, after=4, keep=True)
        for part in question["parts"]:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.left_indent = Inches(0.3)
            p.paragraph_format.first_line_indent = Inches(-0.3)
            p.paragraph_format.keep_with_next = True
            _run(p, f"{part['label']}) ", bold=True)
            _run(p, part["text"])
            _marks(doc, part["marks"], keep=True)

    _para(doc, "END OF QUESTION PAPER", italic=True, size=9,
          align=WD_ALIGN_PARAGRAPH.CENTER, before=14, after=4)
    out_docx.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_docx))
    return out_docx


def _replace_text_nodes(xml: str) -> str:
    import re
    replacements = (
        ("CSC662", "CSC413"),
        ("COMPUTER SECURITY", "INTERACTIVE MULTIMEDIA"),
        ("OCTOBER 2026 (MOCK)", "NOV 2026 (MOCK)"),
        ("CS/MOCK", "CS/NOV"),
        ("OCT", ""),
    )
    pattern = re.compile(r"(<w:t\b[^>]*>)(.*?)(</w:t>)", re.S)

    def replace(match):
        text = match.group(2)
        for old, new_value in replacements:
            text = text.replace(old, new_value)
        return match.group(1) + text + match.group(3)

    return pattern.sub(replace, xml)


def _fit_scheme_title(xml: str) -> str:
    """Fit the short scheme-cover title on one line."""
    import re
    pattern = re.compile(
        r"(<w:p\b(?:(?!</w:p>).)*?<w:t[^>]*>INTERACTIVE MULTIMEDIA</w:t>"
        r".*?</w:p>)", re.S)

    def replace(match: re.Match) -> str:
        return match.group(1).replace('w:val="23"', 'w:val="16"')

    return pattern.sub(replace, xml)


def _rewrite_scheme_template(source: Path, target: Path) -> None:
    with zipfile.ZipFile(source) as zin, zipfile.ZipFile(
            target, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if (item.filename == "word/document.xml" or
                    (item.filename.startswith("word/header") and
                     item.filename.endswith(".xml"))):
                xml = _replace_text_nodes(data.decode("utf-8"))
                if item.filename == "word/document.xml":
                    xml = _fit_scheme_title(xml)
                data = xml.encode("utf-8")
            zout.writestr(item, data)


def _set_paragraph_text(paragraph, text: str, *, left: bool = False) -> None:
    first = paragraph.runs[0] if paragraph.runs else None
    font_name = first.font.name if first is not None else "Arial"
    font_size = first.font.size if first is not None else Pt(10)
    bold = first.bold if first is not None else False
    italic = first.italic if first is not None else False
    for run in list(paragraph.runs):
        run._r.getparent().remove(run._r)
    for br in list(paragraph._p.findall(qn("w:br"))):
        br.getparent().remove(br)
    for br in list(paragraph._p.findall(qn("w:cr"))):
        br.getparent().remove(br)
    run = paragraph.add_run(text)
    run.font.name = font_name
    run.font.size = font_size
    run.bold = bold
    run.italic = italic
    if left:
        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        pf = paragraph.paragraph_format
        pf.tab_stops.clear_all()
        pf.right_indent = None
        if pf.left_indent is not None and pf.left_indent > Inches(1):
            pf.left_indent = Inches(0.5)


def _patch_scheme_notes(doc, paper: dict) -> None:
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text.startswith("This marking scheme accompanies"):
            _set_paragraph_text(
                paragraph,
                "This marking scheme accompanies the CSC413 mock paper "
                "(NOV 2026).", left=True)
        elif text.startswith("Computed answers show working"):
            _set_paragraph_text(
                paragraph,
                "Answers show the expected marking points; all questions are "
                "deterministic and paper-derived; no lecture slides are used.", left=True)
        elif text.startswith("Supported theory marking points"):
            _set_paragraph_text(
                paragraph,
                "Marking points show the expected answer and the allocation "
                "of marks; unresolved slots would remain visible.", left=True)
        elif text.startswith("Part A ="):
            _set_paragraph_text(
                paragraph,
                "Part A = 15 x 1 mark; Part B = 15 x 1 mark; "
                "Part C = 30 x 1 mark; Part D = 4 x 10 marks; total = 100.", left=True)
        elif text.startswith("Computed:"):
            _set_paragraph_text(
                paragraph,
                f"Questions: {paper['question_count']}. "
                f"Slots: {paper['slot_count']}. Placeholders: 0. "
                "No LLM call.", left=True)
        elif text.startswith("Near-copy rejection"):
            _set_paragraph_text(
                paragraph,
                "Structure derived from 15 unique CSC413 past papers; "
                "no past-paper text is copied.", left=True)


def _answer_key_table(doc, headers: tuple[str, ...],
                      rows: list[tuple[str, ...]],
                      widths: tuple[float, ...], *, size: float = 9) -> None:
    table = doc.add_table(rows=1, cols=len(headers))
    table.autofit = True
    _set_table_borders(table)
    _set_cell_margins(table)
    for cell, width, text in zip(table.rows[0].cells, widths, headers):
        cell.width = Inches(width)
        cell.text = ""
        cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP
        cell.paragraphs[0].paragraph_format.space_after = Pt(2)
        _run(cell.paragraphs[0], text, bold=True, size=size)
    for row in rows:
        cells = table.add_row().cells
        for cell, width, text in zip(cells, widths, row):
            cell.width = Inches(width)
            cell.text = ""
            cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP
            cell.paragraphs[0].paragraph_format.space_after = Pt(2)
            _run(cell.paragraphs[0], text, size=size)
    _no_split(table)


def _scheme_body(doc, paper: dict) -> None:
    _part_heading(doc, "PART A - ANSWER KEY")
    _answer_key_table(
        doc, ("Q", "Ans", "Statement", "Explanation"),
        [(q["number"], q["answer"], q["stem"], q["solution"])
         for q in paper["questions"] if q["part"] == "A"],
        (0.45, 0.6, 2.8, 2.9))

    doc.add_page_break()
    _part_heading(doc, "PART B - ANSWER KEY")
    _answer_key_table(
        doc, ("Q", "Ans", "Term", "Definition"),
        [(q["number"], q["answer"], q["answer_term"], q["stem"])
         for q in paper["questions"] if q["part"] == "B"],
        (0.45, 0.55, 1.5, 4.2))

    doc.add_page_break()
    _part_heading(doc, "PART C - ANSWER KEY")
    _answer_key_table(
        doc, ("Q", "Ans", "Correct answer"),
        [(q["number"], q["answer"], q["answer_text"])
         for q in paper["questions"] if q["part"] == "C"],
        (0.5, 0.6, 5.8))

    doc.add_page_break()
    _part_heading(doc, "PART D - WORKED ANSWERS")
    for question in [q for q in paper["questions"] if q["part"] == "D"]:
        _question_heading(doc, question["number"])
        _para(doc, f"Topic: {question['topic'].replace('_', ' ')}",
              italic=True, size=9, after=3, keep=True)
        _para(doc, question["stem"], size=10, after=3, keep=True)
        for index, part in enumerate(question["parts"]):
            more = index < len(question["parts"]) - 1
            _para(doc, f"{part['label']}) {part['text']}", bold=True,
                  size=10, after=2, keep=True)
            _para(doc, part["answer"], size=10, after=2, keep=True)
            _marks(doc, part["marks"], keep=more)

    _para(doc, "END OF MARKING SCHEME", italic=True, size=9,
          align=WD_ALIGN_PARAGRAPH.CENTER, before=14, after=4)


def _build_scheme_docx(paper: dict, out_docx: Path,
                       template: Path = SCHEME_TEMPLATE) -> Path:
    """Append answer keys to the owner-supplied CSC413 scheme template."""
    out_docx.parent.mkdir(parents=True, exist_ok=True)
    doc = docx.Document(str(template))
    _scheme_body(doc, paper)
    doc.save(str(out_docx))
    return out_docx


def _cover_page_count(docx_path: Path, pages: int) -> None:
    document = docx.Document(str(docx_path))
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text.startswith("This examination paper consists of"):
            for run in paragraph.runs:
                run.text = ""
            paragraph.runs[0].text = (
                f"This examination paper consists of {pages} printed pages.")
            break
    document.save(str(docx_path))


def _scheme_page_count(docx_path: Path, pages: int) -> None:
    doc = docx.Document(str(docx_path))
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text.startswith("This marking scheme consists of"):
            _set_paragraph_text(
                paragraph,
                f"This marking scheme consists of {pages} printed pages")
            break
    doc.save(str(docx_path))


def _docx_text(path: Path) -> str:
    document = docx.Document(str(path))
    parts = [p.text for p in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                parts.append(cell.text)
    for section in document.sections:
        for part in (section.header, section.footer,
                     section.first_page_header, section.first_page_footer):
            try:
                parts.extend(p.text for p in part.paragraphs)
            except Exception:
                continue
    return "\n".join(parts)


def _validate_docx(path: Path, paper: dict, *, scheme: bool) -> dict:
    result = {"path": str(path), "xml_valid": False, "forbidden_tokens": [],
              "missing": [], "problems": []}
    try:
        with zipfile.ZipFile(str(path)) as archive:
            archive.read("word/document.xml")
        result["xml_valid"] = True
    except Exception as error:
        result["problems"].append(f"invalid DOCX: {error}")
        return result
    text = _docx_text(path)
    normalised = " ".join(text.split())
    result["forbidden_tokens"] = [token for token in FORBIDDEN if token in text]
    if scheme:
        if "MARKING SCHEME" not in text:
            result["missing"].append("MARKING SCHEME heading")
        for heading in ("PART A - ANSWER KEY", "PART B - ANSWER KEY",
                        "PART C - ANSWER KEY", "PART D - WORKED ANSWERS"):
            if heading not in text:
                result["missing"].append(heading)
        for question in paper["questions"]:
            if question["part"] == "A":
                if f"{question['number']} {question['answer']}" not in normalised:
                    result["missing"].append(f"{question['number']} answer")
            elif question["part"] == "B":
                answer = " ".join(
                    f"{question['number']} {question['answer']} "
                    f"{question['answer_term']}".split())
                if answer not in normalised:
                    result["missing"].append(f"{question['number']} answer")
            elif question["part"] == "C":
                if f"{question['number']} {question['answer']}" not in normalised:
                    result["missing"].append(f"{question['number']} answer")
            else:
                for part in question["parts"]:
                    answer = " ".join(part["answer"].split())[:60]
                    if answer not in normalised:
                        result["missing"].append(
                            f"{question['number']}{part['label']} answer")
    else:
        for heading in ("PART A (15 MARKS)", "PART B (15 MARKS)",
                        "PART C (30 MARKS)", "PART D (40 MARKS)",
                        "END OF QUESTION PAPER"):
            if heading not in text:
                result["missing"].append(heading)
        for question in paper["questions"]:
            if question["part"] in {"A", "B", "C"}:
                if question["stem"][:30] not in text:
                    result["missing"].append(f"{question['number']} stem")
            else:
                for part in question["parts"]:
                    if part["text"][:30] not in text:
                        result["missing"].append(
                            f"{question['number']}{part['label']} text")
    if result["forbidden_tokens"]:
        result["problems"].append(
            "forbidden tokens: " + ", ".join(result["forbidden_tokens"]))
    if result["missing"]:
        result["problems"].append(
            "missing content: " + ", ".join(result["missing"][:8]))
    return result


def _validate_pdf(path: Path, *, scheme: bool) -> dict:
    result = {"path": str(path), "pages": 0, "page1_cover": False,
              "body_starts_page2": False, "right_overflow": [],
              "problems": []}
    with pymupdf.open(str(path)) as pdf:
        result["pages"] = len(pdf)
        if not len(pdf):
            result["problems"].append("PDF has no pages")
            return result
        pages = [page.get_text() for page in pdf]
        result["page1_cover"] = (
            "CSC413" in pages[0] and
            ("INTERACTIVE MULTIMEDIA" in pages[0] or "MARKING SCHEME" in pages[0]))
        if not scheme and len(pages) > 1:
            result["body_starts_page2"] = "PART A" in pages[1]
        for index, page in enumerate(pdf):
            width = page.rect.width
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        if span.get("bbox") and span["bbox"][2] > width - 30:
                            result["right_overflow"].append({
                                "page": index + 1,
                                "text": span.get("text", "")[:60],
                                "x1": round(span["bbox"][2], 1),
                                "width": round(width, 1),
                            })
    if not scheme:
        if result["pages"] < 2:
            result["problems"].append("paper has fewer than 2 pages")
        if not result["page1_cover"]:
            result["problems"].append("cover page missing")
        if not result["body_starts_page2"]:
            result["problems"].append("PART A does not start on page 2")
    if result["right_overflow"]:
        result["problems"].append(
            f"right overflow on {len(result['right_overflow'])} span(s)")
    return result


def build_seed(seed: int, out_dir: Path | None = None,
               export: bool = True, force: bool = False) -> dict:
    out = Path(out_dir) if out_dir is not None else DEFAULT_OUT
    meta_path = out / "meta.json"
    if not force and meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            files = [Path(value) for value in (meta.get("files") or {}).values()
                     if value]
            if files and all(path.exists() for path in files):
                qa_path = out / "qa.json"
                qa = (json.loads(qa_path.read_text(encoding="utf-8"))
                      if qa_path.exists() else {})
                return {
                    **qa,
                    "seed": seed, "cached": True, "path": str(out),
                    "pdf": bool(meta.get("files", {}).get("paper_pdf")),
                    "scheme_pdf_available": bool(meta.get("files", {}).get("scheme_pdf")),
                    "files": meta.get("files", {}),
                    "problems": qa.get("problems", []),
                }
        except Exception:
            pass
    out.mkdir(parents=True, exist_ok=True)
    plan = build_plan(seed)
    paper = generate_paper(plan)
    (out / "paper.json").write_text(
        json.dumps(paper, indent=2), encoding="utf-8")
    paper_docx = out / f"CSC413 Seed {seed:02d} 2026.docx"
    scheme_docx = out / f"CSC413 Seed {seed:02d} 2026 - Marking Scheme.docx"
    _build_paper_docx(paper, paper_docx)
    _build_scheme_docx(paper, scheme_docx)
    qa = {
        "subject": SUBJECT,
        "seed": seed,
        "paper_docx": _validate_docx(paper_docx, paper, scheme=False),
        "scheme_docx": _validate_docx(scheme_docx, paper, scheme=True),
        "paper_pdf": {},
        "scheme_pdf": {},
    }
    if export:
        paper_pdf = paper_docx.with_suffix(".pdf")
        scheme_pdf = scheme_docx.with_suffix(".pdf")
        pages = export_pdf(paper_docx, paper_pdf)
        _cover_page_count(paper_docx, pages)
        pages = export_pdf(paper_docx, paper_pdf)
        qa["paper_pdf"] = _validate_pdf(paper_pdf, scheme=False)
        qa["paper_pdf"]["pages"] = pages
        scheme_pages = export_pdf(scheme_docx, scheme_pdf)
        _scheme_page_count(scheme_docx, scheme_pages)
        scheme_pages = export_pdf(scheme_docx, scheme_pdf)
        qa["scheme_pdf"] = _validate_pdf(scheme_pdf, scheme=True)
        qa["scheme_pdf"]["pages"] = scheme_pages
        qa["files"] = {
            "paper_docx": str(paper_docx),
            "paper_pdf": str(paper_pdf),
            "scheme_docx": str(scheme_docx),
            "scheme_pdf": str(scheme_pdf),
        }
    else:
        qa["files"] = {
            "paper_docx": str(paper_docx),
            "paper_pdf": "",
            "scheme_docx": str(scheme_docx),
            "scheme_pdf": "",
        }
    qa["problems"] = (
        qa["paper_docx"].get("problems", []) +
        qa["scheme_docx"].get("problems", []) +
        qa["paper_pdf"].get("problems", []) +
        qa["scheme_pdf"].get("problems", []))
    (out / "qa.json").write_text(json.dumps(qa, indent=2), encoding="utf-8")
    if qa["problems"]:
        raise RuntimeError(
            f"CSC413 seed {seed} validation failed: "
            + "; ".join(qa["problems"][:5]))
    created = time.time()
    progress = []
    for question in paper["questions"]:
        if question["part"] == "D":
            for part in question["parts"]:
                progress.append({
                    "question": question["number"],
                    "slot": f"{question['number']}{part['label']}",
                    "status": "accepted",
                    "message": question["topic"],
                    "cost_usd": 0, "calls": 0,
                    "accepted": 1, "placeholders": 0,
                })
        else:
            progress.append({
                "question": question["number"],
                "slot": question["number"],
                "status": "accepted",
                "message": question["topic"],
                "cost_usd": 0, "calls": 0,
                "accepted": 1, "placeholders": 0,
            })
    meta = {
        "subject": SUBJECT,
        "seed": seed,
        "mode": "realistic",
        "computed_marks": None,
        "model": "csc413-deterministic",
        "cost_usd": 0.0,
        "accepted": len(progress),
        "placeholders": 0,
        "total_slots": len(progress),
        "total_marks": paper["total_marks"],
        "question_count": paper["question_count"],
        "has_practice_mode": False,
        "has_placeholders": False,
        "created": created,
        "year": utc_year(created),
        "topic_marks": plan["topic_marks"],
        "files": qa["files"],
        "summary": {
            "subject": SUBJECT,
            "seed": seed,
            "mode": "realistic",
            "accepted": len(progress),
            "placeholders": 0,
            "total_slots": len(progress),
            "total_marks": paper["total_marks"],
            "question_count": paper["question_count"],
            "has_practice_mode": False,
            "has_placeholders": False,
            "model": "csc413-deterministic",
            "cost_usd": 0.0,
            "cached": True,
            "topic_marks": plan["topic_marks"],
            "pdf_available": bool(export),
        },
        "progress": progress,
        "validation": qa,
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return {**qa, "seed": seed, "cached": False, "path": str(out),
            "pdf": bool(export), "scheme_pdf_available": bool(export),
            "accepted": len(progress), "total_marks": paper["total_marks"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--no-pdf", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    qa = build_seed(args.seed, Path(args.out), export=not args.no_pdf,
                    force=args.force)
    print(json.dumps({
        "seed": qa["seed"],
        "files": qa["files"],
        "paper_docx_problems": qa["paper_docx"]["problems"],
        "scheme_docx_problems": qa["scheme_docx"]["problems"],
        "paper_pdf_problems": qa["paper_pdf"].get("problems", []),
        "scheme_pdf_problems": qa["scheme_pdf"].get("problems", []),
        "problems": qa["problems"],
    }, indent=2))
    if qa["problems"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
