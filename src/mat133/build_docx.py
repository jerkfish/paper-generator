"""Build MAT133 question papers and marking schemes.

The builder starts from the cleaned ``MAT133 TEMPLATE.docx`` cover, adds a
fresh body and never reads or clones any CSC662 sample question block.  It
accepts :class:`~src.mat133.models.Mat133Paper` and writes a DOCX plus, when
Word is available, a PDF.

Body layout:
  cover (template) -> page break -> QUESTION 1..N -> APPENDIX 1 (paper only)
  cover (relabelled) -> page break -> worked marking scheme
"""
from __future__ import annotations

import re
import subprocess
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import docx
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor
from pypdf import PdfReader

from src.config import subject_reference_dir
from src.mat133.models import DEFAULT_APPENDIX, Mat133Paper
from src.render.mathfig import formula_png

TEMPLATE = (subject_reference_dir("MAT133") / "MAT133 TEMPLATE.docx")
FORBIDDEN_TOKENS = (
    "CSC662", "COMPUTER SECURITY", "THEORY SLOT", "CIPHER",
    "Vigen", "ACM", "PART A (80 MARKS)", "PART B (20 MARKS)",
)
MONTHS = {
    "JAN": "JANUARY", "FEB": "FEBRUARY", "MAR": "MARCH", "APR": "APRIL",
    "MAY": "MAY", "JUN": "JUNE", "JUL": "JULY", "AUG": "AUGUST",
    "SEP": "SEPTEMBER", "OCT": "OCTOBER", "NOV": "NOVEMBER",
    "DEC": "DECEMBER",
}


def _el(p):
    return getattr(p, "_p", p)


def _set_text(p, text: str) -> None:
    """Replace a paragraph's text, preserving its first run's formatting."""
    p = _el(p)
    runs = p.findall(qn("w:r"))
    if not runs:
        r = docx.oxml.OxmlElement("w:r")
        p.append(r)
        runs = [r]
    for r in runs[1:]:
        p.remove(r)
    r0 = runs[0]
    for t in list(r0.findall(qn("w:t")))[1:]:
        r0.remove(t)
    t_el = r0.find(qn("w:t"))
    if t_el is None:
        t_el = docx.oxml.OxmlElement("w:t")
        r0.append(t_el)
    parts = str(text).split("\n")
    t_el.text = parts[0]
    t_el.set(qn("xml:space"), "preserve")
    for extra in parts[1:]:
        r0.append(docx.oxml.OxmlElement("w:br"))
        t2 = docx.oxml.OxmlElement("w:t")
        t2.text = extra
        t2.set(qn("xml:space"), "preserve")
        r0.append(t2)


def _para_text(p) -> str:
    p = _el(p)
    return "".join(t.text or "" for t in p.findall(".//" + qn("w:t")))


def _replace_runs(p, old: str, new: str) -> bool:
    p = _el(p)
    done = False
    for t in p.findall(".//" + qn("w:t")):
        if old in (t.text or ""):
            t.text = t.text.replace(old, new)
            done = True
    return done


