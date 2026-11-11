"""ICT450 Stage-7 paper and marking-scheme builder.

Starts from the approved standard cover and marking-scheme templates (the
non-v2 files), patches the cover tokens to ICT450, appends five questions
with their repurposed past-paper tables/figures, exports PDFs through the
shared exporter, and writes QA/meta records.

    uv run python -m src.subjects.ict450.build_docx --seed 1
    uv run python -m src.app.prebuild_library --seeds 1 --subject ICT450 --force
"""
from __future__ import annotations

import argparse
import html
import json
import re
import tempfile
import time
import zipfile
from pathlib import Path

import docx
import pymupdf
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from lxml import html as lxml_html
from PIL import Image

from src import config
from src.app.filenames import utc_year
from src.assemble.pdf_export import export_pdf
from src.subjects.ict450.assets import copy_assets
from src.subjects.ict450.generators import generate

SUBJECT = "ICT450"
TRACKING = config.TRACKING_DIR / "ict450"
TEMPLATE = config.subject_reference_dir("ICT450") / "ICT450 TEMPLATE.docx"
SCHEME_TEMPLATE = (config.REFERENCE_DIR / "standard" /
                   "UTM_STANDARD_MARKING_SCHEME.docx")
DEFAULT_OUT = TRACKING / "build_sample"
FORBIDDEN = ("CSC662", "MAT133", "TODO", "placeholder", "data/reference")


def _replace_text_nodes(xml: str) -> str:
    replacements = (
        ("CSC662", "ICT450"),
        ("COMPUTER", "DATABASE DESIGN AND"),
        ("SECURITY", "DEVELOPMENT"),
        ("FEBRUARY", "MOCK"),
        ("FEB", "MOCK"),
        ("OCTOBER ", ""),
        ("OCT\xa0", ""),
        ("OCT ", ""),
        ("OCT", ""),
    )
    pattern = re.compile(r"(<w:t\b[^>]*>)(.*?)(</w:t>)", re.S)

    def replace(match):
        text = html.unescape(match.group(2))
        for old, new in replacements:
            text = text.replace(old, new)
        return match.group(1) + html.escape(text, quote=False) + match.group(3)

    return pattern.sub(replace, xml)


def _shrink_cover_course(xml: str) -> str:
    """Fit the ICT450 course name and code into the fixed cover value box.

    The CSC662 cover stores ``COMPUTER SECURITY`` on one line and lets
    ``CSC662 FEBRUARY 2026`` wrap after the code.  ``DATABASE DESIGN AND
    DEVELOPMENT`` is much longer, so the value box is widened and the course
    name is reduced to 7.5 pt.  A hard break after ``ICT450`` restores the
    intended code/date alignment.
    """
    xml = xml.replace("width:2650", "width:3200")

    def shrink(match):
        run = match.group(0)
        if "DATABASE DESIGN AND" in run or ">DEVELOPMENT<" in run:
            run = run.replace('<w:sz w:val="23"/>', '<w:sz w:val="15"/>')
            run = run.replace('<w:szCs w:val="23"/>',
                              '<w:szCs w:val="15"/>')
        return run

    xml = re.sub(r"<w:r\b.*?</w:r>", shrink, xml, flags=re.S)
    code_run = ('<w:r><w:rPr><w:rFonts w:ascii="Arial"/>'
                '<w:color w:val="1C1C1C"/><w:sz w:val="23"/></w:rPr>'
                '<w:t>ICT450</w:t></w:r>')
    if "MARKING SCHEME" not in xml and code_run in xml:
        xml = xml.replace(code_run, code_run + "<w:r><w:br/></w:r>", 1)
    return xml


def _widen_cover_code(xml: str) -> str:
    """Keep the right-hand cover code on one line after the ICT450 patch.

    The cover stores ``CS/FEB 2026/CSC662`` in a 103.5 pt text box anchored
    420.9 pt from the page edge.  ``CS/MOCK 2026/ICT450`` is two characters
    longer, so the box is widened to 122 pt and its left edge moved to keep
    the right edge in the same place.
    """
    xml = xml.replace("margin-left:420.9pt", "margin-left:402.4pt")
    return xml.replace("width:103.5pt", "width:122pt")


