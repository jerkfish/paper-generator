"""V5 MAT133 seed builder: recycled papers and unofficial marking schemes.

Seeds are built only from approved bank questions whose model answer is
usable.  The paper uses the approved MAT133 cover template; the scheme uses
the standard UTM marking-scheme cover required by AGENTS.md.

Run:
    uv run python -m src.subjects.mat133.render_v5 --seeds 1-3
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import tempfile
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

import docx
import pymupdf
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt

from src import config
from src.assemble.pdf_export import export_pdf
from src.assemble.recycle import display_width, rewrite_references
from src.bank.store import load_json, save_json
from src.render.mathfig import formula_png
from src.subjects.mat133.assemble_v2 import (BANK, FORMAT, OUT, TRACKING,
                                             plans_for)

TEMPLATE = config.subject_reference_dir("MAT133") / "MAT133 TEMPLATE.docx"
SCHEME_TEMPLATE = (config.REFERENCE_DIR / "standard" /
                   "UTM_STANDARD_MARKING_SCHEME.docx")
SUBJECT = "MAT133"
MONTH = "NOV"
YEAR = 2026
MONTH_FULL = "NOVEMBER"
DURATION = "2 HOURS"
FORBIDDEN = ("CSC662", "COMPUTER SECURITY", "MAT133-20", "TODO",
             "placeholder", "data/reference")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# --------------------------------------------------------------------------
# math and rich text
# --------------------------------------------------------------------------

MATH_RE = re.compile(
    r"\$\$(.+?)\$\$|\$([^$]+?)\$|\\\((.+?)\\\)|\\\[(.+?)\\\]", re.S)
PROSE_RE = re.compile(
    r"\b(the|and|so|then|thus|need|denominator|cannot|where|with|for|"
    r"is|are|or|hence|since|if|let|from|gives|remainder|quotient|vertex|"
    r"center|centre|radius|sketch|domain|intercepts|answer|mark|marks)\b",
    re.I)
LATEX_ALIASES = {
    r"\dfrac": r"\frac", r"\tfrac": r"\frac",
    r"\leq": r"\leq", r"\ge": r"\geq", r"\le": r"\le",
    r"\Rightarrow": r"\rightarrow", r"\Longrightarrow": r"\rightarrow",
}


def _plain_math(latex: str) -> str:
    value = str(latex or "")
    symbols = {
        r"\ne": "≠", r"\neq": "≠", r"\le": "≤", r"\leq": "≤",
        r"\ge": "≥", r"\geq": "≥", r"\Rightarrow": "⇒",
        r"\rightarrow": "→", r"\times": "×", r"\cdot": "·",
        r"\pi": "π", r"\theta": "θ", r"\alpha": "α", r"\beta": "β",
        r"\circ": "°", r"\pm": "±", r"\infty": "∞", r"\sqrt": "√",
    }
    for old, new in symbols.items():
        value = re.sub(re.escape(old) + r"(?![A-Za-z])", new, value)
    value = re.sub(
        r"\\(?:d|t)?frac\{([^{}]*)\}\{([^{}]*)\}",
        lambda match: f"({match.group(1)})/({match.group(2)})", value)
    value = re.sub(
        r"\\sqrt\{([^{}]*)\}",
        lambda match: "√(" + match.group(1) + ")", value)
    value = re.sub(r"\\(mathrm|text|operatorname)\{([^{}]*)\}", r"\2", value)
    value = value.replace("\\left", "").replace("\\right", "")
    value = value.replace("\\,", " ").replace("\\;", " ")
    value = value.replace("\\!", "")
    value = re.sub(r"\\[a-zA-Z]+", "", value)
    value = value.replace("{", "").replace("}", "")
    return value.strip()


def _sanitise_latex(latex: str) -> str:
    value = str(latex or "").strip()
    value = value.replace(r"\begin{array}", "").replace(r"\end{array}", "")
    value = value.replace(r"\begin{cases}", "").replace(r"\end{cases}", "")
    value = value.replace("\\\\", "; ").replace("&", " ")
    value = re.sub(r"\\tag\{[^{}]*\}", "", value)
    value = re.sub(r"\\text\{([^{}]*)\}",
                   lambda match: "\\mathrm{" + match.group(1) + "}", value)
    value = re.sub(r"\\big+", lambda _match: "", value)
    value = re.sub(r"\\Big+", lambda _match: "", value)
    value = re.sub(r"\\overline\s+([A-Za-z])",
                   lambda match: "\\overline{" + match.group(1) + "}", value)
    value = re.sub(r"\\bar\s+([A-Za-z])",
                   lambda match: "\\bar{" + match.group(1) + "}", value)
    value = value.replace(r"\dfrac", r"\frac").replace(r"\tfrac", r"\frac")
    value = re.sub(r"\\frac(\d)(\d)",
                   lambda match: "\\frac{" + match.group(1) + "}{"
                   + match.group(2) + "}", value)
    value = re.sub(r"\\frac(\d)\{([^{}]*)\}",
                   lambda match: "\\frac{" + match.group(1) + "}{"
                   + match.group(2) + "}", value)
    value = re.sub(r"\\frac(\d)([A-Za-z])",
                   lambda match: "\\frac{" + match.group(1) + "}{"
                   + match.group(2) + "}", value)
    value = re.sub(r"\\frac\\([A-Za-z]+)(\d)",
                   lambda match: "\\frac{\\" + match.group(1) + "}{"
                   + match.group(2) + "}", value)
    value = re.sub(r"\\sqrt(\d)",
                   lambda match: "\\sqrt{" + match.group(1) + "}", value)
    value = re.sub(r"\\sqrt\s+([A-Za-z])",
                   lambda match: "\\sqrt{" + match.group(1) + "}", value)
    value = re.sub(r"\\le(?![A-Za-z])", lambda _match: "\\leq", value)
    value = re.sub(r"\\ge(?![A-Za-z])", lambda _match: "\\geq", value)
    value = value.replace(r"\iff", r"\Leftrightarrow")
    value = value.replace(r"\Longleftrightarrow", r"\Leftrightarrow")
    value = value.replace(r"\implies", r"\rightarrow")
    value = value.replace(r"\therefore", r"\rightarrow")
    value = value.replace(r"\quad", r"\ ")
    return value.strip()


def _math_png(latex: str, cache: Path, key: str) -> Path | None:
    try:
        digest = hashlib.sha1(
            f"{latex}|{key}".encode("utf-8")).hexdigest()[:16]
        path = cache / f"{digest}.png"
        if not path.is_file():
            formula_png(_sanitise_latex(latex), path, fontsize=12, dpi=300)
        return path
    except Exception:
        return None


def _set_run_font(run, size: float = 10.5, *, bold: bool = False,
                  italic: bool = False) -> None:
    run.bold = bold
    run.italic = italic
    run.font.name = "Arial"
    run.font.size = Pt(size)


def _add_math(p, latex: str, cache: Path, key: str, *,
              display: bool = False, max_width_cm: float = 6.0) -> None:
    path = _math_png(latex, cache, key)
    if path is None:
        run = p.add_run(_plain_math(latex))
        _set_run_font(run)
        return
    from PIL import Image
    with Image.open(path) as image:
        pixels_w, pixels_h = image.size
    tall = re.search(r"\\(frac|dfrac|tfrac|sqrt|overline|bar|sum|int)\b",
                     latex) is not None
    height_cm = 0.72 if display else (0.68 if tall else 0.50)
    width_cm = height_cm * pixels_w / max(1, pixels_h)
    if width_cm > max_width_cm:
        width_cm = max_width_cm
        height_cm = width_cm * pixels_h / max(1, pixels_w)
    run = p.add_run()
    run.add_picture(str(path), width=Cm(width_cm), height=Cm(height_cm))


def _add_rich_text(p, text: str, cache: Path, key: str,
                   size: float = 10.5) -> None:
    """Add text with inline ``$...$`` maths rendered as small images."""
    value = str(text or "")
    value = value.replace("\\\\quad", " ").replace("\\\\", " ")
    if ("$" not in value and "\\(" not in value and "\\[" not in value
            and re.search(r"\\[A-Za-z]+", value)):
        if PROSE_RE.search(value):
            run = p.add_run(_plain_math(value))
            _set_run_font(run, size)
        else:
            _add_math(p, value.strip(), cache, key)
        return
    position = 0
    for match in MATH_RE.finditer(value):
        plain = value[position:match.start()]
        if plain:
            run = p.add_run(plain)
            _set_run_font(run, size)
        latex = next(group for group in match.groups()
                     if group is not None)
        _add_math(p, latex, cache, key)
        position = match.end()
    tail = value[position:]
    if tail:
        run = p.add_run(tail)
        _set_run_font(run, size)


def _para(doc, text: str = "", *, cache: Path, key: str,
          size: float = 10.5, bold: bool = False, italic: bool = False,
          align=None, before: float = 0, after: float = 2,
          indent: float = 0, hanging: float = 0, keep: bool = False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = 1.05
    pf.keep_with_next = keep
    if align is not None:
        p.alignment = align
    if indent:
        pf.left_indent = Inches(indent)
    if hanging:
        pf.first_line_indent = Inches(-hanging)
    if text:
        _add_rich_text(p, text, cache, key, size)
    return p


def _marks_line(doc, marks: int) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(f"({marks:g} marks)")
    _set_run_font(run, 9.5, italic=True)


# --------------------------------------------------------------------------
# cover
# --------------------------------------------------------------------------

def _replace_runs(paragraph, old: str, new: str) -> bool:
    done = False
    for node in paragraph._p.findall(".//" + qn("w:t")):
        if old in (node.text or ""):
            node.text = node.text.replace(old, new)
            done = True
    return done


def _set_paragraph_text(paragraph, text: str) -> None:
    first = paragraph.runs[0] if paragraph.runs else None
    name = first.font.name if first is not None else "Arial"
    size = first.font.size if first is not None else Pt(10)
    bold = first.bold if first is not None else False
    italic = first.italic if first is not None else False
    for run in list(paragraph.runs):
        run._r.getparent().remove(run._r)
    for br in list(paragraph._p.findall(qn("w:br"))):
        br.getparent().remove(br)
    for br in list(paragraph._p.findall(qn("w:cr"))):
        br.getparent().remove(br)
    run = paragraph.add_run(text)
    run.font.name = name
    run.font.size = size
    run.bold = bold
    run.italic = italic


def _patch_paper_cover(doc) -> None:
    for paragraph in doc.paragraphs:
        text = paragraph.text
        if "CS/FEB" in text and "MAT133" in text:
            _replace_runs(paragraph, "FEB", MONTH)
        elif text.strip().startswith("This question paper consists of"):
            _set_paragraph_text(
                paragraph,
                "This question paper consists of four (4) questions.")
    for box in doc.element.body.iter(qn("w:txbxContent")):
        for paragraph in box.findall(qn("w:p")):
            texts = [(node.text or "") for node in
                     paragraph.findall(".//" + qn("w:t"))]
            is_exam_row = "MAT133" in texts and "2026" in texts
            for node in paragraph.findall(".//" + qn("w:t")):
                value = node.text or ""
                if value == "FEBRUARI":
                    node.text = MONTH_FULL
                elif value == "2026":
                    node.text = str(YEAR)
            if is_exam_row:
                for size in paragraph.findall(".//" + qn("w:sz")):
                    size.set(qn("w:val"), "21")
                for size in paragraph.findall(".//" + qn("w:szCs")):
                    size.set(qn("w:val"), "21")


def _paper_section(doc):
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
        run = hp.add_run(f"CS/{MONTH} {YEAR}/MAT133")
        _set_run_font(run, 8, bold=True)
        run = hp.add_run("\tCONFIDENTIAL")
        _set_run_font(run, 8, bold=True)

    fill_header(section.header)
    fill_header(section.even_page_header)
    return section


# --------------------------------------------------------------------------
# bank access
# --------------------------------------------------------------------------

def _bank() -> tuple[dict[str, dict], dict[str, dict], dict[str, dict]]:
    questions = {}
    for path in (BANK / "questions").glob("*.json"):
        question = json.loads(path.read_text(encoding="utf-8"))
        questions[question["id"]] = question
    assets = {}
    for path in (BANK / "assets").glob("*.json"):
        asset = json.loads(path.read_text(encoding="utf-8"))
        assets[asset["id"]] = asset
    answers = load_json(BANK / "answers.json", {}).get("by_qid") or {}
    return questions, assets, answers


def _asset_path(asset: dict) -> Path:
    path = Path(asset.get("path") or "")
    if path.is_file():
        return path
    alternative = BANK / "assets" / f"{asset['id']}.png"
    return alternative


def _question_assets(question: dict, assets: dict[str, dict]) -> list[dict]:
    """Approved assets, de-duplicated by label.

    ``MAT133-2021-JUL`` contains two five-question sets in one PDF, so Q5 and
    Q5-2 share asset labels on different pages.  A ``-2`` question keeps the
    later occurrence; every other question keeps the first.
    """
    rows = []
    for aid in question.get("assets") or []:
        asset = assets.get(aid)
        if not asset or asset.get("verdict") != "approved":
            continue
        if _asset_path(asset).is_file():
            rows.append(asset)
    seen: dict[str, int] = {}
    keep_later = str(question.get("id") or "").endswith("-2")
    chosen: list[dict] = []
    for asset in rows:
        label = str(asset.get("label") or "").strip()
        if not label:
            chosen.append(asset)
            continue
        if label in seen:
            if keep_later:
                chosen[seen[label]] = asset
            continue
        seen[label] = len(chosen)
        chosen.append(asset)
    return chosen


def _label_assets(rows: list[dict], fig_counter: list[int],
                  table_counter: list[int]) -> tuple[dict[str, str], list[dict]]:
    mapping: dict[str, str] = {}
    ordered = []
    for asset in rows:
        if asset.get("kind") == "table":
            table_counter[0] += 1
            new = f"Table {table_counter[0]}"
        else:
            fig_counter[0] += 1
            new = f"Figure {fig_counter[0]}"
        old = str(asset.get("label") or "").strip()
        if old and old not in mapping:
            mapping[old] = new
        ordered.append({**asset, "_display_label": new})
    return mapping, ordered


def _caption(asset: dict, new_label: str) -> str:
    old = str(asset.get("label") or "").strip()
    caption = " ".join(str(asset.get("caption") or "").split())
    if not old:
        return ""
    if not caption or caption == old:
        return new_label
    if caption.lower().startswith(old.lower()):
        return new_label + caption[len(old):]
    return f"{new_label}: {caption}"


def _attach_assets(question: dict, rows: list[dict]) -> dict[int, list[dict]]:
    """Attach each asset to the first part that names its label."""
    parts = question.get("parts") or []
    attachments: dict[int, list[dict]] = {}
    for asset in rows:
        label = str(asset.get("label") or "").strip()
        target = len(parts) - 1
        if label:
            for index, part in enumerate(parts):
                if re.search(rf"\b{re.escape(label)}\b", part.get("text") or "",
                             re.I):
                    target = index
                    break
        attachments.setdefault(max(0, target), []).append(asset)
    return attachments


# --------------------------------------------------------------------------
# paper build
# --------------------------------------------------------------------------

def _add_figure(doc, asset: dict, caption: str, width_cm: float) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(str(_asset_path(asset)), width=Cm(width_cm))
    if caption:
        p.paragraph_format.keep_with_next = True
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.paragraph_format.space_after = Pt(3)
        run = cap.add_run(caption)
        _set_run_font(run, 8.5, italic=True)


def build_paper(plan: dict, out_dir: Path) -> Path:
    questions, assets, answers = _bank()
    cache = OUT / "_math"
    cache.mkdir(parents=True, exist_ok=True)
    doc = docx.Document(str(TEMPLATE))
    _patch_paper_cover(doc)
    _paper_section(doc)
    fig_counter = [0]
    table_counter = [0]
    for number, slot in enumerate(plan["slots"], start=1):
        if number >= 3:
            doc.add_page_break()
        question = questions[slot["question_id"]]
        rows = _question_assets(question, assets)
        mapping, ordered = _label_assets(rows, fig_counter, table_counter)
        attachments = _attach_assets(question, ordered)
        _para(doc, f"QUESTION {number}", cache=cache,
              key=f"seed{plan['seed']}-q{number}",
              size=11.5, bold=True, before=14, after=5, keep=True)
        for index, part in enumerate(question.get("parts") or []):
            p = doc.add_paragraph()
            pf = p.paragraph_format
            pf.left_indent = Inches(0.28)
            pf.first_line_indent = Inches(-0.28)
            pf.space_before = Pt(4)
            pf.space_after = Pt(0)
            pf.line_spacing = 1.05
            pf.keep_with_next = bool(attachments.get(index))
            label = str(part.get("label") or "")
            if label:
                run = p.add_run(f"{label})")
                _set_run_font(run, 10.5, bold=True)
                run = p.add_run("\t")
                _set_run_font(run, 10.5)
            text = rewrite_references(part.get("text") or "", mapping)
            _add_rich_text(p, text, cache,
                           f"seed{plan['seed']}-q{number}-{label}")
            if not re.search(r"\(\d+\s*marks?\)", text, re.I):
                _marks_line(doc, int(part.get("marks") or 0))
            for asset in attachments.get(index, []):
                new_label = asset.get("_display_label") or ""
                caption = _caption(asset, new_label)
                _add_figure(doc, asset, caption,
                            display_width(asset, {}))
    _para(doc, "END OF QUESTION PAPER", cache=cache,
          key=f"seed{plan['seed']}-end", size=9, italic=True,
          align=WD_ALIGN_PARAGRAPH.CENTER, before=14, after=4)
    _add_appendix(doc, cache, plan["seed"])
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "paper.docx"
    doc.save(str(path))
    return path


APPENDIX = [
    r"\sin^{2} A + \cos^{2} A = 1",
    r"\sin(A+B) = \sin A\cos B + \cos A\sin B",
    r"\cos(A+B) = \cos A\cos B - \sin A\sin B",
    r"\tan(A-B) = \frac{\tan A-\tan B}{1+\tan A\tan B}",
    r"\cos 2A = \cos^{2}A - \sin^{2}A = 1-2\sin^{2}A = 2\cos^{2}A-1",
    r"\sin 2A = 2\sin A\cos A",
    r"\tan^{2}A + 1 = \sec^{2}A",
    r"\tan 2A = \frac{2\tan A}{1-\tan^{2}A}",
    r"\mathrm{Arc},\ s = r\theta",
    r"\mathrm{Area\ of\ sector} = \frac{1}{2}r^{2}\theta",
    r"\frac{a}{\sin A} = \frac{b}{\sin B} = \frac{c}{\sin C}",
    r"a^{2} = b^{2}+c^{2}-2bc\cos A",
    r"\mathrm{Area} = \frac{1}{2}ab\sin C",
    r"\mathrm{Area} = \sqrt{s(s-a)(s-b)(s-c)}",
]


def _add_appendix(doc, cache: Path, seed: int) -> None:
    doc.add_page_break()
    _para(doc, "APPENDIX 1", cache=cache, key=f"seed{seed}-appendix",
          size=13, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER,
          before=0, after=3)
    _para(doc, "Formula sheet (as supplied with the paper).", cache=cache,
          key=f"seed{seed}-appendix-note", size=8.5, italic=True,
          align=WD_ALIGN_PARAGRAPH.CENTER, after=8)
    table = doc.add_table(rows=len(APPENDIX), cols=1)
    table.autofit = True
    for index, latex in enumerate(APPENDIX):
        cell = table.cell(index, 0)
        cell.text = ""
        paragraph = cell.paragraphs[0]
        paragraph.paragraph_format.space_after = Pt(4)
        numbered = f"{index + 1}.\\quad {latex}"
        _add_math(paragraph, numbered, cache,
                  f"seed{seed}-appendix-{index}", display=True,
                  max_width_cm=15.5)


# --------------------------------------------------------------------------
# scheme build
# --------------------------------------------------------------------------

def _rewrite_scheme_xml(source: Path, target: Path) -> None:
    replacements = (
        ("CSC662", "MAT133"),
        ("COMPUTER SECURITY", "PRE CALCULUS"),
        ("OCTOBER", "NOVEMBER"),
        ("OCT", "NOV"),
    )
    pattern = re.compile(r"(<w:t\b[^>]*>)(.*?)(</w:t>)", re.S)

    def replace(match):
        text = match.group(2)
        for old, new in replacements:
            text = text.replace(old, new)
        return match.group(1) + text + match.group(3)

    with zipfile.ZipFile(source) as zin, zipfile.ZipFile(
            target, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml" or (
                    item.filename.startswith("word/header")
                    and item.filename.endswith(".xml")):
                data = pattern.sub(replace, data.decode("utf-8")).encode(
                    "utf-8")
            zout.writestr(item, data)


def _clear_after_section_break(document) -> None:
    cut = None
    for index, paragraph in enumerate(document.paragraphs):
        ppr = paragraph._p.pPr
        if ppr is not None and ppr.find(qn("w:sectPr")) is not None:
            cut = index
            break
    if cut is None:
        raise RuntimeError("scheme template has no section break")
    for paragraph in list(document.paragraphs)[cut + 1:]:
        element = paragraph._element
        parent = element.getparent()
        if parent is not None:
            parent.remove(element)


def _patch_scheme_notes(doc, plan: dict) -> None:
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text.startswith("This marking scheme accompanies"):
            _set_paragraph_text(
                paragraph,
                "This marking scheme accompanies the MAT133 mock paper "
                f"({MONTH_FULL.title()} {YEAR}).")
        elif text.startswith("Computed answers show working"):
            _set_paragraph_text(
                paragraph,
                "Answers are unofficial model answers generated from the "
                "printed past-paper question; they are not an official UTM "
                "marking scheme.")
        elif text.startswith("Supported theory marking points"):
            _set_paragraph_text(
                paragraph,
                "Marking points follow the printed part labels and marks. "
                "Verify every model answer against the source page.")
        elif text.startswith("Part A ="):
            _set_paragraph_text(
                paragraph,
                "Four questions: 10 + 10 + 10 + 25 marks; total = 55 marks.")
        elif text.startswith("Computed:"):
            _set_paragraph_text(
                paragraph,
                f"Questions: {len(plan['slots'])}. Real recycled questions: "
                f"{len(plan['slots'])}. Placeholders: 0.")
        elif text.startswith("Questions and answers are"):
            _set_paragraph_text(
                paragraph,
                "For local study use only; model answers are unofficial.")
        elif text.startswith("Near-copy rejection"):
            _set_paragraph_text(
                paragraph,
                "Every question is a real MAT133 past-paper question; its "
                "source paper and page are printed with the answer.")
        elif text.startswith("This marking scheme consists of"):
            _set_paragraph_text(
                paragraph,
                "This marking scheme consists of 1 printed page.")


def _patch_scheme_cover(doc) -> None:
    for box in doc.element.body.iter(qn("w:txbxContent")):
        for paragraph in box.findall(qn("w:p")):
            for node in paragraph.findall(".//" + qn("w:t")):
                value = node.text or ""
                if value == "3 HOURS":
                    node.text = "2 HOURS"
                elif value == "NOVEMBER 2026 (MOCK)":
                    node.text = f"{MONTH_FULL} {YEAR}"


def _source_label(question: dict) -> str:
    pages = ", ".join(str(page) for page in question.get("pages") or [])
    return (f"{question.get('source_paper')}"
            + (f", page(s) {pages}" if pages else ""))


def _scheme_body(doc, plan: dict, questions: dict, answers: dict) -> None:
    for number, slot in enumerate(plan["slots"], start=1):
        question = questions[slot["question_id"]]
        answer = answers.get(question["id"]) or {}
        heading = doc.add_paragraph()
        heading.paragraph_format.space_before = Pt(12)
        heading.paragraph_format.space_after = Pt(2)
        heading.paragraph_format.keep_with_next = True
        run = heading.add_run(f"QUESTION {number}")
        _set_run_font(run, 11, bold=True)
        run = heading.add_run(f"\t({int(question['marks'])} marks)")
        _set_run_font(run, 11, bold=True)
        heading.paragraph_format.tab_stops.add_tab_stop(
            Inches(6.25), WD_TAB_ALIGNMENT.RIGHT)
        _para(doc, f"Source: {_source_label(question)}", cache=OUT / "_math",
              key=f"scheme{plan['seed']}-{number}-src", size=9, italic=True,
              after=2)
        _para(doc,
              "Unofficial model answer — AI-generated, not an official UTM "
              "marking scheme.",
              cache=OUT / "_math", key=f"scheme{plan['seed']}-{number}-label",
              size=9, bold=True, after=3)
        for part in question.get("parts") or []:
            label = str(part.get("label") or "")
            marks = int(part.get("marks") or 0)
            _para(doc, f"{label}) {part.get('text') or ''}",
                  cache=OUT / "_math",
                  key=f"scheme{plan['seed']}-{number}-{label}-q",
                  size=9.5, after=2)
            subpart = next(
                (row for row in answer.get("subparts") or []
                 if str(row.get("label") or "").lower() == label.lower()),
                {})
            if subpart.get("answer"):
                _para(doc, f"Answer: {subpart['answer']}",
                      cache=OUT / "_math",
                      key=f"scheme{plan['seed']}-{number}-{label}-a",
                      size=10, after=1)
            for line in subpart.get("working") or []:
                _para(doc, f"• {line}", cache=OUT / "_math",
                      key=f"scheme{plan['seed']}-{number}-{label}-w",
                      size=9.5, after=1)
            if not subpart.get("answer"):
                _para(doc, "No usable model answer for this part.",
                      cache=OUT / "_math",
                      key=f"scheme{plan['seed']}-{number}-{label}-none",
                      size=9, italic=True, after=1)
            if not re.search(r"\(\d+\s*marks?\)",
                             part.get("text") or "", re.I):
                _marks_line(doc, marks)
        if answer.get("assumptions"):
            _para(doc, f"Assumptions: {answer['assumptions']}",
                  cache=OUT / "_math",
                  key=f"scheme{plan['seed']}-{number}-assume",
                  size=8.5, italic=True, after=3)
        if answer.get("confidence"):
            _para(doc, f"Model confidence: {answer['confidence']}.",
                  cache=OUT / "_math",
                  key=f"scheme{plan['seed']}-{number}-conf",
                  size=8.5, italic=True, after=3)
    _para(doc, "END OF MARKING SCHEME", cache=OUT / "_math",
          key=f"scheme{plan['seed']}-end", size=9, italic=True,
          align=WD_ALIGN_PARAGRAPH.CENTER, before=14, after=4)


def _set_word_15(document) -> None:
    settings = document.settings.element
    compat = settings.find(qn("w:compat"))
    if compat is None:
        return
    for setting in compat.findall(qn("w:compatSetting")):
        if setting.get(qn("w:name")) == "compatibilityMode":
            setting.set(qn("w:val"), "15")


def build_scheme(plan: dict, out_dir: Path) -> Path:
    questions, assets, answers = _bank()
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mat133_scheme_") as tmp:
        prepared = Path(tmp) / "scheme_template.docx"
        _rewrite_scheme_xml(SCHEME_TEMPLATE, prepared)
        doc = docx.Document(str(prepared))
        _clear_after_section_break(doc)
        _patch_scheme_cover(doc)
        _patch_scheme_notes(doc, plan)
        _scheme_body(doc, plan, questions, answers)
        _set_word_15(doc)
        path = out_dir / "scheme.docx"
        doc.save(str(path))
    return path


# --------------------------------------------------------------------------
# QA and evidence
# --------------------------------------------------------------------------

def _docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml").decode("utf-8")
    return "".join(re.findall(r"<w:t\b[^>]*>([^<]*)</w:t>", xml))


def _update_page_count(docx_path: Path, pdf_path: Path, *,
                       scheme: bool) -> int:
    pages = export_pdf(docx_path, pdf_path)
    doc = docx.Document(str(docx_path))
    needle = ("marking scheme consists of" if scheme
              else "examination paper consists of")
    for paragraph in doc.paragraphs:
        if needle in paragraph.text:
            _set_paragraph_text(
                paragraph,
                f"This {'marking scheme' if scheme else 'examination paper'} "
                f"consists of {pages} printed pages")
            break
    doc.save(str(docx_path))
    return export_pdf(docx_path, pdf_path)


def _qa(plan: dict, paper_docx: Path, paper_pdf: Path,
        scheme_docx: Path, scheme_pdf: Path) -> dict:
    questions, assets, answers = _bank()
    paper_text = _docx_text(paper_docx)
    scheme_text = _docx_text(scheme_docx)
    problems = []
    for name, path in (("paper", paper_docx), ("scheme", scheme_docx)):
        try:
            with zipfile.ZipFile(path) as archive:
                ET.fromstring(archive.read("word/document.xml"))
        except Exception as error:
            problems.append(f"{name} DOCX is invalid: {error}")
    slots = plan["slots"]
    if len(slots) != 4:
        problems.append(f"expected 4 slots, got {len(slots)}")
    if sum(int(slot["marks"]) for slot in slots) != 55:
        problems.append("slot marks do not total 55")
    ids = [slot["question_id"] for slot in slots]
    if len(set(ids)) != len(ids):
        problems.append("duplicate question inside the paper")
    if len({slot["source_paper"] for slot in slots}) < 4:
        problems.append("fewer than 4 distinct source papers")
    for slot in slots:
        question = questions.get(slot["question_id"]) or {}
        answer = answers.get(slot["question_id"]) or {}
        if question.get("status") != "approved":
            problems.append(f"{slot['question_id']} is not approved")
        if not answer.get("usable"):
            problems.append(f"{slot['question_id']} has no usable answer")
        parts = question.get("parts") or []
        for part in parts:
            label = part.get("label") or "?"
            if not str(part.get("text") or "").strip():
                problems.append(
                    f"{slot['question_id']} part {label} has no text")
            if not part.get("marks"):
                problems.append(
                    f"{slot['question_id']} part {label} has no marks")
        labels = [str(part.get("label") or "").lower() for part in parts]
        answered = {
            str(row.get("label") or "").lower(): row
            for row in answer.get("subparts") or []}
        if sorted(labels) != sorted(answered):
            problems.append(
                f"{slot['question_id']} answer labels {sorted(answered)} "
                f"do not match parts {sorted(labels)}")
        for label, row in answered.items():
            if not str(row.get("answer") or "").strip():
                problems.append(
                    f"{slot['question_id']} part {label} has no answer")
        for aid in question.get("assets") or []:
            asset = assets.get(aid)
            if asset and asset.get("verdict") == "approved" \
                    and not _asset_path(asset).is_file():
                problems.append(f"missing asset file {aid}")
    def _headings(path: Path) -> int:
        document = docx.Document(str(path))
        return sum(
            1 for paragraph in document.paragraphs
            if re.match(r"^QUESTION\s+[1-4](?!\d)", paragraph.text.strip()))

    paper_headings = _headings(paper_docx)
    scheme_headings = _headings(scheme_docx)
    if paper_headings != 4:
        problems.append(f"paper headings: {paper_headings}")
    if scheme_headings != 4:
        problems.append(f"scheme headings: {scheme_headings}")
    for token in FORBIDDEN:
        if token.lower() in paper_text.lower():
            problems.append(f"paper contains {token}")
    for token in ("CSC662", "COMPUTER SECURITY", "OCTOBER 2026"):
        if token.lower() in scheme_text.lower():
            problems.append(f"scheme contains {token}")
    with pymupdf.open(str(paper_pdf)) as document:
        paper_pages = len(document)
    with pymupdf.open(str(scheme_pdf)) as document:
        scheme_pages = len(document)
    return {
        "schema_version": 1,
        "subject": SUBJECT,
        "seed": int(plan["seed"]),
        "checked_on": _today(),
        "paper": {
            "path": str(paper_docx),
            "pdf": str(paper_pdf),
            "pages": paper_pages,
            "headings": paper_headings,
            "forbidden_tokens": [
                token for token in FORBIDDEN
                if token.lower() in paper_text.lower()],
        },
        "scheme": {
            "path": str(scheme_docx),
            "pdf": str(scheme_pdf),
            "pages": scheme_pages,
            "headings": scheme_headings,
        },
        "total_marks": sum(int(slot["marks"]) for slot in slots),
        "problems": problems,
    }


def _evidence(plan: dict) -> dict:
    questions, assets, answers = _bank()
    slots = []
    for slot in plan["slots"]:
        question = questions[slot["question_id"]]
        answer = answers.get(slot["question_id"]) or {}
        slots.append({
            "slot": slot["slot"],
            "question_id": question["id"],
            "marks": question["marks"],
            "source_paper": question["source_paper"],
            "pages": question.get("pages") or [],
            "topic_tags": question.get("topic_tags") or [],
            "assets": [
                {
                    "id": asset["id"],
                    "label": asset.get("label"),
                    "path": str(_asset_path(asset)),
                }
                for asset in _question_assets(question, assets)],
            "answer": {
                "answer_id": answer.get("answer_id"),
                "provenance": answer.get("provenance"),
                "confidence": answer.get("confidence"),
                "usable": answer.get("usable"),
                "subparts": len(answer.get("subparts") or []),
            },
        })
    return {
        "schema_version": 1,
        "subject": SUBJECT,
        "seed": int(plan["seed"]),
        "built_on": _now(),
        "format_profile": str(FORMAT),
        "total_marks": sum(int(slot["marks"]) for slot in plan["slots"]),
        "slots": slots,
    }


def _preview(pdf: Path, target_dir: Path, stem: str) -> list[str]:
    target_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    with pymupdf.open(str(pdf)) as document:
        for index, page in enumerate(document, start=1):
            path = target_dir / f"{stem}_page_{index:02d}.png"
            page.get_pixmap(dpi=90).save(str(path))
            paths.append(str(path))
    return paths


def build_seed(seed: int) -> dict:
    seed_dir = OUT / f"seed_{seed:02d}"
    if seed_dir.exists():
        shutil.rmtree(seed_dir)
    plans = [plan for plan in plans_for([seed]) if int(plan["seed"]) == seed]
    if not plans:
        raise SystemExit(f"no plan for seed {seed}")
    plan = plans[0]
    save_json(seed_dir / "plan.json", plan)
    paper_docx = build_paper(plan, seed_dir)
    scheme_docx = build_scheme(plan, seed_dir)
    paper_pdf = seed_dir / "paper.pdf"
    scheme_pdf = seed_dir / "scheme.pdf"
    _update_page_count(paper_docx, paper_pdf, scheme=False)
    _update_page_count(scheme_docx, scheme_pdf, scheme=True)
    qa = _qa(plan, paper_docx, paper_pdf, scheme_docx, scheme_pdf)
    save_json(seed_dir / "qa.json", qa)
    evidence = _evidence(plan)
    save_json(seed_dir / "evidence.json", evidence)
    meta = {
        "subject": SUBJECT,
        "seed": seed,
        "mode": "recycle_v2",
        "model": "none (deterministic assembly of real bank questions)",
        "cost_usd": 0.0,
        "accepted": len(plan["slots"]),
        "placeholders": 0,
        "created": _now(),
        "total_marks": plan["total_marks"],
        "question_count": len(plan["slots"]),
        "source_papers": [slot["source_paper"] for slot in plan["slots"]],
        "question_ids": [slot["question_id"] for slot in plan["slots"]],
        "qa_problems": len(qa["problems"]),
        "paper_pdf": str(paper_pdf),
        "scheme_pdf": str(scheme_pdf),
    }
    save_json(seed_dir / "meta.json", meta)
    _preview(paper_pdf, seed_dir / "preview", "paper")
    _preview(scheme_pdf, seed_dir / "preview", "scheme")
    return {"seed": seed, "plan": str(seed_dir / "plan.json"),
            "qa": qa, "paper_pdf": str(paper_pdf),
            "scheme_pdf": str(scheme_pdf), "meta": str(seed_dir / "meta.json")}


def _gate_b_report(results: list[dict]) -> Path:
    lines = [
        "# MAT133 V5 — Gate B package (seeds 1–3)",
        "",
        f"Built: {_today()}",
        "Subject: MAT133 (Type D recycle, playbook v2.0)",
        "",
        "Format: 4 questions, 10 + 10 + 10 + 25 = 55 marks, 2 HOURS.",
        "Every question is an approved real past-paper question with a usable",
        "unofficial model answer. The scheme uses the standard UTM marking",
        "scheme cover.",
        "",
        "## Gates",
        "",
        "- Gate A: approved by project owner on 2026-11-14.",
        "- Gate B: **pending owner review of these three seeds.**",
        "",
        "## Seeds",
        "",
    ]
    for result in results:
        seed = result["seed"]
        qa = result["qa"]
        plan = load_json(Path(result["plan"]), {})
        lines += [
            f"### Seed {seed}",
            "",
            f"- Paper: `{result['paper_pdf']}`",
            f"- Scheme: `{result['scheme_pdf']}`",
            f"- Marks: {plan.get('total_marks')}",
            f"- QA problems: {len(qa['problems'])}",
            "",
            "| Slot | Question | Marks | Topic | Source | Pages | Assets |",
            "|---|---|---|---|---|---|---|",
        ]
        for slot in plan.get("slots") or []:
            lines.append(
                f"| {slot['slot']} | {slot['question_id']} | "
                f"{slot['marks']} | {', '.join(slot.get('topic_tags') or [slot.get('topic') or ''])} | "
                f"{slot.get('source_paper') or ''} | "
                f"{', '.join(str(page) for page in slot.get('pages') or [])} | "
                f"{len(slot.get('assets') or [])} |")
        lines.append("")
        for problem in qa["problems"]:
            lines.append(f"- QA problem: {problem}")
        if qa["problems"]:
            lines.append("")
    Path(OUT / "Gate_B_report.md").write_text("\n".join(lines) + "\n",
                                              encoding="utf-8")
    return OUT / "Gate_B_report.md"


def _index(results: list[dict]) -> Path:
    rows = []
    for result in results:
        seed = result["seed"]
        plan = load_json(Path(result["plan"]), {})
        items = "".join(
            f"<li><strong>{slot['slot']}</strong> "
            f"{slot['question_id']} ({slot['marks']} marks) — "
            f"{', '.join(slot.get('topic_tags') or [slot.get('topic') or ''])}, {slot.get('source_paper') or ''}</li>"
            for slot in plan.get("slots") or [])
        rows.append(
            f"<h2>Seed {seed}</h2>"
            f"<p><a href=\"seed_{seed:02d}/paper.pdf\">paper.pdf</a> · "
            f"<a href=\"seed_{seed:02d}/scheme.pdf\">scheme.pdf</a> · "
            f"<a href=\"seed_{seed:02d}/qa.json\">qa.json</a> · "
            f"<a href=\"seed_{seed:02d}/evidence.json\">evidence.json</a></p>"
            f"<ul>{items}</ul>"
            f"<p>QA problems: {len(result['qa']['problems'])}</p>")
    html = ("<!doctype html><meta charset=\"utf-8\">"
            "<title>MAT133 V5 Gate B</title>"
            "<style>body{font-family:Arial;margin:2rem}"
            "h1{color:#5b1a1a}</style>"
            "<h1>MAT133 V5 — seeds 1–3 (Gate B)</h1>"
            + "".join(rows) + "</body>")
    path = OUT / "index.html"
    path.write_text(html, encoding="utf-8")
    return path


def build(seeds: list[int]) -> dict:
    from src.subjects.mat133.assemble_v2 import feasibility_report
    feasibility = feasibility_report()
    save_json(OUT / "feasibility.json", feasibility)
    results = [build_seed(seed) for seed in seeds]
    report = _gate_b_report(results)
    index = _index(results)
    summary = {
        "schema_version": 1,
        "subject": SUBJECT,
        "built_on": _now(),
        "feasibility": feasibility,
        "seeds": results,
        "gate_b_report": str(report),
        "index": str(index),
        "problems": sum(len(result["qa"]["problems"]) for result in results),
    }
    save_json(OUT / "build_summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", default="1-3")
    args = parser.parse_args()
    if "-" in args.seeds:
        start, end = args.seeds.split("-", 1)
        seeds = list(range(int(start), int(end) + 1))
    else:
        seeds = [int(part) for part in args.seeds.split(",") if part.strip()]
    print(json.dumps(build(seeds), indent=2))


if __name__ == "__main__":
    main()