def _para(doc, text: str = "", *, bold: bool = False, italic: bool = False,
          size: float = 10.5, align=None, before: float = 0,
          after: float = 0, indent: float = 0, hanging: float = 0,
          keep: bool = False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = 1.05
    if align is not None:
        p.alignment = align
    if indent:
        pf.left_indent = Inches(indent)
    if hanging:
        pf.first_line_indent = Inches(-hanging)
    if keep:
        pf.keep_with_next = True
    if text:
        r = p.add_run(text)
        r.bold = bold
        r.italic = italic
        r.font.name = "Arial"
        r.font.size = Pt(size)
    return p


def _run(p, text: str, *, bold: bool = False, italic: bool = False,
         size: float = 10.5) -> None:
    r = p.add_run(text)
    r.bold = bold
    r.italic = italic
    r.font.name = "Arial"
    r.font.size = Pt(size)


def _month_full(month: str) -> str:
    key = str(month).strip().upper()
    return MONTHS.get(key[:3], key)


def _month_short(month: str) -> str:
    key = str(month).strip().upper()
    return key[:3]


def patch_cover(doc, paper: Mat133Paper, *, scheme: bool = False) -> None:
    """Patch the template cover for this paper/scheme."""
    month = _month_full(paper.month)
    mshort = _month_short(paper.month)
    year = str(paper.year)

    for p in doc.paragraphs:
        text = _para_text(p)
        if "CS/FEB" in text and "MAT133" in text:
            _replace_runs(p, "FEB", mshort)
            _replace_runs(p, "2026", year)
        if scheme and text.strip() == "UNIVERSITI TEKNOLOGI MARA FINAL EXAMINATION":
            _set_text(p._p, "UNIVERSITI TEKNOLOGI MARA\nMARKING SCHEME")
        elif scheme and text.strip().startswith("This question paper consists of"):
            _set_text(p._p,
                      f"This marking scheme accompanies the MAT133 mock paper "
                      f"({month.title()} {year}).")
        elif scheme and text.strip().startswith("Answer ALL questions in the"):
            _set_text(p._p, "Answers and marking points are for local study use only.")
        elif scheme and text.strip() == "INSTRUCTIONS TO CANDIDATES":
            _set_text(p._p, "INSTRUCTIONS TO MARKERS")
            for el in list(p._p.findall(".//" + qn("w:spacing"))):
                if el.getparent() is not None and el.getparent().tag == qn("w:rPr"):
                    el.getparent().remove(el)
            for el in list(p._p.findall(".//" + qn("w:w"))):
                if el.getparent() is not None:
                    el.getparent().remove(el)
        elif scheme and text.strip() == "DO NOT TURN THIS PAGE UNTIL YOU ARE TOLD TO DO SO":
            _set_text(p._p, "FOR MARKERS' USE ONLY")
        elif scheme and text.strip().startswith("This examination paper consists of"):
            _set_text(p._p, "This marking scheme consists of N printed pages")
        elif not scheme and text.strip().startswith("This question paper consists of"):
            _set_text(p._p, f"This question paper consists of "
                            f"{len(paper.questions)} questions.")

    if scheme:
        # Keep the scheme cover to the two marker notes only; the template's
        # candidate instructions do not belong on a marking scheme.
        start = next((i for i, p in enumerate(doc.paragraphs)
                      if _para_text(p._p).startswith(
                          "This marking scheme accompanies")), None)
        end = next((i for i, p in enumerate(doc.paragraphs)
                    if _para_text(p._p).strip() == "FOR MARKERS' USE ONLY"), None)
        if start is not None and end is not None and start < end:
            for p in list(doc.paragraphs[start + 1:end]):
                text = _para_text(p._p).strip()
                if text.startswith("Answers and marking points"):
                    continue
                # Remove the candidate-instruction paragraphs outright so
                # Word's automatic 3./4./5. numbering disappears too.
                if text or p._p.find(".//" + qn("w:numPr")) is not None:
                    parent = p._p.getparent()
                    if parent is not None:
                        parent.remove(p._p)

    # Course box values are separate runs: PRE | CALCULUS, MAT133 | FEBRUARI |
    # 2026, 2 | HOURS.
    for box in doc.element.body.iter(qn("w:txbxContent")):
        for p in box.findall(qn("w:p")):
            for t in p.findall(".//" + qn("w:t")):
                value = t.text or ""
                if value == "FEBRUARI":
                    t.text = month
                elif value == "2026":
                    t.text = year
                elif value == "2" and paper.duration.upper().startswith("2"):
                    t.text = "2"
                elif value == "3" and paper.duration.upper().startswith("3"):
                    t.text = "3"


def _body_section(doc, paper: Mat133Paper):
    section = doc.sections[-1]
    section.start_type = WD_SECTION.NEW_PAGE
    section.different_first_page_header_footer = False
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.footer.is_linked_to_previous = True

    def fill_header(header) -> None:
        header.is_linked_to_previous = False
        hp = header.paragraphs[0]
        hp.text = ""
        hp.paragraph_format.tab_stops.add_tab_stop(
            Inches(6.25), WD_TAB_ALIGNMENT.RIGHT)
        _run(hp, f"CS/{_month_short(paper.month)} {paper.year}/MAT133",
             size=8, bold=True)
        _run(hp, "\tCONFIDENTIAL", size=8, bold=True)

    fill_header(section.header)
    # The template enables evenAndOddHeaders, so even body pages use this.
    fill_header(section.even_page_header)
    return section


def _question_heading(doc, number: int) -> None:
    p = _para(doc, f"QUESTION {number}", bold=True, size=11.5,
              before=14, after=5, keep=True)
    # No rule under QUESTION headings; the template's question blocks do not
    # use one and the user's reviewed group-1 paper removed it.


def _add_figure(doc, path: str, caption: str = "", width_cm: float = 10.0,
                before: float = 4, after: float = 2) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.add_run().add_picture(str(path), width=Cm(width_cm))
    if caption:
        p.paragraph_format.keep_with_next = True
        _para(doc, caption, italic=True, size=8.5,
              align=WD_ALIGN_PARAGRAPH.CENTER, after=2)


def _add_part_paper(doc, part, level: float = 0) -> None:
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Inches(0.28 + level * 0.25)
    pf.first_line_indent = Inches(-0.28)
    pf.space_before = Pt(4)
    pf.space_after = Pt(0)
    pf.line_spacing = 1.05
    pf.keep_with_next = bool(part.diagram or part.formula)
    if part.label:
        label = part.label if part.label.endswith(")") else f"{part.label})"
        _run(p, label, bold=True, size=10.5)
        _run(p, "\t", size=10.5)
    _run(p, part.text, size=10.5)
    marks_p = _para(doc, f"({part.marks:g} marks)", italic=True, size=9.5,
                    align=WD_ALIGN_PARAGRAPH.RIGHT, after=3)
    if part.diagram or part.formula:
        marks_p.paragraph_format.keep_with_next = True
    if part.formula:
        _add_figure(doc, part.formula.path, part.formula.caption,
                    part.formula.width_cm, before=2, after=2)
    if part.diagram:
        _add_figure(doc, part.diagram.path, part.diagram.caption,
                    part.diagram.width_cm, before=3, after=3)


def _add_question_paper(doc, q) -> None:
    _question_heading(doc, q.number)
    if q.stem:
        _para(doc, q.stem, size=10.5, after=3)
    for part in q.parts:
        level = 1 if re.match(r"^[ivx]+$", part.label or "") else 0
        _add_part_paper(doc, part, level=level)


def _add_appendix(doc, paper: Mat133Paper) -> None:
    if not paper.with_appendix:
        return
    doc.add_page_break()
    _para(doc, "APPENDIX 1", bold=True, size=13,
          align=WD_ALIGN_PARAGRAPH.CENTER, before=0, after=3)
    _para(doc, "Formula sheet (as supplied with the paper).",
          italic=True, size=8.5, align=WD_ALIGN_PARAGRAPH.CENTER, after=8)
    lines = paper.appendix or DEFAULT_APPENDIX
    rows = (len(lines) + 1) // 2
    table = doc.add_table(rows=rows, cols=2)
    table.autofit = True
    for i, line in enumerate(lines):
        cell = table.cell(i % rows, i // rows)
        cell.text = ""
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(2)
        _run(p, line, size=9.5)


def build_paper_docx(paper: Mat133Paper, out_docx: Path,
                     template: Path = TEMPLATE) -> Path:
    doc = docx.Document(str(template))
    patch_cover(doc, paper, scheme=False)
    _body_section(doc, paper)
    for q in paper.questions:
        _add_question_paper(doc, q)
    _para(doc, "END OF QUESTION PAPER", italic=True, size=9,
          align=WD_ALIGN_PARAGRAPH.CENTER, before=14, after=4)
    _add_appendix(doc, paper)
    out_docx.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_docx))
    return out_docx


