"""Build CSC429 question papers and marking schemes.

Stage 7 builder.  The cover is the owner-approved CSC429 template; the
marking scheme uses the shared UTM standard scheme cover.  No LLM call is
made: the paper comes from the stage-6 deterministic generators.
"""
from __future__ import annotations

import json
import re
import shutil
import time
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

import docx
import pymupdf
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

from src.app.filenames import utc_year
from src.app.jobs import cache_path
from src.assemble.pdf_export import export_pdf
from src.config import subject_reference_dir
from src.subjects.csc429.figures import render_figure
from src.subjects.csc429.generators import generate_paper
from src.subjects.csc429.planner import build_plan
from src.subjects.forbidden import forbidden_tokens

SUBJECT = "CSC429"
PAPER_TEMPLATE = subject_reference_dir(SUBJECT) / "CSC429 TEMPLATE.docx"
SCHEME_TEMPLATE = (subject_reference_dir(SUBJECT)
                   / "CSC429 SCHEME TEMPLATE.docx")
PAPER_COVER_MARKER = "This examination paper consists"
SCHEME_COVER_MARKER = "This marking scheme consists"
BODY_WIDTH_CM = 16.2


def _squash(text: str) -> str:
    return re.sub(r"\s+", "", str(text))


def _set_paragraph_text(paragraph, text: str) -> None:
    """Replace a paragraph's text while preserving its first run style."""
    runs = paragraph.runs
    if not runs:
        paragraph.add_run(text)
        return
    runs[0].text = text
    for run in runs[1:]:
        run.text = ""


def _replace_text_nodes(document, replacements: dict[str, str],
                        exact: dict[str, str] | None = None) -> None:
    roots = []
    for part in document.part.package.iter_parts():
        element = getattr(part, "element", None)
        if element is not None:
            roots.append(element)
    for root in roots:
        for node in root.iter(qn("w:t")):
            if not node.text:
                continue
            value = node.text
            for old, new in replacements.items():
                value = value.replace(old, new)
            if exact:
                value = exact.get(value, value)
            node.text = value


def _patch_paragraph(document, prefix: str, text: str) -> bool:
    for paragraph in document.paragraphs:
        if paragraph.text.strip().startswith(prefix):
            _set_paragraph_text(paragraph, text)
            return True
    return False


def _section_break_index(document) -> int | None:
    for index, paragraph in enumerate(document.paragraphs):
        ppr = paragraph._p.pPr
        if ppr is not None and ppr.find(qn("w:sectPr")) is not None:
            return index
    return None


def _clear_after_section_break(document) -> None:
    cut = _section_break_index(document)
    if cut is None:
        raise RuntimeError("template has no section break")
    for paragraph in list(document.paragraphs)[cut + 1:]:
        paragraph._element.getparent().remove(paragraph._element)


def _add_part_heading(document, title: str, note: str) -> None:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(6)
    paragraph.paragraph_format.space_after = Pt(2)
    run = paragraph.add_run(title)
    run.bold = True
    run.font.size = Pt(12)
    note_paragraph = document.add_paragraph(note)
    note_paragraph.paragraph_format.space_after = Pt(8)


def _add_marks_heading(document, label: str, marks: int) -> None:
    blank = document.add_paragraph()
    blank.paragraph_format.line_spacing = 1.5
    blank.paragraph_format.space_before = Pt(10)
    blank.paragraph_format.space_after = Pt(2)
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.line_spacing = 1.5
    paragraph.paragraph_format.space_before = Pt(10)
    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.paragraph_format.tab_stops.add_tab_stop(
        Cm(BODY_WIDTH_CM), WD_TAB_ALIGNMENT.RIGHT)
    run = paragraph.add_run(label)
    run.bold = True
    paragraph.add_run("\t")
    run = paragraph.add_run(f"({marks} marks)")
    run.bold = True


def _add_figure(document, figure: dict) -> None:
    picture = document.add_paragraph()
    picture.alignment = WD_ALIGN_PARAGRAPH.CENTER
    picture.paragraph_format.line_spacing = 1.5
    picture.paragraph_format.space_before = Pt(4)
    picture.paragraph_format.space_after = Pt(2)
    picture.add_run().add_picture(
        figure["path"], width=Cm(float(figure.get("width_cm", 14.5))))
    caption = document.add_paragraph(figure["caption"])
    caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption.paragraph_format.line_spacing = 1.5
    caption.paragraph_format.space_after = Pt(6)
    run = caption.runs[0]
    run.italic = True
    run.font.size = Pt(9)


