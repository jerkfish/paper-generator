"""V5 assembly for MAT406 seeds 1-3.

Eight questions per seed in the current Part A / Part B role order:
A1 coordinate geometry, A2 trigonometry, A3 vectors, A4 matrices;
B1 coordinate geometry/circles, B2 trigonometry, B3 vectors,
B4 matrices/systems.

The assembler carries each question's printed marks and targets 100 marks.
No question repeats inside a seed; a question is reused at most four times
across the Library.  Seeds prefer distinct source papers.

Run:
    uv run python -m src.subjects.mat406.assemble_v5 --seeds 1-3
"""
from __future__ import annotations

import argparse
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
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt

from src import config
from src.assemble.build_docx_paper import export_pdf
from src.bank.store import BankStore, load_json, save_json
from src.subjects.mat133.render_v5 import (
    _add_rich_text,
    _marks_line,
    _plain_math,
    _para,
    _set_run_font,
)
from src.subjects.mat406.papers import SUBJECT

TRACKING = config.TRACKING_DIR / "mat406" / "v2"
BANK = TRACKING / "bank"
PAPER_TEMPLATE = config.subject_reference_dir("MAT406") / "MAT406 TEMPLATE.docx"
SCHEME_TEMPLATE = (config.subject_reference_dir("MAT406") /
                   "scheme-template-fix.docx")
OUT = config.PROJECT_ROOT / "outputs" / "review" / "mat406_v2" / "seeds"
MATH_CACHE = OUT / "_math"
ROLES = ("A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4")
PART_A = ROLES[:4]
PART_B = ROLES[4:]
REUSE_CAP = 4
TARGET_MARKS = 100
MIN_DISTINCT_PAPERS = 6
CURRENT_PAPERS = {"MAT406-2026-FEB", "MAT406-2025-JUL"}