def _patched_template(source: Path, target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source) as zin, zipfile.ZipFile(
            target, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.startswith("word/") and item.filename.endswith(
                    ".xml"):
                text = data.decode("utf-8", errors="replace")
                text = _replace_text_nodes(text)
                if item.filename == "word/document.xml":
                    text = _shrink_cover_course(text)
                if re.match(r"word/header\d*\.xml$", item.filename):
                    text = _widen_cover_code(text)
                data = text.encode("utf-8")
            zout.writestr(item, data)
    return target


def _docx_text(path: Path) -> str:
    parts = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if (name == "word/document.xml"
                    or name.startswith("word/header")
                    or name.startswith("word/footer")) and name.endswith(".xml"):
                xml = archive.read(name).decode("utf-8", errors="replace")
                parts.extend(re.findall(r"<w:t\b[^>]*>(.*?)</w:t>", xml, re.S))
    return " ".join(html.unescape(part) for part in parts)


def _run(paragraph, text: str, *, size: float = 11, bold: bool = False,
         italic: bool = False, mono: bool = False) -> None:
    run = paragraph.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.name = "Courier New" if mono else "Arial"
    run.font.size = Pt(size)


def _para(doc, text: str = "", *, size: float = 11, bold: bool = False,
          italic: bool = False, align=None, before: float = 0,
          after: float = 4, keep: bool = False, mono: bool = False):
    paragraph = doc.add_paragraph()
    if align is not None:
        paragraph.alignment = align
    pf = paragraph.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.keep_with_next = keep
    if text:
        _run(paragraph, text, size=size, bold=bold, italic=italic, mono=mono)
    return paragraph


def _marks(doc, marks: int) -> None:
    _para(doc, f"({marks} mark{'s' if marks != 1 else ''})", size=10.5,
          align=WD_ALIGN_PARAGRAPH.RIGHT, after=10)


def _page_field(paragraph) -> None:
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = " PAGE "
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(begin)
    run._r.append(instruction)
    run._r.append(end)


def _running_header_footer(section, right_text: str) -> None:
    section.different_first_page_header_footer = True
    header = section.header
    header.is_linked_to_previous = False
    paragraph = header.paragraphs[0]
    paragraph.text = ""
    paragraph.paragraph_format.tab_stops.add_tab_stop(
        Inches(3.25), WD_TAB_ALIGNMENT.CENTER)
    paragraph.paragraph_format.tab_stops.add_tab_stop(
        Inches(6.5), WD_TAB_ALIGNMENT.RIGHT)
    _run(paragraph, "CONFIDENTIAL", size=9)
    paragraph.add_run("\t")
    _page_field(paragraph)
    paragraph.add_run("\t")
    _run(paragraph, right_text, size=9)

    footer = section.footer
    footer.is_linked_to_previous = False
    paragraph = footer.paragraphs[0]
    paragraph.text = ""
    paragraph.paragraph_format.tab_stops.add_tab_stop(
        Inches(6.5), WD_TAB_ALIGNMENT.RIGHT)
    _run(paragraph, "© Hak Cipta Universiti Teknologi MARA", size=8)
    paragraph.add_run("\t")
    _run(paragraph, "CONFIDENTIAL", size=8)


def _question_heading(doc, number: str, *, before: float = 18) -> None:
    _para(doc, f"QUESTION {number}", size=12, bold=True,
          before=before, after=6, keep=True)


def _set_paragraph_text(paragraph, text: str) -> None:
    for run in paragraph.runs:
        run.text = ""
    if paragraph.runs:
        paragraph.runs[0].text = text
    else:
        paragraph.add_run(text)


def _fix_cover_header(doc) -> None:
    """Replace the cover's fitted-space header with a right tab.

    The template pads ``CONFIDENTIAL`` and the course code with a long run
    of spaces.  The ICT450 code is slightly longer than CSC662, so that
    paragraph wraps.  A right tab keeps both parts on one line.
    """
    for paragraph in doc.paragraphs:
        text = paragraph.text
        if text.startswith("CONFIDENTIAL") and "CS/MOCK" in text:
            logo = None
            for run in list(paragraph.runs):
                if run._r.xpath(".//w:drawing") or run._r.xpath(".//w:pict"):
                    logo = run
                    continue
                run._r.getparent().remove(run._r)
            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
            pf = paragraph.paragraph_format
            pf.tab_stops.clear_all()
            pf.tab_stops.add_tab_stop(Inches(2.835),
                                      WD_TAB_ALIGNMENT.LEFT)
            pf.tab_stops.add_tab_stop(Inches(6.5), WD_TAB_ALIGNMENT.RIGHT)
            left = paragraph.add_run("CONFIDENTIAL")
            left.font.name = "Arial"
            left.font.size = Pt(10)
            tab_left = paragraph.add_run()
            tab_left._r.append(OxmlElement("w:tab"))
            tab_right = paragraph.add_run()
            tab_right._r.append(OxmlElement("w:tab"))
            code = paragraph.add_run("CS/MOCK 2026/ICT450")
            code.font.name = "Arial"
            code.font.size = Pt(10)
            if logo is not None:
                logo._r.addprevious(left._r)
                logo._r.addprevious(tab_left._r)
            break


def _fix_cover_instructions(doc) -> None:
    remove = []
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text.startswith("This question paper consists of two (2) parts"):
            _set_paragraph_text(
                paragraph,
                "This question paper consists of five (5) questions.")
        elif text in {"PART A (10 Questions)", "PART B (2 Questions)"}:
            remove.append(paragraph)
    for paragraph in remove:
        paragraph._element.getparent().remove(paragraph._element)


def _strip_after(doc, marker: str, *, exact: bool = False,
                 include_marker: bool = False) -> None:
    """Drop the template's old paper/scheme body, keeping the cover."""
    marker_paragraph = None
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if (text == marker) if exact else (marker in text):
            marker_paragraph = paragraph._p
            break
    if marker_paragraph is None:
        return
    body = doc.element.body
    started = False
    for child in list(body):
        if child is marker_paragraph:
            started = True
            if include_marker:
                body.remove(child)
            continue
        if started and child.tag != qn("w:sectPr"):
            body.remove(child)


def _update_cover_pages(docx_path: Path, pages: int) -> None:
    document = docx.Document(str(docx_path))
    containers = [document.paragraphs]
    for section in document.sections:
        containers.extend([
            section.first_page_footer.paragraphs,
            section.footer.paragraphs,
        ])
    changed = False
    for paragraphs in containers:
        for paragraph in paragraphs:
            if paragraph.text.strip().startswith(
                    "This examination paper consists of"):
                _set_paragraph_text(
                    paragraph,
                    f"This examination paper consists of {pages} printed pages.")
                changed = True
                break
        if changed:
            break
    if changed:
        document.save(str(docx_path))


def _update_scheme_pages(docx_path: Path, pages: int) -> None:
    document = docx.Document(str(docx_path))
    changed = False
    for paragraph in document.paragraphs:
        if paragraph.text.strip().startswith(
                "This marking scheme consists of"):
            _set_paragraph_text(
                paragraph,
                f"This marking scheme consists of {pages} printed pages")
            changed = True
            break
    if changed:
        document.save(str(docx_path))


def _picture_size(path: Path, max_width: float, max_height: float) -> tuple:
    with Image.open(path) as image:
        width, height = image.size
    aspect = width / height if height else 1.0
    draw_width = max_width
    draw_height = draw_width / aspect
    if draw_height > max_height:
        draw_height = max_height
        draw_width = draw_height * aspect
    return draw_width, draw_height


def _table_specs(table_html: str) -> tuple[list[tuple], int, int]:
    """Turn MinerU table HTML into (row, col, rowspan, colspan, text) cells."""
    root = lxml_html.fromstring(table_html)
    rows = root.xpath(".//tr")
    specs: list[tuple] = []
    occupied: set[tuple[int, int]] = set()
    ncols = 0
    for row_index, row in enumerate(rows):
        col = 0
        for cell in row.xpath("./td|./th"):
            while (row_index, col) in occupied:
                col += 1
            colspan = max(1, int(cell.get("colspan") or 1))
            rowspan = max(1, int(cell.get("rowspan") or 1))
            text = " ".join("".join(cell.itertext()).split())
            specs.append((row_index, col, rowspan, colspan, text))
            for dr in range(rowspan):
                for dc in range(colspan):
                    occupied.add((row_index + dr, col + dc))
            ncols = max(ncols, col + colspan)
            col += colspan
    nrows = max([len(rows)] + [r + 1 for r, _ in occupied])
    return specs, nrows, ncols


def _set_table_borders(table) -> None:
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "4")
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), "000000")
        borders.append(element)
    table._tbl.tblPr.append(borders)