def _add_paper_question(document, question: dict) -> None:
    _add_marks_heading(
        document, f"QUESTION {question['number']}", question["marks"])
    stem = document.add_paragraph(question["stem"])
    stem.paragraph_format.line_spacing = 1.5
    stem.paragraph_format.space_after = Pt(4)
    if question.get("figure"):
        _add_figure(document, question["figure"])
    for part in question["parts"]:
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.line_spacing = 1.5
        paragraph.paragraph_format.left_indent = Cm(0.9)
        paragraph.paragraph_format.first_line_indent = Cm(-0.9)
        paragraph.paragraph_format.tab_stops.add_tab_stop(Cm(0.9))
        paragraph.paragraph_format.space_after = Pt(3)
        paragraph.add_run(f"({part['label']})\t")
        paragraph.add_run(part["text"])
        paragraph.add_run(f" ({part['marks']} marks)")


def _add_scheme_question(document, question: dict) -> None:
    _add_marks_heading(
        document, f"QUESTION {question['number']}", question["marks"])
    stem = document.add_paragraph(question["stem"])
    stem.paragraph_format.line_spacing = 1.5
    stem.paragraph_format.space_after = Pt(4)
    if question.get("figure"):
        _add_figure(document, question["figure"])
    for part in question["parts"]:
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.line_spacing = 1.5
        paragraph.paragraph_format.left_indent = Cm(0.9)
        paragraph.paragraph_format.first_line_indent = Cm(-0.9)
        paragraph.paragraph_format.tab_stops.add_tab_stop(Cm(0.9))
        run = paragraph.add_run(f"({part['label']}) ({part['marks']} marks) ")
        run.bold = True
        paragraph.add_run(part["text"])
        answer = document.add_paragraph()
        answer.paragraph_format.line_spacing = 1.5
        answer.paragraph_format.left_indent = Cm(0.9)
        answer.paragraph_format.space_after = Pt(6)
        answer.paragraph_format.keep_together = True
        paragraph.paragraph_format.keep_with_next = True
        answer.add_run("Answer: ").bold = True
        run = answer.add_run(part["answer"])
        if question["generator_id"] == "csc429.assembly":
            run.font.name = "Courier New"


def _build_paper_docx(paper: dict, path: Path) -> None:
    shutil.copy2(PAPER_TEMPLATE, path)
    document = docx.Document(str(path))
    document.styles["Normal"].font.name = "Arial"
    document.styles["Normal"].font.size = Pt(11)
    cover, body = document.sections[0], document.sections[1]
    body.start_type = WD_SECTION.NEW_PAGE
    body.left_margin = cover.left_margin
    body.right_margin = cover.right_margin
    body.top_margin = cover.top_margin
    body.bottom_margin = cover.bottom_margin
    _clear_after_section_break(document)
    part_a = [q for q in paper["questions"] if q["part"] == "A"]
    part_b = [q for q in paper["questions"] if q["part"] == "B"]
    _add_part_heading(document, "PART A (80 MARKS)",
                      "Answer ALL questions in this part.")
    for question in part_a:
        _add_paper_question(document, question)
    document.add_page_break()
    _add_part_heading(document, "PART B (20 MARKS)",
                      "Answer the question in this part.")
    for question in part_b:
        _add_paper_question(document, question)
    document.save(str(path))


def _scheme_notes(paper: dict) -> list[tuple[str, str]]:
    computed = sum(
        1 for q in paper["questions"]
        if q["generator_id"] in {"csc429.data_representation",
                                 "csc429.assembly"})
    descriptive = len(paper["questions"]) - computed
    return [
        ("Computed slots:",
         f"Computed slots: {computed}; descriptive slots: {descriptive}; "
         "placeholders: 0."),
        ("Fingerprint based on 20 unique CSC429 papers",
         "Fingerprint based on 20 unique CSC429 papers; output is "
         f"deterministic for seed {paper['seed']}."),
    ]