POOLS = {
    "A1": ["MAT406-2025-JUL-Q1", "MAT406-2026-FEB-Q1",
           "MAT406-2024-JUL-Q1", "MAT406-2024-JAN-Q1",
           "MAT406-2025-FEB-Q1", "MAT406-2022-FEB-Q4",
           "MAT406-2023-FEB-Q4", "MAT406-2023-JUL-Q4"],
    "A2": ["MAT406-2025-JUL-Q2", "MAT406-2026-FEB-Q2",
           "MAT406-2024-JUL-Q3", "MAT406-2024-JAN-Q3",
           "MAT406-2025-FEB-Q3", "MAT406-2023-FEB-Q5",
           "MAT406-2023-JUL-Q5", "MAT406-2021-JUL-Q3"],
    "A3": ["MAT406-2025-JUL-Q3", "MAT406-2026-FEB-Q3",
           "MAT406-2024-JUL-Q4", "MAT406-2024-JAN-Q4",
           "MAT406-2022-FEB-Q7", "MAT406-2021-JUL-Q5",
           "MAT406-2025-FEB-Q4"],
    "A4": ["MAT406-2025-JUL-Q4", "MAT406-2026-FEB-Q4",
           "MAT406-2024-JUL-Q5", "MAT406-2024-JAN-Q5",
           "MAT406-2022-FEB-Q6", "MAT406-2021-JUL-Q4",
           "MAT406-2023-FEB-Q6", "MAT406-2023-JUL-Q6",
           "MAT406-2025-FEB-Q5"],
    "B1": ["MAT406-2025-JUL-Q1-2", "MAT406-2026-FEB-Q1-2",
           "MAT406-2024-JUL-Q2", "MAT406-2024-JAN-Q2",
           "MAT406-2025-FEB-Q2", "MAT406-2023-FEB-Q4",
           "MAT406-2022-FEB-Q4", "MAT406-2021-JUL-Q2"],
    "B2": ["MAT406-2025-JUL-Q2-2", "MAT406-2026-FEB-Q2-2",
           "MAT406-2024-JUL-Q3", "MAT406-2024-JAN-Q3",
           "MAT406-2025-FEB-Q3", "MAT406-2023-FEB-Q5",
           "MAT406-2021-JUL-Q3", "MAT406-2022-FEB-Q5"],
    "B3": ["MAT406-2025-JUL-Q3-2", "MAT406-2026-FEB-Q3-2",
           "MAT406-2024-JUL-Q4", "MAT406-2024-JAN-Q4",
           "MAT406-2022-FEB-Q7", "MAT406-2021-JUL-Q5",
           "MAT406-2025-FEB-Q4"],
    "B4": ["MAT406-2025-JUL-Q4-2", "MAT406-2026-FEB-Q4-2",
           "MAT406-2024-JUL-Q6", "MAT406-2024-JAN-Q6",
           "MAT406-2023-FEB-Q6", "MAT406-2023-JUL-Q6",
           "MAT406-2022-FEB-Q3", "MAT406-2021-JUL-Q4",
           "MAT406-2025-FEB-Q6"],
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
    for required in ("FOUNDATION", "MATHEMATICS", "MAT406", "HOURS"):
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
    p.add_run().add_picture(str(path), width=Cm(6.5))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_before = Pt(6)
    cap.paragraph_format.space_after = Pt(12)
    cap.paragraph_format.keep_together = True
    label = str(asset.get("label") or asset.get("caption") or f"Figure {number}")
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


def _add_question(doc, question: dict, number: int,
                  cache: Path) -> None:
    start = len(doc.paragraphs)
    heading = doc.add_paragraph()
    heading.paragraph_format.space_before = Pt(8)
    heading.paragraph_format.space_after = Pt(2)
    heading.paragraph_format.keep_with_next = True
    run = heading.add_run(f"QUESTION {number}")
    _set_run_font(run, 11, bold=True)
    if question.get("stem"):
        stem = re.sub(r"\(\s*\d{1,3}\s*marks?\s*\)", "",
                      _prep_text(question["stem"]), flags=re.I)
        _para(doc, stem, cache=cache, key=question["id"], keep=True)
    parts = question.get("parts") or []
    assets = list(question.get("_assets") or [])
    by_part: dict[int, list[dict]] = {}
    for asset in assets:
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
        text = re.sub(r"\(\s*\d{1,3}\s*marks?\s*\)", "",
                      _prep_text(part.get("text") or ""), flags=re.I)
        part["text"] = text.strip()
        _add_part_text_together(doc, part, cache, question["id"],
                                str(part.get("label") or ""),
                                keep_next=False)
        for figure, asset in enumerate(by_part.get(index, []), start=1):
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
        if part[0] == "B":
            # Start Part B on a new page without adding a separate break
            # paragraph, which can leave an empty page when Part A fills its
            # last page exactly.
            title.paragraph_format.page_break_before = True
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
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(f"{label}) ")
        _set_run_font(run, 10, bold=True)
        text = _prep_text(str(sub.get("answer") or "No answer."))
        _add_rich_text(p, text, cache, question["id"])
        _marks_line(doc, int(part.get("marks") or 0))
        for line in sub.get("working") or []:
            wp = doc.add_paragraph()
            wp.paragraph_format.left_indent = Cm(0.5)
            wp.paragraph_format.space_before = Pt(0)
            wp.paragraph_format.space_after = Pt(0)
            _add_rich_text(wp, _prep_text(str(line)), cache, question["id"], size=9.5)
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
    if len(slots) != 8:
        problems.append(f"expected 8 slots, found {len(slots)}")
    if len({row["question_id"] for row in slots}) != len(slots):
        problems.append("question repeated inside the seed")
    if len({row["source_paper"] for row in slots}) < MIN_DISTINCT_PAPERS:
        problems.append("fewer than six distinct source papers")
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
        if xml.count("QUESTION ") < 8:
            problems.append("paper has fewer than 8 QUESTION headings")
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
