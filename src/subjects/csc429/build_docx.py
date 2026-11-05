"""Stage-7 CSC429 paper and marking-guide builder.

The paper is assembled from the approved CSC429 template and the resolved
Stage-5 plan: data-representation slots come from the Stage-6 generators and
every other slot is a real past-paper question with its original figure/table
presentation. The marking guide reuses the standard UTM scheme template.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import shutil
import tempfile
import time
import zipfile
from pathlib import Path

import docx
import pymupdf
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt

from src import config
from src.app.filenames import utc_year
from src.subjects import forbidden
from src.subjects.csc429 import generators, planner
from src.subjects.csc429 import seed_pilot as pilot
from src.subjects.csc429.tables import table_question_assets

SUBJECT = "CSC429"
TRACKING = config.TRACKING_DIR / "csc429"
BANK_PATH = TRACKING / "question_bank_draft.json"
LOG_PATH = TRACKING / "question_log.json"
ASSETS_PATH = TRACKING / "assets" / "manifest.json"
TEMPLATE = config.subject_reference_dir(SUBJECT) / "CSC429 TEMPLATE.docx"
SCHEME_TEMPLATE = (config.REFERENCE_DIR / "standard" /
                   "UTM_STANDARD_MARKING_SCHEME.docx")
DEFAULT_OUT = TRACKING / "build_sample"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _set_paragraph_text(paragraph, text: str) -> None:
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


def _set_cover_text_preserving_crest(paragraph, text: str) -> None:
    """Replace the CONFIDENTIAL line without deleting its inline crest."""
    drawing_elements = [
        run._r for run in paragraph.runs
        if run._r.findall(qn("w:drawing"))
    ]
    if not drawing_elements:
        _set_paragraph_text(paragraph, text)
        return
    first = next((run for run in paragraph.runs
                  if run._r not in drawing_elements), None)
    font_name = first.font.name if first is not None else "Arial"
    font_size = first.font.size if first is not None else Pt(9.5)
    bold = first.bold if first is not None else True
    italic = first.italic if first is not None else False
    for run in list(paragraph.runs):
        if run._r in drawing_elements:
            for node in list(run._r.findall(qn("w:t"))):
                run._r.remove(node)
            continue
        run._r.getparent().remove(run._r)
    run = paragraph.add_run(text)
    run.font.name = font_name
    run.font.size = font_size
    run.bold = bold
    run.italic = italic
    drawing_elements[0].addprevious(run._r)


def _rewrite_scheme_text(source: Path, target: Path) -> None:
    replacements = (
        ("CSC662", "CSC429"),
        ("COMPUTER SECURITY", "COMPUTER ORGANIZATION AND ARCHITECTURE"),
        ("OCTOBER 2026", "NOVEMBER 2026"),
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


def _resolved_slots(seed: int, plan: dict, bank: dict, log: dict,
                    assets: dict[str, dict], layouts: dict[str, dict]) -> list[dict]:
    entries = {entry["question_id"]: entry for entry in log["entries"]}
    questions = {q["question_id"]: q for q in bank["questions"]}
    used_ids: set[str] = set()
    used_papers: set[str] = set()
    warnings = []
    resolved = []
    for slot in plan["slots"]:
        if slot["resolver"] == "csc429.generator":
            generated = generators.generate_for_slot(
                seed, slot["slot"], slot["topic"], slot["marks"])
            if generated is None:
                raise RuntimeError(f"generator missing for {slot['slot']}")
            blocks = [{"type": "text", "page": 1, "y": 0,
                       "text": generated["text"]}]
            for index, subpart in enumerate(generated["subparts"]):
                blocks.append({
                    "type": "text", "page": 1, "y": index + 1,
                    "text": f"{subpart['label']}) {subpart['text']}",
                })
            resolved.append({
                **slot,
                "kind": "generated_question",
                "question_id": generated["question_id"],
                "paper_id": generated["paper_id"],
                "source_file": "",
                "source_pages": [],
                "asset_ids": [],
                "content": blocks,
                "text": generated["text"],
                "subparts": generated["subparts"],
                "answer": generated["answer"],
                "marking": generated["marking"],
                "generator_id": generated["generator_id"],
                "metadata": generated["metadata"],
            })
            continue
        if slot["resolver"] != "csc429.real_bank":
            raise RuntimeError(f"unknown resolver: {slot['resolver']}")
        candidates = []
        for entry in log["entries"]:
            question = questions.get(entry["question_id"])
            if question is None:
                continue
            if (entry["part"] != slot["part"]
                    or entry["topic"] != slot["topic"]
                    or entry["marks"] != slot["marks"]):
                continue
            if question["question_id"] in used_ids:
                continue
            if not pilot._usable(question, assets, layouts):
                continue
            selected_assets = pilot._question_assets(question, assets)
            content = pilot.build_content(question, assets, layouts)
            if not content:
                continue
            candidates.append((question, entry, selected_assets, content))
        if not candidates:
            raise RuntimeError(
                f"no real question for {slot['slot']} "
                f"({slot['topic']}, {slot['marks']} marks)")
        fresh = [row for row in candidates
                 if row[0]["paper_id"] not in used_papers]
        pool = fresh or candidates
        if not fresh:
            warnings.append(
                f"{slot['slot']} reuses source paper "
                f"{sorted({row[0]['paper_id'] for row in candidates})}")
        rng = random.Random(f"csc429:build:{seed}:{slot['slot']}")
        question, entry, selected_assets, content = rng.choice(pool)
        used_ids.add(question["question_id"])
        used_papers.add(question["paper_id"])
        resolved.append({
            **slot,
            "kind": "real_bank_question",
            "question_id": question["question_id"],
            "paper_id": question["paper_id"],
            "source_file": question.get("source_file", ""),
            "source_pages": question.get("pages", []),
            "asset_ids": [asset["asset_id"] for asset in selected_assets],
            "content": content,
            "text": question.get("text", ""),
            "subparts": question.get("subparts", []),
            "answer": "",
            "marking": [],
            "generator_id": "",
        })
    return resolved, warnings


def _paper_qa(plan: dict, docx_path: Path, pdf_path: Path | None) -> dict:
    text = _docx_text(docx_path)
    normalised = " ".join(text.split())
    qa = {
        "path": str(docx_path),
        "xml_valid": False,
        "forbidden_tokens": [],
        "missing": [],
        "problems": [],
        "pdf": {},
    }
    try:
        with zipfile.ZipFile(docx_path) as archive:
            archive.read("word/document.xml")
        qa["xml_valid"] = True
    except Exception as error:
        qa["problems"].append(f"invalid DOCX: {error}")
        return qa
    for heading in ("PART A (80 MARKS)", "PART B (20 MARKS)"):
        if heading not in text:
            qa["missing"].append(heading)
    for slot in plan["slots"]:
        if f"QUESTION {slot['slot']}" not in text:
            qa["missing"].append(f"QUESTION {slot['slot']}")
    if "This examination paper consists of" not in text:
        qa["missing"].append("page-count cover line")
    if "END OF QUESTION PAPER" in text:
        qa["missing"].append("unexpected END OF QUESTION PAPER")
    if qa["missing"]:
        qa["problems"].append("missing content: " + ", ".join(qa["missing"][:8]))
    return qa


def _scheme_qa(plan: dict, docx_path: Path, pdf_path: Path | None) -> dict:
    text = _docx_text(docx_path)
    qa = {
        "path": str(docx_path),
        "xml_valid": False,
        "inline_shapes": 0,
        "forbidden_tokens": [],
        "missing": [],
        "problems": [],
        "pdf": {},
    }
    try:
        with zipfile.ZipFile(docx_path) as archive:
            archive.read("word/document.xml")
        qa["xml_valid"] = True
    except Exception as error:
        qa["problems"].append(f"invalid DOCX: {error}")
        return qa
    qa["inline_shapes"] = len(docx.Document(str(docx_path)).inline_shapes)
    if qa["inline_shapes"] == 0:
        qa["missing"].append("scheme crest image")
    for token in ("MARKING SCHEME", "CSC429", "PART A — MARKING GUIDE",
                  "PART B — MARKING GUIDE"):
        if token not in text:
            qa["missing"].append(token)
    for slot in plan["slots"]:
        if f"QUESTION {slot['slot']}" not in text:
            qa["missing"].append(f"QUESTION {slot['slot']}")
        if slot["kind"] == "generated_question":
            answers = [subpart.get("answer", "")
                       for subpart in slot.get("subparts") or []]
            if not answers:
                answers = [slot.get("answer", "")]
            for answer in answers:
                answer = " ".join(str(answer).split())[:60]
                if answer and answer not in " ".join(text.split()):
                    qa["missing"].append(f"{slot['slot']} generated answer")
                    break
        elif slot["kind"] == "real_bank_question":
            source = str(slot.get("source_file", ""))
            if source and source not in text:
                qa["missing"].append(f"{slot['slot']} source file")
    if qa["missing"]:
        qa["problems"].append("missing content: " + ", ".join(qa["missing"][:8]))
    return qa


def _docx_text(path: Path) -> str:
    document = docx.Document(str(path))
    parts = [paragraph.text for paragraph in document.paragraphs]
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


def _pdf_qa(path: Path, *, scheme: bool) -> dict:
    result = {"path": str(path), "pages": 0, "page1_cover": False,
              "page1_images": 0, "body_starts_page2": False,
              "right_overflow": [], "problems": []}
    with pymupdf.open(str(path)) as pdf:
        result["pages"] = len(pdf)
        if not len(pdf):
            result["problems"].append("PDF has no pages")
            return result
        pages = [page.get_text() for page in pdf]
        result["page1_images"] = len(pdf[0].get_images(full=True))
        cover = pages[0]
        result["page1_cover"] = (
            "CSC429" in cover
            and ("MARKING SCHEME" in cover if scheme
                 else "FINAL EXAMINATION" in cover
                 or "INSTRUCTIONS TO CANDIDATES" in cover))
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
    else:
        if not result["page1_cover"]:
            result["problems"].append("scheme cover missing")
        if result["page1_images"] == 0:
            result["problems"].append("scheme crest image missing")
    if result["right_overflow"]:
        result["problems"].append(
            f"right overflow on {len(result['right_overflow'])} span(s)")
    return result


def _scheme_body(doc, plan: dict) -> None:
    _heading(doc, "PART A — MARKING GUIDE")
    for slot in [s for s in plan["slots"] if s["part"] == "A"]:
        _scheme_entry(doc, slot)
    doc.add_page_break()
    _heading(doc, "PART B — MARKING GUIDE")
    for slot in [s for s in plan["slots"] if s["part"] == "B"]:
        _scheme_entry(doc, slot)
    _para(doc, "END OF MARKING SCHEME", italic=True, size=9,
          align=WD_ALIGN_PARAGRAPH.CENTER, before=14, after=4)


def _heading(doc, text: str) -> None:
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(8)
    paragraph.paragraph_format.space_after = Pt(8)
    run = paragraph.add_run(pilot._safe_text(text))
    run.bold = True
    run.font.name = "Arial"
    run.font.size = Pt(12)


def _para(doc, text: str = "", *, size: float = 10, bold: bool = False,
          italic: bool = False, align=None, before: float = 0,
          after: float = 4) -> None:
    paragraph = doc.add_paragraph()
    if align is not None:
        paragraph.alignment = align
    paragraph.paragraph_format.space_before = Pt(before)
    paragraph.paragraph_format.space_after = Pt(after)
    run = paragraph.add_run(pilot._safe_text(text))
    run.bold = bold
    run.italic = italic
    run.font.name = "Arial"
    run.font.size = Pt(size)


def _scheme_entry(doc, slot: dict) -> None:
    _para(doc, f"QUESTION {slot['slot']} ({slot['marks']} marks)",
          size=11, bold=True, before=10, after=3)
    _para(doc, f"Topic: {slot['topic_label']}", size=9, italic=True, after=3)
    if slot["kind"] == "generated_question":
        _para(doc, slot["text"], size=10, after=3)
        if slot["subparts"]:
            for subpart in slot["subparts"]:
                _para(doc, f"{subpart['label']}) {subpart['text']}",
                      size=10, bold=True, after=2)
                _para(doc, f"Answer: {subpart['answer']}", size=10, after=2)
                for point in subpart.get("marking", []):
                    _para(doc, f"• {point}", size=9, italic=True, after=1)
        else:
            _para(doc, f"Answer: {slot['answer']}", size=10, after=2)
            for point in slot.get("marking", []):
                _para(doc, f"• {point}", size=9, italic=True, after=1)
        return
    _para(doc, slot["text"], size=10, after=3)
    pages = ", ".join(str(page) for page in slot.get("source_pages") or [])
    source = slot.get("source_file") or slot.get("paper_id")
    _para(doc, f"Source: {source}" + (f", page(s) {pages}" if pages else ""),
          size=9, italic=True, after=2)
    _para(doc,
          "Answer: The supplied source pack does not include a marking "
          "scheme for this past-paper question. Use the source paper and its "
          "mark allocation; no answer has been invented.",
          size=9, italic=True, after=4)


def _patch_scheme_cover(doc, plan: dict) -> None:
    generated = sum(1 for slot in plan["slots"]
                    if slot["kind"] == "generated_question")
    real = len(plan["slots"]) - generated
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text.startswith("CONFIDENTIAL"):
            _set_cover_text_preserving_crest(
                paragraph, "CONFIDENTIAL	CS/NOV 2026/CSC429")
        elif text.startswith("This marking scheme accompanies"):
            _set_paragraph_text(
                paragraph,
                "This marking scheme accompanies the CSC429 mock paper "
                "(November 2026).")
        elif text.startswith("Computed answers show working"):
            _set_paragraph_text(
                paragraph,
                "Generated answers show working. Real past-paper questions "
                "are reproduced with their source reference; no answer is "
                "invented where the original scheme is unavailable.")
        elif text.startswith("Supported theory marking points"):
            _set_paragraph_text(
                paragraph,
                "Generated marking points state the expected answer and the "
                "allocation of marks. Real-bank questions retain their source "
                "paper and page reference.")
        elif text.startswith("Part A ="):
            _set_paragraph_text(
                paragraph,
                "Part A = 4 x 5 + 6 x 10; Part B = 1 x 20; total = 100 marks.")
        elif text.startswith("Computed:"):
            _set_paragraph_text(
                paragraph,
                f"Generated slots: {generated}. Real-bank slots: {real}. "
                "Placeholders: 0.")
        elif text.startswith("Questions and answers are"):
            _set_paragraph_text(
                paragraph,
                "Questions and answers are for local study use only.")
        elif text.startswith("Near-copy rejection"):
            _set_paragraph_text(
                paragraph,
                "Structure derived from 20 unique CSC429 past papers; every "
                "real question remains traceable to its source page.")
        elif text.startswith("This marking scheme consists of"):
            _set_paragraph_text(
                paragraph,
                "This marking scheme consists of 1 printed page.")


def _scheme_page_count(path: Path, pages: int) -> None:
    doc = docx.Document(str(path))
    for paragraph in doc.paragraphs:
        if paragraph.text.strip().startswith("This marking scheme consists of"):
            _set_paragraph_text(
                paragraph,
                f"This marking scheme consists of {pages} printed pages")
            break
    doc.save(str(path))


def build_scheme(plan: dict, target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="csc429_scheme_") as tmp:
        rewritten = Path(tmp) / "scheme_template.docx"
        _rewrite_scheme_text(SCHEME_TEMPLATE, rewritten)
        doc = docx.Document(str(rewritten))
        _patch_scheme_cover(doc, plan)
        _scheme_body(doc, plan)
        doc.save(str(target))
    return target


def _generated_content(question: dict) -> list[dict]:
    blocks = [{"type": "text", "page": 1, "y": 0,
               "text": question["text"]}]
    for index, subpart in enumerate(question.get("subparts") or []):
        blocks.append({"type": "text", "page": 1, "y": index + 1,
                       "text": f"{subpart['label']}) {subpart['text']}"})
    return blocks


def build_paper(plan: dict, target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    pilot.build_docx(plan, target)
    return target


def build_seed(seed: int, out_dir: Path | None = None,
               export: bool = True, force: bool = False, **kwargs) -> dict:
    out = Path(out_dir) if out_dir is not None else DEFAULT_OUT
    meta_path = out / "meta.json"
    if not force and meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            files = [Path(value) for value in (meta.get("files") or {}).values()
                     if value]
            if files and all(path.exists() for path in files):
                qa = json.loads((out / "qa.json").read_text(encoding="utf-8"))
                return {**qa, "seed": seed, "cached": True, "path": str(out),
                        "files": meta.get("files", {})}
        except Exception:
            pass
    out.mkdir(parents=True, exist_ok=True)
    plan = planner.build_plan(seed)
    bank = _load(BANK_PATH)
    log = _load(LOG_PATH)
    assets = pilot._asset_index(_load(ASSETS_PATH))
    layouts = pilot._layout_index()
    resolved, warnings = _resolved_slots(seed, plan, bank, log, assets, layouts)
    plan["slots"] = resolved
    plan_path = out / "plan.json"
    plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False),
                         encoding="utf-8")
    paper_docx = out / "paper.docx"
    scheme_docx = out / "scheme.docx"
    paper_pdf = out / "paper.pdf"
    scheme_pdf = out / "scheme.pdf"
    build_paper(plan, paper_docx)
    build_scheme(plan, scheme_docx)
    qa = {
        "subject": SUBJECT,
        "seed": seed,
        "warnings": warnings,
        "paper_docx": _paper_qa(plan, paper_docx, None),
        "scheme_docx": _scheme_qa(plan, scheme_docx, None),
        "paper_pdf": {},
        "scheme_pdf": {},
    }
    files = {}
    if export:
        pages, actual_paper_pdf = pilot._export_seed_pdf(paper_docx, paper_pdf)
        pilot._patch_page_count(paper_docx, pages)
        pages, actual_paper_pdf = pilot._export_seed_pdf(paper_docx, paper_pdf)
        qa["paper_pdf"] = _pdf_qa(actual_paper_pdf, scheme=False)
        qa["paper_pdf"]["pages"] = pages
        scheme_pages, actual_scheme_pdf = pilot._export_seed_pdf(
            scheme_docx, scheme_pdf)
        _scheme_page_count(scheme_docx, scheme_pages)
        scheme_pages, actual_scheme_pdf = pilot._export_seed_pdf(
            scheme_docx, scheme_pdf)
        qa["scheme_pdf"] = _pdf_qa(actual_scheme_pdf, scheme=True)
        qa["scheme_pdf"]["pages"] = scheme_pages
        files = {
            "paper_docx": str(paper_docx),
            "paper_pdf": str(actual_paper_pdf),
            "scheme_docx": str(scheme_docx),
            "scheme_pdf": str(actual_scheme_pdf),
        }
    else:
        files = {
            "paper_docx": str(paper_docx),
            "paper_pdf": "",
            "scheme_docx": str(scheme_docx),
            "scheme_pdf": "",
        }
    scan_paths = [Path(value) for value in files.values() if value]
    scan = forbidden.scan(scan_paths, SUBJECT)
    for key in ("paper_docx", "scheme_docx", "paper_pdf", "scheme_pdf"):
        if key not in qa or not isinstance(qa[key], dict):
            continue
        qa[key]["forbidden_tokens"] = [
            hit["token"] for hit in scan["hits"]
            if hit.get("path") == qa[key].get("path")]
    qa["forbidden_hits"] = scan["hits"]
    qa["problems"] = []
    for key in ("paper_docx", "scheme_docx", "paper_pdf", "scheme_pdf"):
        qa["problems"].extend(qa.get(key, {}).get("problems", []))
    if scan["hits"]:
        qa["problems"].append(
            "forbidden tokens: " + ", ".join(
                f"{Path(hit['path']).name}:{hit['token']}"
                for hit in scan["hits"][:8]))
    qa["warnings"] = warnings
    qa["files"] = files
    (out / "qa.json").write_text(json.dumps(qa, indent=2), encoding="utf-8")
    if qa["problems"]:
        raise RuntimeError(
            f"CSC429 seed {seed} validation failed: "
            + "; ".join(qa["problems"][:5]))
    progress = [{
        "question": slot["slot"],
        "slot": slot["slot"],
        "status": "accepted",
        "message": slot["topic"],
        "cost_usd": 0,
        "calls": 0,
        "accepted": 1,
        "placeholders": 0,
    } for slot in plan["slots"]]
    created = time.time()
    meta = {
        "subject": SUBJECT,
        "seed": seed,
        "mode": "realistic",
        "computed_marks": None,
        "model": "csc429-deterministic",
        "cost_usd": 0.0,
        "accepted": len(progress),
        "placeholders": 0,
        "total_slots": len(progress),
        "total_marks": 100,
        "question_count": len(progress),
        "has_practice_mode": False,
        "has_placeholders": False,
        "created": created,
        "year": utc_year(created),
        "topic_marks": plan["topic_marks"],
        "files": files,
        "warnings": warnings,
        "summary": {
            "subject": SUBJECT,
            "seed": seed,
            "mode": "realistic",
            "accepted": len(progress),
            "placeholders": 0,
            "total_slots": len(progress),
            "total_marks": 100,
            "question_count": len(progress),
            "has_practice_mode": False,
            "has_placeholders": False,
            "model": "csc429-deterministic",
            "cost_usd": 0.0,
            "cached": True,
            "topic_marks": plan["topic_marks"],
            "pdf_available": bool(export),
            "generated_slots": sum(
                1 for slot in plan["slots"]
                if slot["kind"] == "generated_question"),
            "real_bank_slots": sum(
                1 for slot in plan["slots"]
                if slot["kind"] == "real_bank_question"),
            "warnings": warnings,
        },
        "progress": progress,
        "validation": qa,
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return {**qa, "seed": seed, "cached": False, "path": str(out),
            "files": files}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--no-pdf", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    result = build_seed(
        args.seed, Path(args.out), export=not args.no_pdf, force=args.force)
    print(json.dumps({
        "seed": result["seed"],
        "files": result["files"],
        "problems": result["problems"],
        "warnings": result.get("warnings", []),
    }, indent=2))
    if result["problems"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