def _add_html_table(doc, asset: dict) -> None:
    """Render the table content MinerU extracted, not its screenshot."""
    specs, nrows, ncols = _table_specs(asset["table_html"])
    if not specs or ncols <= 0:
        return
    table = doc.add_table(rows=nrows, cols=ncols)
    _set_table_borders(table)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    size = 8.0 if ncols >= 5 else 9.0
    headers = {"student id", "student_ic", "course_id", "course code",
               "customer no", "item", "staff id"}
    for row_index, col, rowspan, colspan, text in specs:
        cell = table.cell(row_index, col)
        if rowspan > 1 or colspan > 1:
            cell = cell.merge(
                table.cell(row_index + rowspan - 1, col + colspan - 1))
        cell.text = ""
        paragraph = cell.paragraphs[0]
        paragraph.paragraph_format.space_before = Pt(1)
        paragraph.paragraph_format.space_after = Pt(1)
        if text:
            run = paragraph.add_run(text)
            run.font.name = "Arial"
            run.font.size = Pt(size)
            first = text.strip().lower()
            if row_index == 0 or first in headers:
                run.bold = True
        paragraph.paragraph_format.keep_with_next = True
    for row in table.rows:
        trpr = row._tr.get_or_add_trPr()
        trpr.append(OxmlElement("w:cantSplit"))