def _latex_image(latex: str, latex_dir: Path, index: int,
                 max_cm: float = 4.2) -> tuple[Path, float]:
    path = formula_png(latex, latex_dir / f"formula_{index:04d}.png",
                       fontsize=13, dpi=300)
    from PIL import Image
    with Image.open(path) as image:
        pixels_w, _ = image.size
    width_cm = min(max_cm, max(2.0, pixels_w / 300 * 2.54 * 1.15))
    return path, width_cm


def _add_latex_run(p, latex: str, latex_dir: Path, index: int,
                   max_cm: float = 4.2) -> None:
    path, width_cm = _latex_image(latex, latex_dir, index, max_cm)
    p.add_run().add_picture(str(path), width=Cm(width_cm))


def _scheme_lines(part) -> tuple[list[str], list[str]]:
    """Return mathematical working lines and aligned marking codes.

    Explanatory ``solution_steps`` are deliberately not used.  The working
    list is the generator's mathematical path; ``answer_latex`` is only a
    fallback when no working list exists.  Marking codes are taken from
    ``solution_marks`` when supplied;
    otherwise the codes in ``marking_notes`` are aligned from the final answer
    backwards (A1/B1 on results, M1 on method lines).
    """
    lines = list(part.solution_latex)
    if not lines and part.answer_latex:
        lines = [part.answer_latex]
    if part.solution_marks and len(part.solution_marks) == len(lines):
        return lines, list(part.solution_marks)
    codes = []
    for note in part.marking_notes:
        match = re.match(r"^\s*([MAB]\d+)\b", note)
        if match:
            codes.append(match.group(1))
    marks = [""] * len(lines)
    if codes and lines:
        if len(codes) >= len(lines):
            lead = " ".join(codes[:len(codes) - len(lines) + 1])
            marks[0] = lead
            marks[1:] = codes[len(codes) - len(lines) + 1:]
        else:
            marks[:len(codes) - 1] = codes[:-1]
            marks[-1] = codes[-1]
    return lines, marks