def _build_scheme_docx(paper: dict, path: Path) -> None:
    shutil.copy2(SCHEME_TEMPLATE, path)
    document = docx.Document(str(path))
    document.styles["Normal"].font.name = "Arial"
    document.styles["Normal"].font.size = Pt(11)
    _replace_text_nodes(
        document,
        {
            "CSC662": "CSC429",
            "COMPUTER SECURITY": "COMPUTER ORGANIZATION AND ARCHITECTURE",
            "OCTOBER 2026": "NOVEMBER 2026",
            "October 2026": "November 2026",
            "OCT": "NOV",
        },
    )
    for prefix, text in _scheme_notes(paper):
        _patch_paragraph(document, prefix, text)
    document.sections[1].start_type = WD_SECTION.NEW_PAGE
    _clear_after_section_break(document)
    part_a = [q for q in paper["questions"] if q["part"] == "A"]
    part_b = [q for q in paper["questions"] if q["part"] == "B"]
    _add_part_heading(document, "PART A — MARKING SCHEME",
                      "Worked answers and marking points.")
    for question in part_a:
        _add_scheme_question(document, question)
    document.add_page_break()
    _add_part_heading(document, "PART B — MARKING SCHEME",
                      "Worked answers and marking points.")
    for question in part_b:
        _add_scheme_question(document, question)
    document.save(str(path))


def _docx_text(path: Path) -> tuple[str, list[str]]:
    with zipfile.ZipFile(str(path)) as archive:
        names = ["word/document.xml"]
        names.extend(
            name for name in archive.namelist()
            if re.match(r"word/(header|footer)\d*\.xml$", name))
        parts = []
        for name in names:
            root = ET.fromstring(archive.read(name))
            parts.extend(node.text or "" for node in root.iter(qn("w:t")))
        media = [name for name in archive.namelist()
                 if name.startswith("word/media/")]
    return "".join(parts), media


def _forbidden_hits(text: str) -> list[str]:
    return [token for token in forbidden_tokens(SUBJECT) if token in text]


def _part_counts(paper: dict) -> Counter:
    return Counter(
        part["label"] for question in paper["questions"]
        for part in question["parts"])


def _part_labels_found(text: str, paper: dict) -> int:
    expected = _part_counts(paper)
    found = 0
    for label, count in expected.items():
        found += min(text.count(f"({label})"), count)
    return found


def _answers_present(text: str, paper: dict) -> tuple[int, list[str]]:
    squashed = _squash(text)
    present = 0
    missing: list[str] = []
    for question in paper["questions"]:
        for part in question["parts"]:
            probe = _squash(part["answer"])[:60]
            if probe and probe in squashed:
                present += 1
            else:
                missing.append(f"{question['number']}({part['label']})")
    return present, missing


def _validate_docx(path: Path, paper: dict, *,
                   scheme: bool) -> dict:
    text, media = _docx_text(path)
    headings = re.findall(r"QUESTION\s+[AB]\d+", text)
    expected_questions = len(paper["questions"])
    expected_parts = sum(len(q["parts"]) for q in paper["questions"])
    answers_present, answers_missing = _answers_present(text, paper)
    figures = [q["figure"] for q in paper["questions"] if q.get("figure")]
    captions_found = sum(
        1 for figure in figures if figure["caption"] in text)
    return {
        "xml_valid": True,
        "forbidden_tokens": _forbidden_hits(text),
        "question_headings": len(headings),
        "expected_questions": expected_questions,
        "part_labels_found": _part_labels_found(text, paper),
        "expected_parts": expected_parts,
        "has_crest": any("image1" in name for name in media),
        "has_subject": ("CSC429" in text and "NOVEMBER 2026" in text),
        "scheme_heading": (not scheme) or ("MARKING SCHEME" in text),
        "answers_present": answers_present,
        "answers_missing": answers_missing,
        "figure_questions": len(figures),
        "figure_captions_found": captions_found,
        "media_count": len(media),
        "figures_present": (captions_found == len(figures)
                            and len(media) >= 1 + len(figures)),
        "is_scheme": scheme,
    }