def _add_assets(doc, assets: list[dict], *, max_width: float = 5.6,
                max_height: float = 3.4) -> None:
    for asset in assets:
        caption = asset.get("caption") or asset.get("label") or "Figure"
        _para(doc, caption, size=10, bold=True,
              align=WD_ALIGN_PARAGRAPH.CENTER, before=8, after=3, keep=True)
        if asset.get("table_html"):
            _add_html_table(doc, asset)
            continue
        path = Path(asset.get("img_path") or "")
        if not path.is_file():
            continue
        width, height = _picture_size(path, max_width, max_height)
        paragraph = doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.space_before = Pt(0)
        paragraph.paragraph_format.space_after = Pt(2)
        paragraph.paragraph_format.keep_with_next = True
        paragraph.add_run().add_picture(str(path), width=Inches(width),
                                        height=Inches(height))


def _subpart_paragraph(doc, subpart: dict, level: int):
    paragraph = doc.add_paragraph()
    pf = paragraph.paragraph_format
    pf.space_before = Pt(10 if level == 0 else 4)
    pf.space_after = Pt(0)
    pf.left_indent = Inches(0.35 if level == 0 else 0.95)
    pf.first_line_indent = Inches(-0.35)
    pf.keep_together = True
    pf.keep_with_next = True
    _run(paragraph, f"{subpart['part']}) ", size=11)
    _run(paragraph, subpart["text"], size=11)
    return paragraph