def _set_table_grid(table) -> None:
    tblPr = table._tbl.tblPr
    for old in tblPr.findall(qn("w:tblBorders")):
        tblPr.remove(old)
    borders = docx.oxml.OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = docx.oxml.OxmlElement(f"w:{side}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "6")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "808080")
        borders.append(el)
    tblPr.append(borders)


def _repeat_header(row) -> None:
    trPr = row._tr.get_or_add_trPr()
    header = docx.oxml.OxmlElement("w:tblHeader")
    header.set(qn("w:val"), "true")
    trPr.append(header)


def _add_scheme_row(doc, table, q, part, latex_dir: Path,
                    counter: list[int]) -> None:
    row = table.add_row()
    trPr = row._tr.get_or_add_trPr()
    cant = docx.oxml.OxmlElement("w:cantSplit")
    trPr.append(cant)
    no_cell, solution_cell, mark_cell = row.cells
    label = part.label or ""
    no_text = f"{q.number} {label})" if label else f"{q.number}"
    no_p = no_cell.paragraphs[0]
    no_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _run(no_p, no_text, bold=True, size=10)

    lines, codes = _scheme_lines(part)
    solution_cell.text = ""
    if lines:
        inner = solution_cell.add_table(rows=0, cols=2)
        inner.autofit = False
        for line, code in zip(lines, codes):
            r = inner.add_row()
            fp, cp = r.cells[0].paragraphs[0], r.cells[1].paragraphs[0]
            fp.paragraph_format.space_before = Pt(0)
            fp.paragraph_format.space_after = Pt(1)
            counter[0] += 1
            _add_latex_run(fp, line, latex_dir, counter[0], max_cm=9.4)
            cp.alignment = WD_ALIGN_PARAGRAPH.LEFT
            cp.paragraph_format.space_before = Pt(0)
            cp.paragraph_format.space_after = Pt(1)
            if code:
                _run(cp, code, bold=True, size=9)
                cp.runs[0].font.color.rgb = RGBColor(0xC0, 0, 0)
        # nested table widths: formula + code columns
        for r in inner.rows:
            r.cells[0].width = Inches(4.0)
            r.cells[1].width = Inches(0.8)
    if part.diagram:
        p = solution_cell.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(2)
        p.add_run().add_picture(str(part.diagram.path), width=Cm(6.5))

    mark_p = mark_cell.paragraphs[0]
    mark_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _run(mark_p, f"{part.marks:g} m", bold=True, size=10)


def build_scheme_docx(paper: Mat133Paper, out_docx: Path,
                      template: Path = TEMPLATE) -> Path:
    doc = docx.Document(str(template))
    patch_cover(doc, paper, scheme=True)
    _body_section(doc, paper)
    table = doc.add_table(rows=1, cols=3)
    table.autofit = False
    table.columns[0].width = Inches(0.8)
    table.columns[1].width = Inches(4.9)
    table.columns[2].width = Inches(0.8)
    _set_table_grid(table)
    headers = ("NO", "SOLUTION", "MARK")
    for cell, text in zip(table.rows[0].cells, headers):
        cell.width = Inches(0.8) if text != "SOLUTION" else Inches(4.9)
        _run(cell.paragraphs[0], text, bold=True, size=10)
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    _repeat_header(table.rows[0])
    with tempfile.TemporaryDirectory(prefix="mat133_latex_") as tmp:
        latex_dir = Path(tmp)
        counter = [0]
        for q in paper.questions:
            for part in q.parts:
                _add_scheme_row(doc, table, q, part, latex_dir, counter)
        out_docx.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(out_docx))
    return out_docx