def _validate_pdf(path: Path, paper: dict, *,
                  scheme: bool) -> dict:
    document = pymupdf.open(str(path))
    pages: list[str] = []
    overflow: list[dict] = []
    image_count = 0
    try:
        for index, page in enumerate(document):
            pages.append(page.get_text())
            image_count += len(page.get_images(full=True))
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
    finally:
        document.close()
    text = "\n".join(pages)
    squashed_text = _squash(text)
    squashed_first = _squash(pages[0]) if pages else ""
    expected_questions = [f"QUESTION {q['number']}"
                          for q in paper["questions"]]
    expected_marks = [f"({part['marks']} marks)"
                      for q in paper["questions"] for part in q["parts"]]
    answers_present, answers_missing = _answers_present(text, paper)
    figures = [q["figure"] for q in paper["questions"] if q.get("figure")]
    captions_found = sum(
        1 for figure in figures if _squash(figure["caption"]) in squashed_text)
    if scheme:
        cover_tokens = ["UNIVERSITI TEKNOLOGI MARA", "MARKING SCHEME",
                        "CSC429", "COMPUTER ORGANIZATION AND ARCHITECTURE",
                        "NOVEMBER 2026"]
    else:
        cover_tokens = ["UNIVERSITI TEKNOLOGI MARA", "CSC429",
                        "COMPUTER ORGANIZATION AND ARCHITECTURE",
                        "NOVEMBER 2026", "3 HOURS"]
    return {
        "pages": len(pages),
        "page1_has_cover": bool(pages) and all(
            _squash(token) in squashed_first for token in cover_tokens),
        "body_starts_on_page2": (
            len(pages) > 1
            and _squash("QUESTION A1") in _squash(pages[1])),
        "headings_found": all(
            _squash(label) in squashed_text for label in expected_questions),
        "full_marks": all(
            _squash(mark) in squashed_text for mark in expected_marks),
        "scheme_heading": (not scheme) or ("MARKING SCHEME" in text),
        "forbidden_tokens": _forbidden_hits(text),
        "right_overflow": overflow[:10],
        "answers_present": answers_present,
        "answers_missing": answers_missing,
        "figure_questions": len(figures),
        "figure_captions_found": captions_found,
        "image_count": image_count,
        "figures_present": (captions_found == len(figures)
                            and image_count >= len(figures)),
        "is_scheme": scheme,
    }


def _validate(paper: dict, paper_docx: Path, scheme_docx: Path,
              paper_pdf: Path | None, scheme_pdf: Path | None,
              *, require_pdf: bool = True) -> dict:
    checks = {
        "paper_docx": _validate_docx(paper_docx, paper, scheme=False),
        "scheme_docx": _validate_docx(scheme_docx, paper, scheme=True),
        "paper_pdf": _validate_pdf(paper_pdf, paper, scheme=False)
        if paper_pdf else {},
        "scheme_pdf": _validate_pdf(scheme_pdf, paper, scheme=True)
        if scheme_pdf else {},
    }
    expected_parts = sum(len(q["parts"]) for q in paper["questions"])
    figure_count = sum(1 for q in paper["questions"] if q.get("figure"))
    problems: list[str] = []
    for name in ("paper_docx", "scheme_docx"):
        check = checks[name]
        if not check.get("xml_valid"):
            problems.append(f"{name}: invalid XML")
        if check.get("forbidden_tokens"):
            problems.append(f"{name}: forbidden tokens "
                            f"{check['forbidden_tokens']}")
        if check.get("question_headings") != check.get("expected_questions"):
            problems.append(f"{name}: question headings mismatch")
        if check.get("part_labels_found") != check.get("expected_parts"):
            problems.append(f"{name}: part labels mismatch")
        if not check.get("has_crest"):
            problems.append(f"{name}: crest missing")
        if not check.get("has_subject"):
            problems.append(f"{name}: subject/date missing")
        if not check.get("scheme_heading"):
            problems.append(f"{name}: MARKING SCHEME missing")
        if name == "paper_docx" and check.get("answers_present"):
            problems.append(f"{name}: answer text leaked into the paper")
        if (name == "scheme_docx"
                and check.get("answers_present") != check.get("expected_parts")):
            problems.append(
                f"{name}: answers missing for "
                f"{check.get('answers_missing')}")
        if not check.get("figures_present"):
            problems.append(
                f"{name}: diagram captions/images missing "
                f"({check.get('figure_captions_found')}/{figure_count})")
    for name in ("paper_pdf", "scheme_pdf"):
        check = checks[name]
        if not check:
            if require_pdf:
                problems.append(f"{name}: PDF not produced")
            continue
        if not check.get("page1_has_cover"):
            problems.append(f"{name}: cover missing")
        if not check.get("body_starts_on_page2"):
            problems.append(f"{name}: body does not start on page 2")
        if not check.get("headings_found"):
            problems.append(f"{name}: headings missing")
        if not check.get("full_marks"):
            problems.append(f"{name}: marks missing")
        if check.get("forbidden_tokens"):
            problems.append(f"{name}: forbidden tokens "
                            f"{check['forbidden_tokens']}")
        if check.get("right_overflow"):
            problems.append(f"{name}: right-margin overflow "
                            f"{check['right_overflow'][:2]}")
        if (name == "scheme_pdf"
                and check.get("answers_present") != expected_parts):
            problems.append(
                f"{name}: answers missing for "
                f"{check.get('answers_missing')}")
        if not check.get("figures_present"):
            problems.append(
                f"{name}: diagram captions/images missing "
                f"({check.get('figure_captions_found')}/{figure_count})")
    checks["problems"] = problems
    return checks