def _render_subparts(doc, question: dict, subparts: list[dict],
                     *, level: int = 0) -> None:
    for subpart in subparts:
        _subpart_paragraph(doc, subpart, level)
        if subpart.get("asset"):
            _add_assets(doc, question.get("assets", []))
        if subpart.get("children"):
            _render_subparts(doc, question, subpart["children"],
                             level=level + 1)
        else:
            _marks(doc, subpart["marks"])


def build_paper_docx(paper: dict, out_docx: Path,
                     template: Path = TEMPLATE) -> Path:
    with tempfile.TemporaryDirectory(prefix="ict450_paper_") as tmp:
        patched = _patched_template(template, Path(tmp) / "template.docx")
        doc = docx.Document(str(patched))
    _fix_cover_instructions(doc)
    _fix_cover_header(doc)
    _strip_after(doc, "This examination paper consists of")
    section = doc.sections[-1]
    _running_header_footer(section, "CS/MOCK 2026/ICT450")
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    section.top_margin = Inches(1.25)
    section.bottom_margin = Inches(1)
    section.header_distance = Inches(0.55)
    section.footer_distance = Inches(0.5)
    doc.add_page_break()
    for question in paper["questions"]:
        _question_heading(doc, question["question"])
        _render_subparts(doc, question, question["subparts"])
    _para(doc, "END OF QUESTION PAPER", italic=True, size=9,
          align=WD_ALIGN_PARAGRAPH.CENTER, before=18, after=4)
    out_docx.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_docx))
    return out_docx


def _iter_leaves(subparts: list[dict], prefix: str = ""):
    for subpart in subparts:
        label = f"{prefix}{subpart['part']}"
        if subpart.get("children"):
            yield from _iter_leaves(subpart["children"], label + " ")
        else:
            yield label, subpart


def build_scheme_docx(paper: dict, out_docx: Path,
                      template: Path = SCHEME_TEMPLATE) -> Path:
    with tempfile.TemporaryDirectory(prefix="ict450_scheme_") as tmp:
        patched = _patched_template(template, Path(tmp) / "template.docx")
        doc = docx.Document(str(patched))
    for paragraph in list(doc.paragraphs):
        text = paragraph.text.strip()
        if text.startswith("This marking scheme accompanies"):
            _set_paragraph_text(
                paragraph,
                "This marking scheme accompanies the ICT450 mock paper (2026).")
        elif text.startswith("Part A = 10 x"):
            _set_paragraph_text(
                paragraph, "Five questions x 20 marks = 100 marks.")
        elif any(marker in text for marker in (
                "Computed answers show working",
                "Supported theory marking points",
                "Computed: 0 slot(s)",
                "Near-copy rejection used")):
            paragraph._element.getparent().remove(paragraph._element)
    _strip_after(doc, "This marking scheme consists of")
    for index, section in enumerate(doc.sections):
        _running_header_footer(section, "CS/MOCK 2026/ICT450")
        if index > 0:
            section.different_first_page_header_footer = False
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)
            section.top_margin = Inches(1.25)
            section.bottom_margin = Inches(1)
            section.header_distance = Inches(0.55)
            section.footer_distance = Inches(0.5)
    for index, question in enumerate(paper["questions"]):
        _question_heading(doc, question["question"], before=16)
        _para(doc, question["topic_label"], italic=True, size=9.5, after=4)
        for label, leaf in _iter_leaves(question["subparts"]):
            _para(doc, f"{label}) {leaf['answer']}", size=10, after=2)
            _para(doc, "Marking points: " + "; ".join(leaf["marking_points"]),
                  size=9, italic=True, after=2)
            _marks(doc, leaf["marks"])
        if index < len(paper["questions"]) - 1:
            doc.add_page_break()
    out_docx.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_docx))
    return out_docx