def _tmp_ps(docx_path: Path, pdf_path: Path) -> Path:
    with tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False,
                                     encoding="utf-8") as fh:
        fh.write(f"""
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$doc = $word.Documents.Open("{docx_path}", $false, $true)
$doc.SaveAs([ref]"{pdf_path}", [ref]17)
$doc.Close([ref]$false)
$word.Quit([ref]$false)
""")
    return Path(fh.name)


def export_pdf(docx_path: Path, pdf_path: Path) -> int:
    """Export to PDF with Word COM (Windows) or LibreOffice (container)."""
    from src.assemble.pdf_export import export_pdf as _export_pdf
    return _export_pdf(docx_path, pdf_path)


def update_page_count(docx_path: Path, pdf_path: Path, *, scheme: bool) -> int:
    pages = export_pdf(docx_path, pdf_path)
    doc = docx.Document(str(docx_path))
    needle = "marking scheme consists of" if scheme else "examination paper consists of"
    for p in doc.paragraphs:
        text = _para_text(p._p)
        if needle in text:
            prefix = ("This marking scheme consists of" if scheme
                      else "This examination paper consists of")
            _set_text(p._p, f"{prefix} {pages} printed pages")
            break
    doc.save(str(docx_path))
    return export_pdf(docx_path, pdf_path)


def validate_docx(docx_path: Path, paper: Mat133Paper, *,
                  scheme: bool = False) -> dict:
    with zipfile.ZipFile(str(docx_path)) as z:
        xml = z.read("word/document.xml").decode("utf-8")
        media = [n for n in z.namelist() if n.startswith("word/media/")]
    ET.fromstring(xml.encode("utf-8"))
    text = "".join(re.findall(r"<w:t\b[^>]*>([^<]*)</w:t>", xml))
    bad = [token for token in FORBIDDEN_TOKENS if token in text]
    headings = len(re.findall(r"QUESTION\s+\d+", text))
    expected_parts = sum(len(q.parts) for q in paper.questions)
    part_labels = [f"{q.number} {p.label})".strip()
                   for q in paper.questions for p in q.parts if p.label]
    found_labels = sum(1 for label in part_labels if label in text)
    return {
        "xml_valid": True,
        "forbidden_tokens": bad,
        "question_headings": headings,
        "expected_questions": len(paper.questions),
        "part_labels_found": found_labels,
        "expected_parts": expected_parts,
        "media": media,
        "has_crest": any("image1" in m for m in media),
        "has_match": "MAT133" in text and _month_short(paper.month) in text,
        "is_scheme": scheme,
    }