def _patch_page_count(path: Path, marker: str, pages: int) -> bool:
    document = docx.Document(str(path))
    for paragraph in document.paragraphs:
        if paragraph.text.strip().startswith(marker):
            _set_paragraph_text(
                paragraph, f"{marker} of {pages} printed pages.")
            document.save(str(path))
            return True
    return False


def _remove_with_retry(path: Path, attempts: int = 6) -> bool:
    for _ in range(attempts):
        try:
            path.unlink(missing_ok=True)
            return True
        except PermissionError:
            time.sleep(0.4)
    return False


def _export_with_page_count(docx_path: Path, pdf_path: Path,
                            marker: str) -> int:
    measuring = pdf_path.with_name(
        f"{pdf_path.stem}.{time.time_ns()}.measuring.pdf")
    pages = export_pdf(docx_path, measuring)
    if _patch_page_count(docx_path, marker, pages):
        if not _remove_with_retry(pdf_path):
            raise RuntimeError(
                f"cannot replace locked PDF: {pdf_path}")
        pages = export_pdf(docx_path, pdf_path)
        _remove_with_retry(measuring)
    else:
        measuring.replace(pdf_path)
    return pages


def _progress(paper: dict) -> list[dict]:
    events = []
    for question in paper["questions"]:
        for part in question["parts"]:
            events.append({
                "question": question["number"],
                "slot": f"{question['number']}{part['label']}",
                "status": "accepted",
                "message": question["topic"],
                "cost_usd": 0,
                "calls": 0,
                "accepted": 1,
                "placeholders": 0,
            })
    return events


def _files(out: Path, export: bool) -> dict[str, str]:
    return {
        "paper_docx": str(out / "paper.docx"),
        "paper_pdf": str(out / "paper.pdf") if export else "",
        "scheme_docx": str(out / "scheme.docx"),
        "scheme_pdf": str(out / "scheme.pdf") if export else "",
    }


def _render_previews(out: Path, paper_pdf: Path, scheme_pdf: Path,
                     dpi: int = 110) -> list[str]:
    saved = []
    preview = out / "preview"
    preview.mkdir(parents=True, exist_ok=True)
    for name, path in (("paper", paper_pdf), ("scheme", scheme_pdf)):
        if not path.exists():
            continue
        document = pymupdf.open(str(path))
        try:
            for index, page in enumerate(document):
                target = preview / f"{name}_page_{index + 1:02d}.png"
                page.get_pixmap(dpi=dpi).save(str(target))
                saved.append(str(target))
        finally:
            document.close()
    return saved


def _prepare_figures(paper: dict, out: Path) -> int:
    count = 0
    for question in paper["questions"]:
        figure = question.get("figure")
        if not figure:
            continue
        count += 1
        figure["number"] = count
        figure["caption"] = f"Figure {count}: {figure['caption']}"
        question["stem"] = question["stem"].format(
            figure=f"Figure {count}")
        path = out / "figures" / f"figure_{count:02d}_{figure['kind']}.png"
        render_figure(figure["kind"], path)
        figure["path"] = str(path)
    return count