def _validate_docx(path: Path, *, scheme: bool, expected_tables: int = 0,
                   expected_figures: int = 0) -> dict:
    result = {"path": str(path), "exists": path.is_file(),
              "xml_valid": False, "sections": 0, "images": 0, "tables": 0,
              "problems": []}
    if not path.is_file():
        result["problems"].append("DOCX is missing")
        return result
    try:
        document = docx.Document(str(path))
        result["sections"] = len(document.sections)
        result["images"] = len(document.inline_shapes)
        result["tables"] = len(document.tables)
        with zipfile.ZipFile(path) as archive:
            archive.namelist()
        result["xml_valid"] = True
    except Exception as error:
        result["problems"].append(f"cannot open DOCX: {error}")
        return result
    text = _docx_text(path)
    if "ICT450" not in text:
        result["problems"].append("ICT450 token missing")
    if scheme and "MARKING SCHEME" not in text:
        result["problems"].append("marking scheme heading missing")
    if not scheme:
        for number in ("QUESTION 1", "QUESTION 5"):
            if number not in text:
                result["problems"].append(f"{number} heading missing")
        if expected_tables and result["tables"] < expected_tables:
            result["problems"].append(
                f"expected {expected_tables} native tables, "
                f"found {result['tables']}")
        if expected_figures and result["images"] < expected_figures:
            result["problems"].append(
                f"expected {expected_figures} embedded figures, "
                f"found {result['images']}")
        if (expected_tables or expected_figures) and "Table 1" not in text \
                and "Figure 1" not in text:
            result["problems"].append("asset captions missing")
    for token in FORBIDDEN:
        if token in text:
            result["problems"].append(f"forbidden token: {token}")
    return result


def _validate_pdf(path: Path, *, scheme: bool,
                  expected_figures: int = 0) -> dict:
    result = {"path": str(path), "exists": path.is_file(), "pages": 0,
              "images": 0, "problems": []}
    if not path.is_file():
        result["problems"].append("PDF is missing")
        return result
    try:
        with pymupdf.open(str(path)) as document:
            result["pages"] = len(document)
            text = "\n".join(page.get_text() for page in document)
            result["images"] = sum(len(page.get_images())
                                   for page in document)
    except Exception as error:
        result["problems"].append(f"cannot open PDF: {error}")
        return result
    if result["pages"] <= 0:
        result["problems"].append("PDF has no pages")
    if "ICT450" not in text:
        result["problems"].append("ICT450 token missing from PDF")
    if scheme and "MARKING SCHEME" not in text:
        result["problems"].append("marking scheme heading missing from PDF")
    if not scheme and expected_figures and result["images"] < expected_figures:
        result["problems"].append(
            f"expected {expected_figures} PDF figures, "
            f"found {result['images']}")
    return result


