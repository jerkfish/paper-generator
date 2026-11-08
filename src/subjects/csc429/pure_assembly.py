"""P6: assemble reviewed Type D seeds 1-3 with Word COM."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

import docx
import pymupdf
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

from src import config
from src.assemble.pdf_export import export_pdf
from src.subjects import forbidden
from src.subjects.csc429 import pure_config, pure_guard
from src.subjects.csc429 import seed_pilot as pilot

TRACKING = config.TRACKING_DIR / "csc429"
BANK = TRACKING / "bank"
QUESTIONS = BANK / "questions"
ASSETS = BANK / "assets"
PLANS = BANK / "plans"
ANSWERS = BANK / "answers.json"
TEMPLATES = TRACKING / "templates"
PAPER_TEMPLATE = TEMPLATES / "paper_template_good_example_recreational.docx"
SCHEME_TEMPLATE = TEMPLATES / "scheme_template_fix_wide_content.docx"
OUT = config.PROJECT_ROOT / "outputs" / "pure_extraction" / "CSC429_all_seeds"

REF_RE = re.compile(r"\b(Figure|Table)\s+(\d+)\b", re.I)


def _load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _save(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
          spacing: float = 1.25, keep_with_next: bool = False):
    paragraph = document.add_paragraph()
    if align is not None:
        paragraph.alignment = align
    paragraph.paragraph_format.line_spacing = spacing
    paragraph.paragraph_format.space_before = Pt(before)
    paragraph.paragraph_format.space_after = Pt(after)
    if keep_with_next:
        paragraph.paragraph_format.keep_with_next = True
    run = paragraph.add_run(text)
    run.font.name = "Arial"
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    return paragraph


def _multiline(document, text: str, *, size: float = 11,
               keep_with_next: bool = False):
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.line_spacing = 1.25
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(6)
    paragraph.paragraph_format.keep_with_next = keep_with_next
    run = paragraph.add_run()
    run.font.name = "Arial"
    run.font.size = Pt(size)
    lines = str(text or "").replace("\r", "").split("\n")
    for index, line in enumerate(lines):
        if index:
            run.add_break()
        run.add_text(line)
    return paragraph


def _display_question_number(slot_label: str) -> int:
    if str(slot_label).upper().startswith("B"):
        return 11
    return int(str(slot_label)[1:])


def _question_heading(document, label, marks: int) -> None:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(18)
    paragraph.paragraph_format.space_after = Pt(10)
    paragraph.paragraph_format.keep_with_next = True
    section = document.sections[-1]
    text_width = (section.page_width - section.left_margin
                  - section.right_margin)
    paragraph.paragraph_format.tab_stops.add_tab_stop(
        text_width, WD_TAB_ALIGNMENT.RIGHT)
    run = paragraph.add_run(f"QUESTION {label}")
    run.bold = True
    run.font.name = "Arial"
    run.font.size = Pt(11)
    paragraph.add_run("\t")
    mark = paragraph.add_run(f"({marks} marks)")
    mark.font.name = "Arial"
    mark.font.size = Pt(11)


def _display_width(asset: dict, config_data: dict) -> float:
    width = float(asset.get("width_px") or 0)
    height = float(asset.get("height_px") or 0)
    minimum = float(config_data.get("figure_min_width_cm", 6.0))
    maximum = float(config_data.get("figure_max_width_cm", 16.2))
    max_height = 18.0 if asset.get("kind") == "picture" else float(
        config_data.get("figure_max_height_cm", 18.0))
    if width <= 0 or height <= 0:
        return minimum
    aspect = width / height
    area = width * height
    chosen = 8.0 if area < 300_000 else 12.0
    if aspect >= 4.5:
        chosen = maximum
    if asset.get("kind") == "table":
        chosen = 12.0
    chosen = max(minimum, min(maximum, chosen))
    if chosen * height / width > max_height:
        chosen = max_height * width / height
    return round(max(minimum, chosen), 2)


def _picture(document, path: Path, width_cm: float) -> None:
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(3)
    paragraph.paragraph_format.space_after = Pt(1)
    paragraph.paragraph_format.keep_with_next = True
    paragraph.add_run().add_picture(str(path), width=Cm(width_cm))


def _caption(document, text: str) -> None:
    _para(document, text, italic=True, size=9,
          align=WD_ALIGN_PARAGRAPH.CENTER, before=4, after=8, spacing=1.0,
          keep_with_next=True)


def _cell_text(cell, text: str, *, bold: bool = False) -> None:
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.line_spacing = 1.0
    paragraph.paragraph_format.space_before = Pt(1)
    paragraph.paragraph_format.space_after = Pt(1)
    run = paragraph.add_run(str(text or ""))
    run.font.name = "Arial"
    run.font.size = Pt(9)
    run.bold = bold


def _borders(table) -> None:
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


def _table(document, table_spec: dict, caption: str) -> None:
    if caption:
        _caption(document, caption)
    rows = table_spec.get("rows") or []
    columns = int(table_spec.get("columns") or 0)
    columns = max(columns, max((len(row.get("cells") or [])
                               for row in rows), default=1))
    table = document.add_table(rows=len(rows) or 1, cols=columns)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    _borders(table)
    widths = table_spec.get("column_widths_cm") or []
    for r_index, row in enumerate(rows):
        c_index = 0
        for cell_spec in row.get("cells") or []:
            if c_index >= columns:
                break
            cell = table.rows[r_index].cells[c_index]
            _cell_text(cell, cell_spec.get("text", ""),
                       bold=(r_index == 0))
            colspan = int(cell_spec.get("colspan") or 1)
            if colspan > 1 and c_index + colspan <= columns:
                cell = cell.merge(
                    table.rows[r_index].cells[c_index + colspan - 1])
            c_index += colspan
        if widths:
            for index, width in enumerate(widths[:columns]):
                table.rows[r_index].cells[index].width = Cm(float(width))
    _para(document, "", after=4)


def _inside(bbox: list, box: list) -> bool:
    cx = (float(bbox[0]) + float(bbox[2])) / 2
    cy = (float(bbox[1]) + float(bbox[3])) / 2
    return box[0] <= cx <= box[2] and box[1] <= cy <= box[3]


def _clean_question_text(question: dict, assets: dict[str, dict]) -> str:
    spans = (question.get("native_text_blocks") or [{}])[0].get("spans") or []
    if not spans:
        return str((question.get("native_text_blocks") or [{}])[0].get(
            "text", ""))
    boxes = []
    for aid in question.get("assets") or []:
        asset = assets.get(aid)
        if not asset:
            continue
        page = int(asset.get("page", 0))
        for key in ("content_bbox", "caption_bbox"):
            box = asset.get(key)
            if box and len(box) == 4:
                boxes.append((page, [float(value) for value in box]))
    kept = []
    for span in spans:
        bbox = span.get("bbox")
        page = int(span.get("page", 0))
        if bbox and any(page == box_page and _inside(bbox, box)
                        for box_page, box in boxes):
            continue
        text = str(span.get("text", "")).strip()
        if text:
            kept.append(text)
    return chr(10).join(kept)


def _rewrite_refs(text: str, mapping: dict[str, str]) -> str:
    def replace(match):
        old = f"{match.group(1).title()} {int(match.group(2))}"
        return mapping.get(old, match.group(0))
    return REF_RE.sub(replace, str(text or ""))


def _caption_text(asset: dict, new_label: str) -> str:
    caption = " ".join(str(asset.get("caption") or "").split())
    old = str(asset.get("label") or "")
    if old and caption.lower().startswith(old.lower()):
        caption = new_label + caption[len(old):]
    elif caption:
        caption = f"{new_label}: {caption}"
    else:
        caption = new_label
    return caption


def _asset_mapping(question: dict, assets: dict[str, dict],
                   fig_counter: list[int], table_counter: list[int]):
    mapping = {}
    ordered = []
    for aid in question.get("assets") or []:
        asset = assets.get(aid)
        if not asset:
            raise RuntimeError(f"missing asset {aid}")
        if asset.get("kind") == "table":
            table_counter[0] += 1
            new = f"Table {table_counter[0]}"
        else:
            fig_counter[0] += 1
            new = f"Figure {fig_counter[0]}"
        old = str(asset.get("label") or "")
        if old in mapping:
            raise RuntimeError(f"duplicate asset label {old} in {question['id']}")
        mapping[old] = new
        ordered.append((asset, new))
    return mapping, ordered


ROMAN_LABELS = {"i", "ii", "iii", "iv", "v", "vi", "vii"}


def _split_subparts(text: str, subparts: list[dict]) -> list[tuple[str, str]]:
    labels = [str(part.get("label", "")).lower()
              for part in subparts or []
              if str(part.get("label", "")).lower() not in ("", "main")]
    if not labels:
        return [("", str(text or "").strip())]
    ordered = sorted(set(labels), key=len, reverse=True)
    alternatives = "|".join(re.escape(label) for label in ordered)
    pattern = re.compile(
        r"(?:(?<=\n)|^|(?<=[.!?]))\s*(?:\((?P<paren>"
        + alternatives
        + r")\)|(?P<close>" + alternatives + r")\))\s*",
        re.I | re.M)
    matches = list(pattern.finditer(text or ""))
    if not matches:
        return [("", str(text or "").strip())]
    segments: list[tuple[str, str]] = []
    preamble = (text or "")[:matches[0].start()].strip()
    if preamble:
        segments.append(("", preamble))
    for index, match in enumerate(matches):
        label = (match.group("paren") or match.group("close")).lower()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = (text or "")[start:end].strip()
        segments.append((label, body))
    return segments


def _add_question_text(document, question: dict) -> None:
    text = question.get("native_text_blocks", [{}])[0].get("text", "")
    segments = _split_subparts(text, question.get("subpart_marks") or [])
    if len(segments) == 1 and not segments[0][0]:
        _multiline(document, segments[0][1], keep_with_next=bool(
            question.get("assets")))
        return
    numbering = pilot._QuestionNumbering(document)
    for label, body in segments:
        if not label:
            if body:
                _multiline(document, body, keep_with_next=True)
            continue
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.line_spacing = 1.25
        paragraph.paragraph_format.space_before = Pt(0)
        paragraph.paragraph_format.space_after = Pt(4)
        if label in ROMAN_LABELS:
            num_id = numbering.roman(label)
        else:
            num_id = numbering.letter(label)
        pilot._apply_numbering(paragraph, num_id)
        run = paragraph.add_run(body)
        run.font.name = "Arial"
        run.font.size = Pt(11)


def _paper_question(document, question: dict, assets: dict[str, dict],
                    config_data: dict, fig_counter: list[int],
                    table_counter: list[int], slot_label: str) -> dict:
    mapping, ordered = _asset_mapping(
        question, assets, fig_counter, table_counter)
    _question_heading(document, _display_question_number(slot_label),
                      int(question["marks"]))
    rewritten = _rewrite_refs(
        _clean_question_text(question, assets), mapping)
    rewritten_question = dict(question)
    rewritten_question["native_text_blocks"] = [{
        "text": rewritten,
    }]
    if rewritten.strip():
        _add_question_text(document, rewritten_question)
    for asset, new_label in ordered:
        caption = _caption_text(asset, new_label)
        if asset.get("treatment") == "native_table" and asset.get("native_table"):
            _table(document, asset["native_table"], caption)
            continue
        path = config.PROJECT_ROOT / asset["path"]
        _picture(document, path, _display_width(asset, config_data))
        _caption(document, caption)
    return {
        "question_id": question["id"],
        "labels": {old: new for old, new in mapping.items()},
        "assets": [asset["id"] for asset, _new in ordered],
    }


def build_paper(seed: int, plan: dict, assets: dict[str, dict],
                config_data: dict, target: Path) -> dict:
    shutil.copy2(PAPER_TEMPLATE, target)
    document = docx.Document(str(target))
    document.styles["Normal"].font.name = "Arial"
    document.styles["Normal"].font.size = Pt(11)
    _clear_body(document)
    _para(document, "PART A (80 MARKS)", bold=True, size=11, after=4)
    _para(document, "Answer ALL questions in this part.", size=11, after=8)
    fig_counter = [0]
    table_counter = [0]
    mapping = {}
    for slot in [row for row in plan["slots"] if row["part"] == "A"]:
        question = _load(QUESTIONS / f"{slot['question_id']}.json", {})
        mapping[slot["question_id"]] = _paper_question(
            document, question, assets, config_data, fig_counter,
            table_counter, slot["slot"])
    document.add_page_break()
    _para(document, "PART B (20 MARKS)", bold=True, size=11, after=4)
    _para(document, "Answer the question in this part.", size=11, after=8)
    for slot in [row for row in plan["slots"] if row["part"] == "B"]:
        question = _load(QUESTIONS / f"{slot['question_id']}.json", {})
        mapping[slot["question_id"]] = _paper_question(
            document, question, assets, config_data, fig_counter,
            table_counter, slot["slot"])
    document.save(str(target))
    return mapping


def _patch_scheme_notes(document) -> None:
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text.startswith("This marking scheme accompanies"):
            paragraph.text = (
                "This marking scheme accompanies the CSC429 mock paper "
                "(November 2026).")
        elif text.startswith("Generated answers show working"):
            paragraph.text = (
                "Answers are unofficial reference answers, not official UTM "
                "marking schemes.")
        elif text.startswith("Generated marking points state"):
            paragraph.text = (
                "Marking points show the expected answer and mark allocation; "
                "check them against the source paper.")
        elif text.startswith("Part A ="):
            paragraph.text = (
                "Part A = 4 x 5 + 6 x 10; Part B = 1 x 20; total = 100 marks.")
        elif text.startswith("Generated slots:"):
            paragraph.text = (
                "Approved real questions only; no generators, placeholders or "
                "parametric variants.")
        elif text.startswith("Structure derived from"):
            paragraph.text = (
                "Structure derived from the supplied CSC429 papers; every "
                "question remains traceable to its source page.")
        elif text.startswith("This marking scheme consists of"):
            paragraph.text = "This marking scheme consists of 1 printed page"


def _scheme_entry(document, question: dict, answer: dict,
                  slot_label: str) -> None:
    _question_heading(document, _display_question_number(slot_label),
                      int(question["marks"]))
    _para(document, f"Source: {question['source_paper']}, page "
          f"{question.get('pages')}", italic=True, size=9, after=3)
    _para(document, "Unofficial model answer:", bold=True, size=9, after=2)
    for block in str(answer.get("answer", "")).split("\n\n"):
        if block.strip():
            _para(document, block.strip(), size=9.5, after=3)
    marking = answer.get("marking") or []
    if marking:
        _para(document, "Marking points:", bold=True, size=9, after=2)
        for point in marking:
            _para(document, f"• {point}", size=9, italic=True, after=1)
    _para(document, f"Model confidence: {answer.get('confidence', 'medium')}.",
          size=8, italic=True, after=2)
    notes = answer.get("notes") or ""
    if notes:
        _para(document, f"Model note: {notes}", size=8, italic=True, after=4)


def build_scheme(seed: int, plan: dict, answers: dict, target: Path) -> None:
    shutil.copy2(SCHEME_TEMPLATE, target)
    document = docx.Document(str(target))
    document.styles["Normal"].font.name = "Arial"
    document.styles["Normal"].font.size = Pt(10)
    _patch_scheme_notes(document)
    _clear_body(document)
    _para(document, "PART A — MARKING GUIDE", bold=True, size=12,
          align=WD_ALIGN_PARAGRAPH.CENTER, before=8, after=8)
    for slot in [row for row in plan["slots"] if row["part"] == "A"]:
        question = _load(QUESTIONS / f"{slot['question_id']}.json", {})
        answer = answers.get(question["id"], {})
        if not answer.get("answer"):
            raise RuntimeError(f"missing answer for {question['id']}")
        _scheme_entry(document, question, answer, slot["slot"])
    document.add_page_break()
    _para(document, "PART B — MARKING GUIDE", bold=True, size=12,
          align=WD_ALIGN_PARAGRAPH.CENTER, before=8, after=8)
    for slot in [row for row in plan["slots"] if row["part"] == "B"]:
        question = _load(QUESTIONS / f"{slot['question_id']}.json", {})
        answer = answers.get(question["id"], {})
        if not answer.get("answer"):
            raise RuntimeError(f"missing answer for {question['id']}")
        _scheme_entry(document, question, answer, slot["slot"])
    _para(document, "END OF MARKING SCHEME", italic=True, size=9,
          align=WD_ALIGN_PARAGRAPH.CENTER, before=12, after=4)
    document.save(str(target))


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


def _pdf_info(path: Path, *, scheme: bool) -> dict:
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
                        if bbox[2] > width - 24:
                            right.append({"page": index + 1,
                                          "text": span.get("text", "")[:50]})
                        if bbox[3] > height - 24:
                            bottom.append({"page": index + 1,
                                           "text": span.get("text", "")[:50]})
        return {
            "path": str(path),
            "pages": len(pdf),
            "page1_images": len(pdf[0].get_images(full=True)) if len(pdf) else 0,
            "images_total": sum(len(page.get_images(full=True)) for page in pdf),
            "text": text,
            "right_overflow": right,
            "bottom_overflow": bottom,
            "part_a": ("PART A — MARKING GUIDE" if scheme
                       else "PART A (80 MARKS)") in text,
            "part_b": ("PART B — MARKING GUIDE" if scheme
                       else "PART B (20 MARKS)") in text,
        }


def _word_version() -> str:
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command",
             "(New-Object -ComObject Word.Application).Version"],
            capture_output=True, text=True, timeout=30)
        return result.stdout.strip()
    except Exception:
        return ""


def assemble(seed: int, *, force: bool = False) -> dict:
    plan = pure_guard.validate_plan_file(PLANS / f"seed_{seed:02d}.json")
    config_data = pure_config.ensure()
    answers = _load(ANSWERS, {}).get("by_qid", {})
    assets = {path.stem: _load(path, {}) for path in ASSETS.glob("*.json")}
    out = OUT / f"seed_{seed:02d}"
    out.mkdir(parents=True, exist_ok=True)
    paper_docx = out / "paper.docx"
    scheme_docx = out / "scheme.docx"
    paper_pdf = out / "paper.pdf"
    scheme_pdf = out / "scheme.pdf"
    mapping = build_paper(seed, plan, assets, config_data, paper_docx)
    build_scheme(seed, plan, answers, scheme_docx)
    paper_pages = export_pdf(paper_docx, paper_pdf)
    _patch_page_count(paper_docx, paper_pages, "paper")
    paper_pages = export_pdf(paper_docx, paper_pdf)
    scheme_pages = export_pdf(scheme_docx, scheme_pdf)
    _patch_page_count(scheme_docx, scheme_pages, "scheme")
    scheme_pages = export_pdf(scheme_docx, scheme_pdf)

    paper_info = _pdf_info(paper_pdf, scheme=False)
    scheme_info = _pdf_info(scheme_pdf, scheme=True)
    paper_text = paper_info.pop("text")
    scheme_text = scheme_info.pop("text")
    qa = {
        "subject": "CSC429",
        "seed": seed,
        "paper": paper_info,
        "scheme": scheme_info,
        "problems": [],
        "warnings": [],
    }
    if not paper_info["part_a"] or not paper_info["part_b"]:
        qa["problems"].append("paper part headings missing")
    if not scheme_info["part_a"] or not scheme_info["part_b"]:
        qa["problems"].append("scheme part headings missing")
    for slot in plan["slots"]:
        number = _display_question_number(slot["slot"])
        if f"QUESTION {number}" not in paper_text:
            qa["problems"].append(f"missing paper heading QUESTION {number}")
        if f"QUESTION {number}" not in scheme_text:
            qa["problems"].append(f"missing scheme heading QUESTION {number}")
    expected_images = sum(
        1 for slot in plan["slots"]
        for aid in _load(QUESTIONS / f"{slot['question_id']}.json", {}).get(
            "assets", [])
        if assets.get(aid, {}).get("treatment") != "native_table")
    if paper_info["page1_images"] < 1:
        qa["problems"].append("paper crest missing")
    if paper_info.get("images_total", 0) < expected_images:
        qa["problems"].append("paper is missing asset images")
    if scheme_info["page1_images"] < 1:
        qa["problems"].append("scheme crest missing")
    if paper_info["pages"] > 30 or scheme_info["pages"] > 30:
        qa["problems"].append("page overflow")
    if paper_info["right_overflow"] or scheme_info["right_overflow"]:
        qa["problems"].append("right overflow")
    if paper_info["bottom_overflow"] or scheme_info["bottom_overflow"]:
        qa["problems"].append("bottom overflow")
    # Every rewritten reference in the paper must have a caption.
    captions = set()
    for slot in plan["slots"]:
        q = _load(QUESTIONS / f"{slot['question_id']}.json", {})
        for aid in q.get("assets") or []:
            new = mapping.get(q["id"], {}).get("labels", {}).get(
                assets.get(aid, {}).get("label"))
            if new:
                captions.add(new.lower())
    for match in REF_RE.finditer(paper_text):
        ref = f"{match.group(1).title()} {int(match.group(2))}".lower()
        if ref not in captions:
            qa["problems"].append(f"reference without caption: {ref}")
    # The scheme must not print the question body.
    for slot in plan["slots"]:
        q = _load(QUESTIONS / f"{slot['question_id']}.json", {})
        body = " ".join(
            q.get("native_text_blocks", [{}])[0].get("text", "").split())
        if len(body) > 80 and body[:80].lower() in scheme_text.lower():
            qa["problems"].append(f"scheme prints question body: {q['id']}")
    rejected = _load(TRACKING / "rejected_registry.json", {})
    rejected_files = set(rejected.get("files", {}))
    for path in (paper_docx, paper_pdf, scheme_docx, scheme_pdf):
        if _sha256(path) in rejected_files:
            qa["problems"].append(f"generated file matches rejected registry: {path.name}")
    scan = forbidden.scan([paper_docx, paper_pdf, scheme_docx, scheme_pdf],
                          "CSC429")
    if scan["hits"]:
        qa["problems"].append("forbidden tokens")
    qa["forbidden_hits"] = scan["hits"]
    qa["expected_images"] = expected_images
    qa["word_version"] = _word_version()
    qa["mapping"] = mapping
    (out / "qa.json").write_text(
        json.dumps(qa, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if qa["problems"]:
        raise RuntimeError(
            f"CSC429 seed {seed} QA failed: " + "; ".join(qa["problems"][:6]))
    meta = {
        "subject": "CSC429",
        "seed": seed,
        "type": "D",
        "strategy": "pure_extraction",
        "publication": False,
        "paper_pages": paper_info["pages"],
        "scheme_pages": scheme_info["pages"],
        "source_papers": sorted({slot["source_paper"]
                                 for slot in plan["slots"]}),
        "questions": [slot["question_id"] for slot in plan["slots"]],
        "files": {
            "paper_docx": str(paper_docx),
            "paper_pdf": str(paper_pdf),
            "scheme_docx": str(scheme_docx),
            "scheme_pdf": str(scheme_pdf),
        },
        "word_version": qa["word_version"],
        "cost_usd": 0.0,
    }
    (out / "meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "seed": seed,
        "paper_pages": paper_info["pages"],
        "scheme_pages": scheme_info["pages"],
        "problems": qa["problems"],
        "path": str(out),
    }


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", default="1-3")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if "-" in args.seeds:
        a, b = args.seeds.split("-")
        seeds = list(range(int(a), int(b) + 1))
    else:
        seeds = [int(value) for value in args.seeds.split(",")]
    for seed in seeds:
        print(json.dumps(assemble(seed, force=args.force),
                         indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