def build_seed(seed: int, *, out_dir: Path | None = None,
               force: bool = False, export: bool = True,
               scheme_only: bool = False) -> dict:
    """Build one CSC429 seed into the Library cache."""
    paper = generate_paper(build_plan(int(seed)))
    out = Path(out_dir) if out_dir is not None else cache_path(
        "realistic", seed, None, subject=SUBJECT)
    meta_path = out / "meta.json"
    if not force and not scheme_only and meta_path.exists():
        try:
            existing = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            existing = {}
        files = existing.get("files", {})
        if files and all(Path(value).exists() for value in files.values()
                         if value):
            return {"seed": seed, "cached": True, "path": str(out)}
    out.mkdir(parents=True, exist_ok=True)
    _prepare_figures(paper, out)
    paper_docx = out / "paper.docx"
    scheme_docx = out / "scheme.docx"
    paper_pdf = out / "paper.pdf"
    scheme_pdf = out / "scheme.pdf"
    if scheme_only and paper_docx.exists():
        _build_scheme_docx(paper, scheme_docx)
        scheme_pages = 0
        if export:
            scheme_pages = _export_with_page_count(
                scheme_docx, scheme_pdf, SCHEME_COVER_MARKER)
        validation = _validate(
            paper, paper_docx, scheme_docx, None,
            scheme_pdf if scheme_pages else None,
            require_pdf=export)
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        else:
            meta = {}
        meta["files"] = _files(out, export and bool(scheme_pages))
        meta["validation"] = validation
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        if validation["problems"]:
            raise RuntimeError(
                f"CSC429 seed {seed} scheme validation failed: "
                + "; ".join(validation["problems"]))
        return {"seed": seed, "scheme_only": True, "path": str(out),
                "scheme_pdf": bool(scheme_pages)}
    _build_paper_docx(paper, paper_docx)
    _build_scheme_docx(paper, scheme_docx)
    paper_pages = 0
    scheme_pages = 0
    if export:
        paper_pages = _export_with_page_count(
            paper_docx, paper_pdf, PAPER_COVER_MARKER)
        scheme_pages = _export_with_page_count(
            scheme_docx, scheme_pdf, SCHEME_COVER_MARKER)
    validation = _validate(
        paper, paper_docx, scheme_docx,
        paper_pdf if paper_pages else None,
        scheme_pdf if scheme_pages else None,
        require_pdf=export)
    created = time.time()
    year = utc_year(created)
    files = _files(out, export and bool(paper_pages) and bool(scheme_pages))
    progress = _progress(paper)
    figure_paths = [q["figure"]["path"] for q in paper["questions"]
                    if q.get("figure")]
    summary = {
        "subject": SUBJECT,
        "seed": int(seed),
        "mode": "realistic",
        "computed_marks": 100,
        "accepted": len(paper["questions"]),
        "placeholders": 0,
        "total_slots": len(paper["questions"]),
        "has_practice_mode": False,
        "has_placeholders": False,
        "model": "csc429-deterministic",
        "cost_usd": 0.0,
        "cached": True,
        "topic_marks": paper["topic_marks"],
        "total_marks": paper["total_marks"],
        "question_count": paper["question_count"],
        "generator_ids": paper["generator_ids"],
        "figure_questions": len(figure_paths),
        "pdf_available": bool(paper_pages and scheme_pages),
        "qa_problems": validation["problems"],
    }
    meta = {
        "subject": SUBJECT,
        "seed": int(seed),
        "mode": "realistic",
        "computed_marks": 100,
        "model": "csc429-deterministic",
        "cost_usd": 0.0,
        "accepted": len(paper["questions"]),
        "placeholders": 0,
        "total_slots": len(paper["questions"]),
        "has_practice_mode": False,
        "has_placeholders": False,
        "created": created,
        "year": year,
        "topic_marks": paper["topic_marks"],
        "total_marks": paper["total_marks"],
        "question_count": paper["question_count"],
        "generator_ids": paper["generator_ids"],
        "figure_questions": len(figure_paths),
        "figures": figure_paths,
        "files": files,
        "progress": progress,
        "summary": summary,
        "validation": validation,
        "pages": {"paper": paper_pages, "scheme": scheme_pages},
    }
    (out / "qa.json").write_text(
        json.dumps(validation, indent=2), encoding="utf-8")
    if paper_pages and scheme_pages:
        _render_previews(out, paper_pdf, scheme_pdf)
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    if validation["problems"]:
        raise RuntimeError(
            f"CSC429 seed {seed} validation failed: "
            + "; ".join(validation["problems"]))
    return {"seed": int(seed), "cached": False, "path": str(out),
            "pdf": bool(paper_pages), "scheme_pdf": bool(scheme_pages),
            "accepted": len(paper["questions"]),
            "total_marks": paper["total_marks"]}


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--out", default="")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--no-pdf", action="store_true")
    args = parser.parse_args()
    result = build_seed(
        args.seed,
        out_dir=Path(args.out) if args.out else None,
        force=args.force,
        export=not args.no_pdf,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