def build_seed(seed: int, out_dir: Path | None = None, export: bool = True,
               force: bool = False, **kwargs) -> dict:
    if out_dir is None:
        from src.app.jobs import cache_path
        out_dir = cache_path("realistic", seed, None, subject=SUBJECT)
    out = Path(out_dir)
    meta_path = out / "meta.json"
    if not force and meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            files = [Path(value) for value in
                     (meta.get("files") or {}).values() if value]
            if files and all(path.exists() for path in files):
                qa = json.loads((out / "qa.json").read_text(encoding="utf-8"))
                return {**qa, "seed": seed, "cached": True, "path": str(out),
                        "files": meta.get("files", {}),
                        "problems": qa.get("problems", [])}
        except Exception:
            pass
    out.mkdir(parents=True, exist_ok=True)
    paper = generate(seed)
    for index, question in enumerate(paper["questions"], start=1):
        question["assets"] = copy_assets(
            question.get("assets", []), out, seed, index)
    paper["asset_count"] = sum(
        len(question.get("assets", [])) for question in paper["questions"])
    paper["table_count"] = sum(
        1 for question in paper["questions"]
        for asset in question.get("assets", []) if asset.get("table_html"))
    paper["figure_count"] = paper["asset_count"] - paper["table_count"]
    (out / "paper.json").write_text(
        json.dumps(paper, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    paper_docx = out / f"ICT450 Seed {seed:02d} 2026.docx"
    scheme_docx = out / f"ICT450 Seed {seed:02d} 2026 - Marking Scheme.docx"
    build_paper_docx(paper, paper_docx)
    build_scheme_docx(paper, scheme_docx)
    expected_tables = paper["table_count"]
    expected_figures = paper["figure_count"]
    qa = {
        "subject": SUBJECT,
        "seed": seed,
        "paper_docx": _validate_docx(
            paper_docx, scheme=False, expected_tables=expected_tables,
            expected_figures=expected_figures),
        "scheme_docx": _validate_docx(scheme_docx, scheme=True),
        "paper_pdf": {},
        "scheme_pdf": {},
    }
    files = {
        "paper_docx": str(paper_docx),
        "paper_pdf": "",
        "scheme_docx": str(scheme_docx),
        "scheme_pdf": "",
    }
    if export:
        paper_pdf = paper_docx.with_suffix(".pdf")
        pages = export_pdf(paper_docx, paper_pdf)
        _update_cover_pages(paper_docx, pages)
        pages = export_pdf(paper_docx, paper_pdf)
        qa["paper_pdf"] = _validate_pdf(paper_pdf, scheme=False,
                                        expected_figures=expected_figures)
        qa["paper_pdf"]["pages"] = pages
        scheme_pdf = scheme_docx.with_suffix(".pdf")
        scheme_pages = export_pdf(scheme_docx, scheme_pdf)
        _update_scheme_pages(scheme_docx, scheme_pages)
        scheme_pages = export_pdf(scheme_docx, scheme_pdf)
        qa["scheme_pdf"] = _validate_pdf(scheme_pdf, scheme=True)
        qa["scheme_pdf"]["pages"] = scheme_pages
        files["paper_pdf"] = str(paper_pdf)
        files["scheme_pdf"] = str(scheme_pdf)
    qa["files"] = files
    qa["problems"] = (
        qa["paper_docx"].get("problems", [])
        + qa["scheme_docx"].get("problems", [])
        + qa["paper_pdf"].get("problems", [])
        + qa["scheme_pdf"].get("problems", []))
    (out / "qa.json").write_text(json.dumps(qa, indent=2), encoding="utf-8")
    if qa["problems"]:
        raise RuntimeError(
            f"ICT450 seed {seed} validation failed: "
            + "; ".join(qa["problems"][:5]))
    created = time.time()
    progress = []
    for question in paper["questions"]:
        progress.append({
            "question": question["question"],
            "slot": question["slot"],
            "status": "accepted",
            "message": question["topic_label"],
            "cost_usd": 0,
            "calls": 0,
            "accepted": 1,
            "placeholders": 0,
            "assets": len(question.get("assets", [])),
        })
    meta = {
        "subject": SUBJECT,
        "seed": seed,
        "mode": "realistic",
        "computed_marks": None,
        "model": "deterministic-templates",
        "cost_usd": 0.0,
        "accepted": len(paper["questions"]),
        "placeholders": 0,
        "total_slots": len(paper["questions"]),
        "has_practice_mode": True,
        "has_placeholders": True,
        "created": created,
        "year": utc_year(created),
        "asset_count": paper["asset_count"],
        "table_count": paper["table_count"],
        "figure_count": paper["figure_count"],
        "topic_marks": {
            question["topic"]: question["marks"]
            for question in paper["questions"]
        },
        "files": files,
        "progress": progress,
        "summary": {
            "subject": SUBJECT,
            "seed": seed,
            "total_marks": paper["total_marks"],
            "question_count": paper["question_count"],
            "topics": [question["topic"] for question in paper["questions"]],
            "assets": paper["asset_count"],
            "tables": paper["table_count"],
            "figures": paper["figure_count"],
            "qa_problems": qa["problems"],
        },
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return {**qa, "seed": seed, "cached": False, "path": str(out),
            "files": files, "problems": qa["problems"],
            "pdf": bool(files["paper_pdf"]),
            "scheme_pdf_available": bool(files["scheme_pdf"])}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--out", default="")
    parser.add_argument("--no-export", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    result = build_seed(
        args.seed,
        out_dir=Path(args.out) if args.out else DEFAULT_OUT,
        export=not args.no_export,
        force=args.force,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
