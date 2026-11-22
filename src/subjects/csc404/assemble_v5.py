"""V5 assembly for CSC404 seeds 1-3.

Six questions per seed in the current Part A / Part B role order:
A1 pointers/functions, A2 arrays/2D arrays, A3 arrays/functions,
A4 structs/file I/O; B1 file I/O/pointers/structs, B2 functions/structs/arrays.

The assembler carries each question's printed marks and targets 100 marks.
No question repeats inside a seed; a question is reused at most four times
across the Library.  Seeds prefer distinct source papers.

Run:
    uv run python -m src.subjects.csc404.assemble_v5 --seeds 1-3
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import docx
import pymupdf
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt

from src import config
from src.assemble.build_docx_paper import export_pdf
from src.bank.store import BankStore, load_json, save_json
from src.subjects.mat133.render_v5 import (
    MARKS_AT_END_RE,
    _add_rich_text,
    _marks_line,
    _plain_math,
    _para,
    _set_run_font,
)
SUBJECT = "CSC404"

TRACKING = config.TRACKING_DIR / "csc404"
BANK = TRACKING / "bank"
PAPER_TEMPLATE = config.subject_reference_dir("CSC404") / "CSC404 TEMPLATE.docx"
SCHEME_TEMPLATE = (config.subject_reference_dir("CSC404") /
                   "CSC404 SCHEME.docx")
OUT = config.PROJECT_ROOT / "outputs" / "review" / "csc404_v2" / "seeds"
MATH_CACHE = OUT / "_math"
ROLES = ("A1", "A2", "A3", "A4", "B1", "B2")
PART_A = ROLES[:4]
PART_B = ROLES[4:]
REUSE_CAP = 4
TARGET_MARKS = 100
MIN_DISTINCT_PAPERS = 4
CURRENT_PAPERS = {"CSC404-2026-FEB", "CSC404-2025-JUL"}

PAPERS = ("CSC404-2026-FEB", "CSC404-2025-JUL", "CSC404-2025-FEB",
          "CSC404-2024-JUL", "CSC404-2023-FEB")
ROLE_SUFFIX = {
    "A1": "Q1",
    "A2": "Q2",
    "A3": "Q3",
    "A4": "Q4",
    "B1": "Q1-2",
    "B2": "Q2-2",
}
POOLS = {
    role: [f"{paper}-{ROLE_SUFFIX[role]}" for paper in PAPERS]
    for role in ROLES
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _load(path: Path, default=None):
    return load_json(path, default if default is not None else {})


def _questions() -> dict[str, dict]:
    store = BankStore(BANK)
    assets = {str(row["id"]): row for row in store.assets()}
    answers = store.answers_by_question()
    rows = {}
    for question in store.questions():
        if question.get("status") != "approved":
            continue
        question = dict(question)
        question["_assets"] = [assets[aid] for aid in question.get("assets") or []
                               if aid in assets and assets[aid].get("verdict") == "approved"]
        question["_answer"] = answers.get(question["id"])
        rows[question["id"]] = question
    return rows


def build_plans(seed_count: int = 3) -> list[dict]:
    questions = _questions()
    uses: Counter[str] = Counter()
    paper_uses: Counter[str] = Counter()
    plans = []
    for seed in range(1, seed_count + 1):
        best: list[tuple] = []

        def search(index: int, chosen: list[tuple[str, str]], total: int,
                   papers: set[str]) -> None:
            if total > TARGET_MARKS:
                return
            if index == len(ROLES):
                if total != TARGET_MARKS or len(papers) < MIN_DISTINCT_PAPERS:
                    return
                score = (
                    len(papers),
                    -sum(uses[qid] for _, qid in chosen),
                    tuple(qid for _, qid in chosen),
                )
                if not best or score > best[0][0]:
                    best[:] = [(score, list(chosen))]
                return
            role = ROLES[index]
            for qid in sorted(
                    POOLS[role],
                    key=lambda value: (
                        uses[value],
                        paper_uses[questions[value]["source_paper"]],
                        0 if questions[value]["source_paper"] in CURRENT_PAPERS else 1,
                        value,
                    )):
                question = questions.get(qid)
                if question is None:
                    continue
                if uses[qid] >= REUSE_CAP:
                    continue
                if any(qid == chosen_id for _, chosen_id in chosen):
                    continue
                if not (question.get("_answer") or {}).get("usable"):
                    continue
                search(index + 1, chosen + [(role, qid)],
                       total + int(question.get("marks") or 0),
                       papers | {str(question["source_paper"])})

        search(0, [], 0, set())
        if not best:
            break
        chosen = best[0][1]
        slots = []
        for role, qid in chosen:
            question = questions[qid]
            uses[qid] += 1
            paper_uses[str(question["source_paper"])] += 1
            slots.append({
                "slot": role,
                "question_id": qid,
                "marks": int(question.get("marks") or 0),
                "source_paper": question["source_paper"],
                "topic_tags": question.get("topic_tags") or [],
            })
        plans.append({
            "seed": seed,
            "slots": slots,
            "total_marks": TARGET_MARKS,
            "distinct_papers": len({slot["source_paper"] for slot in slots}),
            "reuse_cap": REUSE_CAP,
        })
    return plans


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
    for child in children[keep_until + 1:]:
        if child.tag == qn("w:sectPr"):
            continue
        body.remove(child)


def _replace_xml_text(path: Path, replacements: dict[str, str]) -> None:
    with zipfile.ZipFile(path) as source:
        items = [(info, source.read(info.filename))
                 for info in source.infolist()]
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as target:
        for info, data in items:
            if info.filename.startswith("word/") and info.filename.endswith(
                    ".xml"):
                text = data.decode("utf-8")
                for old, new in replacements.items():
                    text = text.replace(old, new)
                data = text.encode("utf-8")
            target.writestr(info, data)


def _scheme_document() -> docx.Document:
    """Use the owner's manually fixed MAT406 marking-scheme cover.

    The supplied scheme-template-fix.docx already has the correct crest,
    course, code, month, duration and notes.  Copy it through without
    re-patching so the manual layout is preserved.
    """
    if not SCHEME_TEMPLATE.is_file():
        raise SystemExit(f"fixed scheme template not found: {SCHEME_TEMPLATE}")
    with zipfile.ZipFile(SCHEME_TEMPLATE) as source:
        xml = source.read("word/document.xml").decode("utf-8")
        media = [name for name in source.namelist()
                 if name.startswith("word/media/")]
    for required in ("PROGRAMMING", "CSC404", "MARKING SCHEME", "HOURS"):
        if required not in xml:
            raise SystemExit(
                f"fixed scheme template is missing cover text: {required}")
    for forbidden in ("CSC662", "COMPUTER", "SECURITY"):
        if forbidden in xml:
            raise SystemExit(
                f"fixed scheme template still has old course text: {forbidden}")
    if not media:
        raise SystemExit("fixed scheme template has no crest image")
    document = docx.Document(str(SCHEME_TEMPLATE))
    # The section break leaves an empty paragraph at the top of section 2.
    # Drop it so the first scheme heading starts at the top margin.
    body = document.element.body
    children = list(body.iterchildren())
    for index, child in enumerate(children[:-1]):
        if child.tag != qn("w:p"):
            continue
        ppr = child.find(qn("w:pPr"))
        if ppr is None or ppr.find(qn("w:sectPr")) is None:
            continue
        following = children[index + 1]
        if following.tag != qn("w:p"):
            break
        text_nodes = list(following.iter(qn("w:t")))
        if not any((node.text or "").strip() for node in text_nodes):
            body.remove(following)
        break
    return document


def _add_picture(doc, asset: dict, number: int) -> None:
    path = Path(str(asset.get("path") or ""))
    if not path.is_file():
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(path), width=Cm(12.5))
    label = str(asset.get("label") or asset.get("caption")
                or f"Figure {number}")
    if label.lower() in " ".join(_asset_visible_lines(asset)).lower():
        return
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_before = Pt(6)
    cap.paragraph_format.space_after = Pt(12)
    cap.paragraph_format.keep_together = True
    run = cap.add_run(label)
    _set_run_font(run, 8.5, italic=True)


def _prep_text(text: str) -> str:
    """Make printed LaTeX safer for the DOCX renderer."""
    value = str(text or "")
    value = re.sub(r"\\hat\{\\imath\}", lambda _m: r"\boldsymbol{i}", value)
    value = re.sub(r"\\hat\{\\jmath\}", lambda _m: r"\boldsymbol{j}", value)

    # latex2mathml cannot convert \vec / \overrightarrow, which made the
    # renderer fall back to plain text and drop both the arrow and any
    # \langle...\rangle delimiters in the same expression.  Bold italic
    # letters are the standard printed alternative for vectors and keep the
    # expression in OMML.
    def bold_vector(match: re.Match) -> str:
        letters = re.sub(r"[^A-Za-z]", "", match.group(1))
        return r"\boldsymbol{" + letters + "}"

    value = re.sub(
        r"\\(?:vec|overrightarrow)\s*\{\s*"
        r"(?:\\(?:mathrm|mathbf|mathsf)\s*\{\s*)?"
        r"([A-Za-z\s]+)"
        r"(?:\s*\})?\s*\}",
        bold_vector, value)

    def matrix_span(match: re.Match) -> str:
        inner = match.group(1)

        def row_matrix(inner_match: re.Match) -> str:
            body = (inner_match.group(1)
                    .replace("\\\\", " ; ")
                    .replace("&", " "))
            return "[" + " ".join(body.split()) + "]"

        inner = re.sub(r"\\begin\{bmatrix\}(.*?)\\end\{bmatrix\}",
                       row_matrix, inner, flags=re.S)
        return _plain_math(inner)

    value = re.sub(
        r"\$([^$]*\\begin\{bmatrix\}.*?\\end\{bmatrix\}[^$]*)\$",
        matrix_span, value, flags=re.S)
    return value


_MARKS_AT_END_RE = re.compile(r"\((\d+)\s*marks?\)\s*$", re.I)
_EQ_LINE_RE = re.compile(r"^\$([^$]+)\$[.,;]?$")


def _is_equation_line(line: str) -> bool:
    """True for a standalone printed equation/inequality line."""
    match = _EQ_LINE_RE.match(line.strip())
    if not match:
        return False
    body = match.group(1)
    return bool(re.search(
        r"(?<![<>])=(?!=)|\\leq|\\geq|\\le\\b|\\ge\\b|[<>]", body))


def _add_part_text(doc, part: dict, cache: Path, key: str,
                   label: str, keep_next: bool) -> None:
    """Render a part, giving printed equation blocks breathing room."""
    text = str(part.get("text") or "")
    lines = text.split("\n")
    flags = [_is_equation_line(line) for line in lines]
    before = [0] * len(lines)
    after = [0] * len(lines)
    index = 0
    while index < len(lines):
        if not flags[index]:
            index += 1
            continue
        end = index
        while end + 1 < len(lines) and flags[end + 1]:
            end += 1
        if end - index + 1 >= 2:
            before[index] = 10
            after[end] = 10
        index = end + 1

    found_marks = False
    for index, line in enumerate(lines):
        match = _MARKS_AT_END_RE.search(line)
        body = line[:match.start()].rstrip() if match else line
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.left_indent = Inches(0.28)
        pf.first_line_indent = Inches(-0.28 if index == 0 else 0)
        pf.space_before = Pt(4 if index == 0 else before[index])
        pf.space_after = Pt(after[index])
        pf.line_spacing = 1.05
        pf.keep_with_next = keep_next or bool(match)
        if index == 0 and label:
            run = p.add_run(f"{label})")
            _set_run_font(run, 10.5, bold=True)
            run = p.add_run("\t")
            _set_run_font(run, 10.5)
        if body:
            _add_rich_text(p, body, cache, key)
        if match:
            _marks_line(doc, int(match.group(1)))
            found_marks = True
    if not found_marks and part.get("marks"):
        _marks_line(doc, int(part["marks"]))


def _add_part_text_together(doc, part: dict, cache: Path, key: str,
                            label: str, keep_next: bool) -> None:
    """Render a part and keep its whole printed block on one page."""
    start = len(doc.paragraphs)
    _add_part_text(doc, part, cache, key, label, keep_next)
    added = doc.paragraphs[start:]
    for index, paragraph in enumerate(added):
        paragraph.paragraph_format.keep_together = True
        paragraph.paragraph_format.keep_with_next = index < len(added) - 1


def _keep_question_together(doc, start: int) -> None:
    """Keep a question heading and all its parts on the same page."""
    added = doc.paragraphs[start:]
    for index, paragraph in enumerate(added):
        paragraph.paragraph_format.keep_together = True
        paragraph.paragraph_format.keep_with_next = index < len(added) - 1


def _asset_visible_lines(asset: dict) -> set[str]:
    name = str(asset.get("owner_recreation_html") or "")
    if not name:
        return set()
    path = BANK / "review" / "owner_recreations" / name
    if not path.is_file():
        return set()
    raw = path.read_text(encoding="utf-8")
    raw = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    raw = re.sub(r"(?i)</t[dh]>", " | ", raw)
    raw = re.sub(r"(?i)</tr>", "\n", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    text = html.unescape(raw)
    return {" ".join(line.split()) for line in text.splitlines()
            if line.strip()}


def _stem_without_asset_duplicates(stem: str,
                                   assets: list[dict]) -> str:
    """Drop stem lines that the recreation image already prints."""
    duplicate = set()
    for asset in assets:
        duplicate |= _asset_visible_lines(asset)
    kept = []
    for line in str(stem or "").splitlines():
        normalised = " ".join(line.split())
        if not normalised:
            kept.append(line)
            continue
        if normalised in duplicate:
            continue
        if normalised.lower().endswith("- notepad"):
            continue
        if normalised.lower() == "file edit format view help":
            continue
        kept.append(line)
    return "\n".join(kept).strip()


CODE_RE = re.compile(
    r"(#include|[;{}]|\bcout\b|\bcin\b|\bint\s+\w|\bfloat\s+\w|"
    r"\bdouble\s+\w|\bchar\s+\w|\bstring\s+\w|\bvoid\s+\w|"
    r"\bstruct\s+\w|\bfor\s*\(|\bwhile\s*\(|\bif\s*\(|\breturn\b|"
    r"\busing\s+namespace\b|^\s{4,})")


def _looks_like_code(line: str) -> bool:
    return bool(CODE_RE.search(line))


BULLET_RE = re.compile(r"^\s*(?:[•\-–○]|o\s)\s*")
SUBHEAD_RE = re.compile(r"^\s*(?:[a-h][.)]|\(?[ivx]{1,4}[.)])\s+", re.I)
SAMPLE_RE = re.compile(r"^\s*sample output\s*:?\s*$", re.I)
CODE_START_RE = re.compile(
    r"^\s*(?:#include|using\s+namespace|int\s+\w|float\s+\w|"
    r"double\s+\w|char\s+\w|string\s+\w|void\s+\w|struct\s+\w|"
    r"class\s+\w|for\s*\(|while\s*\(|if\s*\(|else\b|return\b|"
    r"cout\b|cin\b|[{}\[\]])")


def _is_code_line(line: str) -> bool:
    text = line.strip()
    if not text or BULLET_RE.match(line) or SUBHEAD_RE.match(line):
        return False
    if SAMPLE_RE.match(text):
        return False
    if text.endswith(":") and not re.search(r"[;{}]", text):
        return False
    return bool(CODE_START_RE.match(line)) or bool(CODE_RE.search(line))


def _is_output_line(line: str) -> bool:
    text = line.strip()
    if not text:
        return True
    return not (BULLET_RE.match(line) or SUBHEAD_RE.match(line)
                or MARKS_AT_END_RE.search(text))


def _code_segments(lines: list[str]) -> list[tuple[str, list[str]]]:
    segments: list[tuple[str, list[str]]] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        text = line.strip()
        if not text:
            index += 1
            continue
        if MARKS_AT_END_RE.search(text):
            segments.append(("marks", [line]))
            index += 1
            continue
        if SAMPLE_RE.match(text):
            block = ["Sample Output:"]
            index += 1
            while index < len(lines):
                candidate = lines[index]
                if not candidate.strip():
                    look = index + 1
                    while look < len(lines) and not lines[look].strip():
                        look += 1
                    if look < len(lines) and _is_output_line(lines[look]):
                        block.append("")
                        index += 1
                        continue
                    break
                if not _is_output_line(candidate):
                    break
                block.append(candidate)
                index += 1
            segments.append(("code", block))
            continue
        if BULLET_RE.match(line):
            block = []
            while index < len(lines) and lines[index].strip() \
                    and BULLET_RE.match(lines[index]):
                block.append(lines[index])
                index += 1
            segments.append(("bullets", block))
            continue
        if SUBHEAD_RE.match(line):
            segments.append(("subhead", [line]))
            index += 1
            continue
        if _is_code_line(line):
            block = []
            while index < len(lines):
                candidate = lines[index]
                if not candidate.strip():
                    look = index + 1
                    while look < len(lines) and not lines[look].strip():
                        look += 1
                    if look < len(lines) and _is_code_line(lines[look]) \
                            and not SAMPLE_RE.match(lines[look].strip()):
                        block.append("")
                        index += 1
                        continue
                    break
                if not _is_code_line(candidate):
                    break
                block.append(candidate)
                index += 1
            segments.append(("code", block))
            continue
        segments.append(("prose", [line]))
        index += 1
    return segments


def _shade_and_border(paragraph) -> None:
    ppr = paragraph._p.get_or_add_pPr()
    shading = OxmlElement("w:shd")
    shading.set(qn("w:val"), "clear")
    shading.set(qn("w:color"), "auto")
    shading.set(qn("w:fill"), "F2F2F2")
    ppr.append(shading)
    borders = OxmlElement("w:pBdr")
    for edge in ("top", "left", "bottom", "right"):
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "4")
        element.set(qn("w:space"), "4")
        element.set(qn("w:color"), "9E9E9E")
        borders.append(element)
    ppr.append(borders)


def _add_code_block(doc, lines: list[str], *, keep_next: bool = False) -> None:
    paragraph = doc.add_paragraph()
    pf = paragraph.paragraph_format
    pf.left_indent = Inches(0.38)
    pf.right_indent = Inches(0.1)
    pf.space_before = Pt(6)
    pf.space_after = Pt(6)
    pf.line_spacing = 1.0
    pf.keep_together = True
    pf.keep_with_next = keep_next
    _shade_and_border(paragraph)
    run = paragraph.add_run()
    for index, line in enumerate(lines):
        if index:
            run.add_break()
        run.add_text(line)
    _set_run_font(run, 9)
    run.font.name = "Consolas"
    rpr = run._element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = rpr.makeelement(qn("w:rFonts"), {})
        rpr.insert(0, fonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs"):
        fonts.set(qn(attr), "Consolas")


def _add_part_text_code(doc, part: dict, cache: Path, key: str,
                        label: str, keep_next: bool) -> None:
    """Render a CSC404 part with code boxes, bullets and subheadings."""
    text = str(part.get("text") or "")
    lines = text.splitlines()
    segments = _code_segments(lines)
    first_block = True
    found_marks = False
    for kind, block in segments:
        if kind == "marks":
            _marks_line(doc, int(MARKS_AT_END_RE.search(block[0]).group(1)))
            found_marks = True
            continue
        if kind == "code":
            if first_block:
                # A part that opens with code still gets its printed label.
                if label:
                    p = doc.add_paragraph()
                    p.paragraph_format.space_before = Pt(4)
                    p.paragraph_format.space_after = Pt(0)
                    run = p.add_run(f"{label})")
                    _set_run_font(run, 10.5, bold=True)
                first_block = False
            _add_code_block(doc, block, keep_next=keep_next)
            continue
        if kind == "bullets":
            for position, line in enumerate(block):
                p = doc.add_paragraph()
                pf = p.paragraph_format
                pf.left_indent = Inches(1.0)
                pf.first_line_indent = Inches(-0.3)
                pf.space_before = Pt(4 if first_block else 0)
                pf.space_after = Pt(0)
                if first_block and position == 0 and label:
                    run = p.add_run(f"{label}) ")
                    _set_run_font(run, 10.5, bold=True)
                _add_rich_text(p, line.strip(), cache, key)
            first_block = False
            continue
        if kind == "subhead":
            p = doc.add_paragraph()
            pf = p.paragraph_format
            pf.left_indent = Inches(0.55)
            pf.space_before = Pt(4)
            pf.space_after = Pt(0)
            if first_block and label:
                run = p.add_run(f"{label}) ")
                _set_run_font(run, 10.5, bold=True)
            _add_rich_text(p, block[0].strip(), cache, key)
            first_block = False
            continue
        for line in block:
            p = doc.add_paragraph()
            pf = p.paragraph_format
            pf.left_indent = Inches(0.28)
            pf.first_line_indent = Inches(-0.28 if first_block else 0)
            pf.space_before = Pt(4 if first_block else 0)
            pf.space_after = Pt(0)
            pf.line_spacing = 1.05
            pf.keep_with_next = keep_next
            if first_block and label:
                run = p.add_run(f"{label})")
                _set_run_font(run, 10.5, bold=True)
                run = p.add_run("\t")
                _set_run_font(run, 10.5)
            _add_rich_text(p, line.strip(), cache, key)
            first_block = False
    if not found_marks and part.get("marks"):
        _marks_line(doc, int(part["marks"]))


def _add_question(doc, question: dict, number: int,
                  cache: Path) -> None:
    start = len(doc.paragraphs)
    heading = doc.add_paragraph()
    heading.paragraph_format.space_before = Pt(8)
    heading.paragraph_format.space_after = Pt(2)
    heading.paragraph_format.keep_with_next = True
    run = heading.add_run(f"QUESTION {number}")
    _set_run_font(run, 11, bold=True)
    parts = question.get("parts") or []
    assets = list(question.get("_assets") or [])
    stem = str(question.get("stem") or "")
    stem_assets = []
    for asset in assets:
        label = str(asset.get("label") or asset.get("caption") or "")
        if label and label.lower() in stem.lower():
            stem_assets.append(asset)
    stem_assets.sort(key=lambda asset: stem.lower().find(
        str(asset.get("label") or "").lower()))
    if stem:
        stem = _stem_without_asset_duplicates(stem, stem_assets)
        stem = re.sub(r"\(\s*\d{1,3}\s*marks?\s*\)", "",
                      _prep_text(stem), flags=re.I)
        _para(doc, stem, cache=cache, key=question["id"], keep=True)
    for figure, asset in enumerate(stem_assets, start=1):
        _add_picture(doc, asset, figure)
    by_part: dict[int, list[dict]] = {}
    for asset in assets:
        if asset in stem_assets:
            continue
        label = str(asset.get("label") or asset.get("caption") or "")
        target = None
        for index, part in enumerate(parts):
            if label and label.lower() in str(part.get("text") or "").lower():
                target = index
                break
        if target is None:
            for index, part in enumerate(parts):
                if "figure" in str(part.get("text") or "").lower():
                    target = index
                    break
        by_part.setdefault(target if target is not None else len(parts) - 1,
                           []).append(asset)
    for index, part in enumerate(parts):
        part = dict(part)
        part_assets = by_part.get(index, [])
        text = _stem_without_asset_duplicates(
            str(part.get("text") or ""), part_assets)
        text = re.sub(r"\(\s*\d{1,3}\s*marks?\s*\)", "",
                      _prep_text(text), flags=re.I)
        part["text"] = text.strip()
        _add_part_text_code(doc, part, cache, question["id"],
                            str(part.get("label") or ""),
                            keep_next=bool(part_assets))
        for figure, asset in enumerate(part_assets, start=1):
            _add_picture(doc, asset, figure)
    _keep_question_together(doc, start)


def build_paper(plan: dict, out_dir: Path) -> Path:
    questions = _questions()
    target = out_dir / "paper.docx"
    document = docx.Document(str(PAPER_TEMPLATE))
    for part in (("A", PART_A), ("B", PART_B)):
        title = document.add_paragraph()
        title.paragraph_format.space_before = Pt(4)
        title.paragraph_format.space_after = Pt(6)
        # Part A starts on the page after the cover; Part B starts a new page.
        title.paragraph_format.page_break_before = True
        title.paragraph_format.keep_with_next = True
        run = title.add_run(f"PART {part[0]}")
        _set_run_font(run, 11, bold=True)
        number = 0
        for role in part[1]:
            slot = next(row for row in plan["slots"] if row["slot"] == role)
            number += 1
            _add_question(document, questions[slot["question_id"]], number,
                          MATH_CACHE)
    document.save(str(target))
    return target


def _add_mono_run(paragraph, text: str, size: float = 9) -> None:
    run = paragraph.add_run(text)
    _set_run_font(run, size)
    run.font.name = "Consolas"
    rpr = run._element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = rpr.makeelement(qn("w:rFonts"), {})
        rpr.insert(0, fonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs"):
        fonts.set(qn(attr), "Consolas")


PROSE_WORDS = re.compile(
    r"\b(?:points?|prints?|sets?|changes?|initiali[sz]ed|assume[sd]?|"
    r"output|means?|because|since|therefore|the|and|is|are|was|were)\b",
    re.I)


def _is_answer_code(line: str) -> bool:
    text = line.strip()
    if not text or PROSE_WORDS.search(text):
        return False
    if re.match(
            r"^(?:#include|using\s+namespace|int\s|float\s|double\s|"
            r"char\s|string\s|void\s|struct\s|class\s|for\s*\(|"
            r"while\s*\(|if\s*\(|return\b|cout\b|cin\b|[{}])", text):
        return True
    return bool(text.endswith(";")
                and re.search(r"[=<>\[\]()+\-*/]", text))


def _add_answer_lines(doc, text: str, cache: Path, key: str,
                      label: str = "", size: float = 9.5) -> None:
    lines = str(text or "").splitlines() or [""]
    index = 0
    first = True
    while index < len(lines):
        line = lines[index]
        if _is_answer_code(line):
            block = []
            while index < len(lines) and _is_answer_code(lines[index]):
                block.append(lines[index])
                index += 1
            _add_code_block(doc, block)
            first = False
            continue
        if line.strip():
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.5)
            p.paragraph_format.space_before = Pt(2 if first else 0)
            p.paragraph_format.space_after = Pt(0)
            if first and label:
                run = p.add_run(f"{label}) ")
                _set_run_font(run, 10, bold=True)
            _add_rich_text(p, _prep_text(line), cache, key, size=size)
            first = False
        index += 1


def _add_scheme_question(doc, question: dict, number: int,
                         cache: Path) -> None:
    heading = doc.add_paragraph()
    heading.paragraph_format.space_before = Pt(8)
    heading.paragraph_format.space_after = Pt(2)
    heading.paragraph_format.keep_with_next = True
    run = heading.add_run(f"QUESTION {number}")
    _set_run_font(run, 11, bold=True)
    source = doc.add_paragraph()
    run = source.add_run(
        f"Source: {question['source_paper']}  |  "
        f"{question.get('marks')} marks  |  model_unofficial")
    _set_run_font(run, 8.5, italic=True)
    answer = question.get("_answer") or {}
    for part in question.get("parts") or []:
        label = str(part.get("label") or "")
        sub = next((row for row in answer.get("subparts") or []
                    if str(row.get("label") or "").lower() == label.lower()),
                   {})
        _add_answer_lines(doc, str(sub.get("answer") or "No answer."),
                          cache, question["id"], label=label)
        _marks_line(doc, int(part.get("marks") or 0))
        for line in sub.get("working") or []:
            _add_answer_lines(doc, str(line), cache, question["id"])
    points = answer.get("marking_points") or []
    if points:
        p = doc.add_paragraph()
        run = p.add_run("Marking points:")
        _set_run_font(run, 9, bold=True)
        for point in points:
            bp = doc.add_paragraph()
            bp.paragraph_format.left_indent = Cm(0.5)
            bp.paragraph_format.space_before = Pt(0)
            bp.paragraph_format.space_after = Pt(0)
            run = bp.add_run("• ")
            _set_run_font(run, 9)
            _add_rich_text(bp, str(point), cache, question["id"], size=9)


def build_scheme(plan: dict, out_dir: Path) -> Path:
    questions = _questions()
    target = out_dir / "scheme.docx"
    document = _scheme_document()
    for part in (("A", PART_A), ("B", PART_B)):
        number = 0
        title = document.add_paragraph()
        if part[0] == "B":
            title.paragraph_format.page_break_before = True
        run = title.add_run(f"PART {part[0]} — MARKING SCHEME")
        _set_run_font(run, 11, bold=True)
        for role in part[1]:
            slot = next(row for row in plan["slots"] if row["slot"] == role)
            number += 1
            _add_scheme_question(document, questions[slot["question_id"]],
                                 number, MATH_CACHE)
    document.save(str(target))
    return target


def _set_page_count(path: Path, marker: str, pages: int) -> bool:
    document = docx.Document(str(path))
    changed = False
    for paragraph in document.paragraphs:
        if marker in paragraph.text:
            paragraph.text = f"{marker} {pages} printed pages"
            changed = True
            break
    if changed:
        document.save(str(path))
    return changed


def qa_seed(plan: dict, out_dir: Path) -> dict:
    questions = _questions()
    problems = []
    slots = plan.get("slots") or []
    if len(slots) != 6:
        problems.append(f"expected 6 slots, found {len(slots)}")
    if len({row["question_id"] for row in slots}) != len(slots):
        problems.append("question repeated inside the seed")
    if len({row["source_paper"] for row in slots}) < MIN_DISTINCT_PAPERS:
        problems.append("fewer than four distinct source papers")
    total = sum(int(row.get("marks") or 0) for row in slots)
    if total != TARGET_MARKS:
        problems.append(f"marks total {total}, expected {TARGET_MARKS}")
    for row in slots:
        question = questions.get(row["question_id"])
        if question is None:
            problems.append(f"{row['question_id']} is missing")
            continue
        if question.get("status") != "approved":
            problems.append(f"{row['question_id']} is not approved")
        if not (question.get("_answer") or {}).get("usable"):
            problems.append(f"{row['question_id']} has no usable answer")
        if int(question.get("marks") or 0) != int(row["marks"]):
            problems.append(f"{row['question_id']} mark mismatch")
    paper = out_dir / "paper.docx"
    scheme = out_dir / "scheme.docx"
    for path in (paper, scheme):
        if not path.is_file():
            problems.append(f"{path.name} is missing")
    if paper.is_file():
        xml = docx.Document(str(paper)).element.xml
        if xml.count("QUESTION ") < 6:
            problems.append("paper has fewer than 6 QUESTION headings")
    if scheme.is_file():
        xml = docx.Document(str(scheme)).element.xml
        if "model_unofficial" not in xml:
            problems.append("scheme lacks the model_unofficial label")
    return {
        "seed": plan["seed"],
        "slots": len(slots),
        "total_marks": total,
        "distinct_papers": len({row["source_paper"] for row in slots}),
        "problems": problems,
    }


def build_seed(seed: int, out_dir: Path | None = None) -> dict:
    plans = build_plans(seed_count=seed)
    if len(plans) < seed:
        raise ValueError(f"only {len(plans)} seeds are feasible")
    plan = plans[seed - 1]
    target = Path(out_dir) if out_dir else OUT / f"seed_{seed:02d}"
    target.mkdir(parents=True, exist_ok=True)
    MATH_CACHE.mkdir(parents=True, exist_ok=True)
    save_json(target / "plan.json", plan)
    paper = build_paper(plan, target)
    scheme = build_scheme(plan, target)
    paper_pdf = target / "paper.pdf"
    scheme_pdf = target / "scheme.pdf"
    export_pdf(paper, paper_pdf)
    paper_pages = len(pymupdf.open(str(paper_pdf)))
    if _set_page_count(paper, "This examination paper consists of",
                       paper_pages):
        export_pdf(paper, paper_pdf)
        paper_pages = len(pymupdf.open(str(paper_pdf)))
    export_pdf(scheme, scheme_pdf)
    scheme_pages = len(pymupdf.open(str(scheme_pdf)))
    if _set_page_count(scheme, "This marking scheme consists of",
                       scheme_pages):
        export_pdf(scheme, scheme_pdf)
        scheme_pages = len(pymupdf.open(str(scheme_pdf)))
    qa = qa_seed(plan, target)
    save_json(target / "qa.json", qa)
    meta = {
        "subject": SUBJECT,
        "seed": seed,
        "mode": "realistic",
        "model": "mat406-v2-role-recycle",
        "cost_usd": 0.0,
        "accepted": len(plan["slots"]),
        "placeholders": 0,
        "total_slots": len(plan["slots"]),
        "total_marks": plan["total_marks"],
        "has_practice_mode": False,
        "has_placeholders": False,
        "created": _now(),
        "year": 2026,
        "topic_marks": {},
        "summary": {"total_marks": plan["total_marks"]},
        "files": {
            "paper_docx": str(paper),
            "paper_pdf": str(paper_pdf),
            "scheme_docx": str(scheme),
            "scheme_pdf": str(scheme_pdf),
        },
    }
    save_json(target / "meta.json", meta)
    save_json(target / "evidence.json", {
        "plan": plan,
        "qa": qa,
        "paper_pages": paper_pages,
        "scheme_pages": scheme_pages,
    })
    return {"seed": seed, "path": str(target), "qa": qa,
            "paper_pages": paper_pages,
            "scheme_pages": scheme_pages}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", default="1-3")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    if "-" in args.seeds:
        first, last = args.seeds.split("-", 1)
        seeds = list(range(int(first), int(last) + 1))
    else:
        seeds = [int(value) for value in args.seeds.split(",")]
    results = [build_seed(seed, args.out) for seed in seeds]
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