def validate_pdf(pdf_path: Path, paper: Mat133Paper, *,
                 scheme: bool = False) -> dict:
    import pymupdf
    doc = pymupdf.open(str(pdf_path))
    pages = []
    overflow = []
    for index, page in enumerate(doc):
        pages.append(page.get_text())
        width = page.rect.width
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    if span.get("bbox") and span["bbox"][2] > width - 30:
                        overflow.append({
                            "page": index + 1,
                            "text": span.get("text", "")[:60],
                            "x1": round(span["bbox"][2], 1),
                            "width": round(width, 1),
                        })
    doc.close()
    text = "\n".join(pages)
    headings = [f"QUESTION {q.number}" for q in paper.questions]
    part_labels = [f"{q.number} {p.label})".strip()
                   for q in paper.questions for p in q.parts if p.label]
    if scheme:
        body_start = len(pages) > 1 and "SOLUTION" in pages[1]
        headings_found = all(label in text for label in part_labels)
        full_marks = all(f"{part.marks:g} m" in text
                         for q in paper.questions for part in q.parts)
    else:
        body_start = len(pages) > 1 and "QUESTION 1" in pages[1]
        headings_found = all(h in text for h in headings)
        full_marks = all(f"({part.marks:g} marks)" in text
                         for q in paper.questions for part in q.parts)
    return {
        "pages": len(pages),
        "page1_has_cover": "UNIVERSITI TEKNOLOGI MARA" in pages[0],
        "page1_has_mat133": "MAT133" in pages[0],
        "body_starts_on_page2": body_start,
        "headings_found": headings_found,
        "scheme_heading": (not scheme) or "MARKING SCHEME" in text,
        "full_marks": full_marks,
        "forbidden_tokens": [t for t in FORBIDDEN_TOKENS if t in text],
        "right_overflow": overflow[:10],
    }


def build_bundle(paper: Mat133Paper, out_dir: Path, *,
                 stem: str | None = None, export: bool = True) -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = stem or f"MAT133 {_month_full(paper.month)} {paper.year} (mock)"
    paper_docx = out_dir / f"{stem}.docx"
    scheme_docx = out_dir / f"{stem} - Marking Scheme.docx"
    build_paper_docx(paper, paper_docx)
    build_scheme_docx(paper, scheme_docx)
    result = {
        "paper_docx": str(paper_docx),
        "scheme_docx": str(scheme_docx),
        "paper_pdf": "",
        "scheme_pdf": "",
        "paper_docx_check": validate_docx(paper_docx, paper),
        "scheme_docx_check": validate_docx(scheme_docx, paper, scheme=True),
        "paper_pdf_check": {},
        "scheme_pdf_check": {},
    }
    if export:
        paper_pdf = out_dir / f"{stem}.pdf"
        scheme_pdf = out_dir / f"{stem} - Marking Scheme.pdf"
        paper_pages = update_page_count(paper_docx, paper_pdf, scheme=False)
        scheme_pages = update_page_count(scheme_docx, scheme_pdf, scheme=True)
        result["paper_pdf"] = str(paper_pdf)
        result["scheme_pdf"] = str(scheme_pdf)
        result["paper_pdf_check"] = validate_pdf(paper_pdf, paper)
        result["scheme_pdf_check"] = validate_pdf(scheme_pdf, paper, scheme=True)
        result["paper_pages"] = paper_pages
        result["scheme_pages"] = scheme_pages
    return result
