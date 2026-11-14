"""V5 paper-only assembly for the ICT450 pilot.

Questions come only from the approved bank.  The clean owner template supplies
the cover and page-2 section; this module inserts five questions and their
approved assets at the sizes recorded by the V3 scaling check.

The scheme is deliberately not built: V4 answers are deferred by the owner.

Run:
    uv run python -m src.subjects.ict450.assemble --seeds 1-3
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import time
from collections import Counter
from pathlib import Path

import docx
import pymupdf
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT

from src import config
from src.assemble.pdf_export import export_pdf
from src.bank.store import BankStore, save_json
from src.bank.validators import validate_seed_plan
from src.subjects import forbidden
from src.subjects.ict450.bank_build import html_rows
from src.subjects.ict450.papers import SUBJECT

TRACKING = config.TRACKING_DIR / "ict450" / "v2"
BANK = TRACKING / "bank"
TEMPLATE = config.PROJECT_ROOT / "data/reference/ICT450/ICT450_PAPER_TEMPLATE_CLEAN.docx"
SCALING = BANK / "asset_scaling.json"
PATTERN = TRACKING / "question_pattern.json"
OUT = config.PROJECT_ROOT / "outputs" / "ict450_pilot"
CATEGORIES = ("concepts", "design_theory", "normalization", "sql", "erd")
CONTENT_WIDTH_CM = 16.56
MARKS_RE = re.compile(r"\s*\(\s*\d{1,2}\s*marks?\s*\)\s*$", re.I)
NOISE_RE = re.compile(
    r"^\s*(END OF QUESTION PAPER|CONFIDENTIAL|©?\s*Hak Cipta.*|"
    r"CS/.*ICT450.*|CD/.*ICT450.*|\d{1,2})\s*$", re.I)
SCHEMA_LINE_RE = re.compile(r"^\s*[A-Z][A-Z0-9_]*\s*\([^()]*\)\s*$")
DASH_LINE_RE = re.compile(r"^\s*(?:[-•*]|)\s+")


def _load(path: Path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _category_map() -> dict[str, str]:
    payload = _load(PATTERN, {})
    mapping: dict[str, str] = {}
    for paper, slots in (payload.get("papers") or {}).items():
        for slot, category in slots.items():
            mapping[f"{paper}-{slot}"] = str(category)
    return mapping


def build_category_plans(questions: list[dict], *, seed_count: int = 3,
                         reuse_cap: int = 4) -> list[dict]:
    """Select five questions in the past-paper slot order.

    Q1 concepts, Q2 design theory, Q3 normalization, Q4 SQL, Q5 ERD.  Marks
    are not used for selection.  Each seed uses five distinct source papers.
    """
    categories = _category_map()
    by_category: dict[str, list[dict]] = {category: [] for category in CATEGORIES}
    for question in questions:
        category = categories.get(str(question.get("id")))
        flags = [str(flag) for flag in (question.get("review_flags") or [])]
        if "subpart label gap" in flags:
            continue
        if any(flag.lower().startswith("marks ") for flag in flags):
            continue
        if category in by_category:
            by_category[category].append(question)
    for rows in by_category.values():
        rows.sort(key=lambda row: (str(row.get("source_paper")),
                                   str(row.get("id"))))
    uses: Counter[str] = Counter()
    paper_uses: Counter[str] = Counter()
    plans = []
    for seed in range(1, seed_count + 1):
        chosen: list[dict] = []
        used_papers: set[str] = set()
        chosen_ids: set[str] = set()
        for category in CATEGORIES:
            candidates = [
                row for row in by_category[category]
                if str(row.get("id")) not in chosen_ids
                and uses[str(row.get("id"))] < reuse_cap
                and str(row.get("source_paper")) not in used_papers]
            if not candidates:
                candidates = [
                    row for row in by_category[category]
                    if str(row.get("id")) not in chosen_ids
                    and uses[str(row.get("id"))] < reuse_cap]
            if not candidates:
                raise ValueError(
                    f"seed {seed}: no approved {category} question within the "
                    "reuse cap")
            picked = min(
                candidates,
                key=lambda row: (uses[str(row["id"])],
                                 paper_uses[str(row.get("source_paper"))],
                                 0 if row.get("marks") == 20 else 1,
                                 str(row.get("source_paper")),
                                 str(row.get("id"))))
            used_papers.add(str(picked.get("source_paper")))
            chosen_ids.add(str(picked.get("id")))
            chosen.append({
                "slot": f"Q{len(chosen) + 1}",
                "category": category,
                "part": picked.get("part", ""),
                "marks": picked.get("marks"),
                "question_id": picked.get("id"),
                "source_paper": picked.get("source_paper"),
                "pages": picked.get("pages"),
                "topic": picked.get("topic_primary") or picked.get("topic"),
                "topic_tags": picked.get("topic_tags") or [],
                "assets": picked.get("assets") or [],
                "refs": picked.get("refs") or [],
                "content_hash": picked.get("content_hash"),
            })
        for slot in chosen:
            qid = str(slot["question_id"])
            uses[qid] += 1
            paper_uses[str(slot["source_paper"])] += 1
        plans.append({
            "schema_version": 2,
            "seed": seed,
            "reuse_cap": reuse_cap,
            "total_marks": sum(int(slot["marks"] or 0) for slot in chosen),
            "slots": chosen,
        })
    return plans


def _scaling_rows() -> dict[str, dict]:
    payload = _load(SCALING, {})
    return {str(row["id"]): row for row in payload.get("rows") or []}


def _set_font(run, size: float, bold: bool = False) -> None:
    run.font.name = "Arial"
    run.font.size = Pt(size)
    run.bold = bold


def _set_mono(run, size: float = 10) -> None:
    run.font.name = "Consolas"
    run.font.size = Pt(size)
    r_pr = run._element.get_or_add_rPr()
    fonts = r_pr.get_or_add_rFonts()
    for attr in ("w:ascii", "w:hAnsi", "w:cs"):
        fonts.set(qn(attr), "Consolas")


def _tabs(paragraph) -> None:
    paragraph.paragraph_format.tab_stops.add_tab_stop(
        Cm(CONTENT_WIDTH_CM), WD_TAB_ALIGNMENT.RIGHT)


def _clean(text: str) -> str:
    lines = [line for line in str(text or "").splitlines()
             if not NOISE_RE.match(line)]
    cleaned = ("\n".join(lines)
               .replace("", "-")
               .replace("☐", "-").replace("□", "-"))
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()


def _strip_marks(text: str) -> str:
    return MARKS_RE.sub("", _clean(text)).strip()


def _preamble(question: dict) -> str:
    text = _clean(question["native_text_blocks"][0]["text"])
    match = re.search(r"(?m)^\s*\(?a\)\s*", text)
    return (text[:match.start()] if match else text).strip()


def _caption(asset: dict) -> str:
    label = str(asset.get("label") or "").strip()
    caption = " ".join(str(asset.get("caption") or "").split())
    if label and caption.lower().startswith(label.lower()):
        return caption
    if label and caption:
        return f"{label}: {caption}"
    return label or caption


def _add_caption(doc, text: str, *, keep_with_next: bool = False) -> None:
    if not text:
        return
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run(text)
    _set_font(run, 9)
    paragraph.paragraph_format.space_after = Pt(4)
    paragraph.paragraph_format.keep_with_next = keep_with_next


def _set_table_borders(table) -> None:
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "4")
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), "000000")
        borders.append(element)
    tbl_pr.append(borders)


def _add_native_table(doc, asset: dict) -> bool:
    rows = html_rows(asset.get("mineru_table_html") or "")
    if not rows:
        return False
    _add_caption(doc, _caption(asset), keep_with_next=True)
    columns = max(len(row) for row in rows)
    table = doc.add_table(rows=len(rows), cols=columns)
    try:
        table.style = "Table Grid"
    except KeyError:
        _set_table_borders(table)
    table.autofit = False
    table.alignment = 1
    for row_index, row in enumerate(rows):
        for col_index in range(columns):
            text = row[col_index] if col_index < len(row) else ""
            cell = table.cell(row_index, col_index)
            cell.text = text
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    _set_font(run, 8)
    for row in table.rows:
        for cell in row.cells:
            cell.width = Cm(CONTENT_WIDTH_CM / columns)
    for index, row in enumerate(table.rows):
        tr_pr = row._tr.get_or_add_trPr()
        tr_pr.append(OxmlElement("w:cantSplit"))
        if index < len(table.rows) - 1:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    paragraph.paragraph_format.keep_with_next = True
    return True


def _add_image(doc, asset: dict, scaling: dict) -> bool:
    source = Path(str(scaling.get("source") or ""))
    if not source.is_file():
        return False
    width = float(scaling.get("display_width_cm") or CONTENT_WIDTH_CM)
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    run.add_picture(str(source), width=Cm(width))
    _add_caption(doc, _caption(asset))
    return True


def _add_asset(doc, asset: dict, scaling: dict) -> bool:
    if not scaling:
        return False
    if scaling.get("mode") == "native_table":
        return _add_native_table(doc, asset)
    if scaling.get("mode") == "image":
        return _add_image(doc, asset, scaling)
    return False


INSTRUCTION_RE = re.compile(
    r"^\s*(Write|Based on|Answer|The following)\b", re.I)
NESTED_RE = re.compile(r"(?m)^\s*\(?(i|ii|iii|iv|v|vi|vii)\)\s*", re.I)


def _nested_segments(text: str) -> list[tuple[str | None, str]]:
    segments: list[tuple[str | None, str]] = []
    matches = list(NESTED_RE.finditer(text or ""))
    if not matches:
        return [(None, text or "")]
    preamble = (text or "")[:matches[0].start()].strip()
    if preamble:
        segments.append((None, preamble))
    for index, match in enumerate(matches):
        end = (matches[index + 1].start() if index + 1 < len(matches)
               else len(text))
        segments.append((match.group(1).lower(), text[match.end():end]))
    return segments


def _segment_marks(text: str) -> tuple[str, int | None]:
    match = re.search(r"\(\s*(\d{1,2})\s*marks?\s*\)\s*$", text, re.I)
    marks = int(match.group(1)) if match else None
    return (_strip_marks(text), marks)


def _split_preamble(preamble: str, assets: list[dict]) -> tuple[str, str]:
    """Drop a caption block that an asset recreation replaces, then split the
    introductory text from the instruction line."""
    lines = preamble.splitlines()
    for asset in assets:
        caption = " ".join(str(asset.get("caption") or "").split())
        label = str(asset.get("label") or "").strip()
        marker = caption.lower()[:24] if caption else ""
        label_re = (re.compile(rf"^\s*{re.escape(label)}\s*[:：]", re.I)
                    if label else None)
        for index, line in enumerate(lines):
            if ((marker and line.strip().lower().startswith(marker))
                    or (label_re and label_re.match(line))):
                end = len(lines)
                for follow in range(index + 1, len(lines)):
                    if INSTRUCTION_RE.match(lines[follow]):
                        end = follow
                        break
                lines = lines[:index] + lines[end:]
                break
    for index, line in enumerate(lines):
        if INSTRUCTION_RE.match(line):
            return ("\n".join(lines[:index]).strip(),
                    "\n".join(lines[index:]).strip())
    return ("\n".join(lines).strip(), "")


def _render_preamble(doc, text: str, *, schema: bool = False,
                     dash_spacing: bool = False) -> None:
    """Render a preamble, optionally styling schema captions and dash lists.

    SQL questions keep their relational schema in a monospace font with clear
    spacing between each caption.  ERD questions get breathing room before the
    first policy dash and after the last one.  Other questions are unchanged.
    """
    if not text:
        return
    blocks: list[tuple[str, list[str]]] = []
    for line in text.splitlines():
        if schema and SCHEMA_LINE_RE.match(line):
            kind = "schema"
        elif dash_spacing and DASH_LINE_RE.match(line):
            kind = "dash"
        else:
            kind = "text"
        if blocks and blocks[-1][0] == kind:
            blocks[-1][1].append(line)
        else:
            blocks.append((kind, [line]))
    for kind, lines in blocks:
        if kind == "schema":
            for index, line in enumerate(lines):
                paragraph = doc.add_paragraph()
                paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                paragraph.paragraph_format.space_before = (
                    Pt(8) if index == 0 else Pt(0))
                paragraph.paragraph_format.space_after = (
                    Pt(8) if index == len(lines) - 1 else Pt(6))
                _set_mono(paragraph.add_run(line.strip()))
            continue
        paragraph = doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        if kind == "dash":
            paragraph.paragraph_format.space_before = Pt(10)
            paragraph.paragraph_format.space_after = Pt(10)
            lines = [re.sub(r"^\s*[•*]\s+", "- ", line) for line in lines]
        else:
            paragraph.paragraph_format.space_after = Pt(6)
        paragraph.add_run("\n".join(lines))


def _asset_target(asset: dict, preamble: str,
                  subparts: list[dict]) -> tuple[str, int]:
    label = str(asset.get("label") or "").lower()
    if label:
        if label in preamble.lower():
            return ("pre", -1)
        for index, part in enumerate(subparts):
            if label in str(part.get("text") or "").lower():
                return ("part", index)
    # A sub-part that explicitly asks for output/output-as-follows owns its
    # table or figure.
    for index, part in enumerate(subparts):
        text = str(part.get("text") or "").lower()
        if any(word in text for word in ("as follows", "shown below",
                                          "output")):
            return ("part", index)
    document_words = ("form", "invoice", "receipt", "report", "figure",
                      "table", "diagram", "schema")
    if any(word in preamble.lower() for word in document_words):
        return ("pre", -1)
    for index, part in enumerate(subparts):
        text = str(part.get("text") or "").lower()
        if any(word in text for word in ("match", "based on", "below",
                                          "shown")):
            return ("part", index)
    return ("part", 0) if subparts else ("pre", -1)


def _strip_leading_label(text: str, label: str) -> str:
    return re.sub(rf"^\s*\(?{re.escape(label)}\)\s*", "", text,
                  count=1, flags=re.I).strip()


def _render_subpart(doc, label: str, text: str, marks: int | None) -> None:
    segments = _nested_segments(text)
    nested = any(name is not None for name, _ in segments)
    if not nested:
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(1)
        body = _strip_leading_label(_strip_marks(text), label)
        paragraph.add_run(f"{label}) {body}")
        if marks:
            marks_paragraph = doc.add_paragraph()
            marks_paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            marks_paragraph.paragraph_format.space_after = Pt(4)
            marks_paragraph.add_run(f"({marks} marks)")
        return
    for name, segment in segments:
        body, segment_marks = _segment_marks(segment)
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(1)
        if name is None:
            body = _strip_leading_label(body, label)
            paragraph.add_run(f"{label}) {body}")
        else:
            paragraph.add_run(f"{name}) {body}")
        if segment_marks:
            marks_paragraph = doc.add_paragraph()
            marks_paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            marks_paragraph.paragraph_format.space_after = Pt(4)
            marks_paragraph.add_run(f"({segment_marks} marks)")


def _update_page_count(path: Path, pages: int) -> None:
    document = docx.Document(str(path))
    for paragraph in document.paragraphs:
        if "This examination paper consists of" in paragraph.text:
            for run in paragraph.runs:
                run.text = re.sub(r"\d+", str(pages), run.text)
            break
    document.save(str(path))


def _qa(pdf_path: Path, plan: dict, images_expected: int) -> dict:
    document = pymupdf.open(str(pdf_path))
    text = "\n".join(page.get_text() for page in document)
    images = sum(len(page.get_images(full=True)) for page in document)
    problems = []
    for index in range(1, 6):
        if f"QUESTION {index}" not in text:
            problems.append(f"missing QUESTION {index}")
    if "CSC429" in text or "CSC662" in text:
        problems.append("foreign subject code in paper")
    if images < images_expected:
        problems.append(f"expected at least {images_expected} images, "
                        f"found {images}")
    if len(document) > 12:
        problems.append(f"page overflow: {len(document)} pages")
    scan = forbidden.scan([pdf_path], SUBJECT)
    if scan["hits"]:
        problems.append("forbidden tokens")
    return {
        "pages": len(document),
        "images": images,
        "marks_total": sum(int(slot.get("marks") or 0)
                           for slot in plan["slots"]),
        "problems": problems,
        "forbidden_hits": scan["hits"],
    }


def _library_meta(seed: int, plan: dict, qa: dict,
                  paper_docx: Path, paper_pdf: Path) -> dict:
    return {
        "subject": SUBJECT,
        "seed": seed,
        "mode": "realistic",
        "paper_only": True,
        "v4_answers": "deferred",
        "created": time.time(),
        "year": time.gmtime().tm_year,
        "total_marks": qa["marks_total"],
        "marks_total": qa["marks_total"],
        "has_practice_mode": False,
        "has_placeholders": False,
        "accepted": len(plan["slots"]),
        "placeholders": 0,
        "cost_usd": 0.0,
        "model": "recycled-bank",
        "topic_marks": {str(slot.get("category")): int(slot.get("marks") or 0)
                        for slot in plan["slots"]},
        "questions": [slot["question_id"] for slot in plan["slots"]],
        "source_papers": sorted({slot["source_paper"]
                                 for slot in plan["slots"]}),
        "paper_pages": qa["pages"],
        "files": {"paper_docx": str(paper_docx),
                  "paper_pdf": str(paper_pdf)},
        "assets": qa.get("assets", {}),
    }


def build_seed(seed: int, plan: dict, *, force: bool = False,
               out_dir: Path | None = None) -> dict:
    out = Path(out_dir) if out_dir is not None else OUT / f"seed_{seed:02d}"
    if out.exists() and not force:
        return {"seed": seed, "cached": True, "path": str(out)}
    out.mkdir(parents=True, exist_ok=True)
    store = BankStore(BANK)
    scaling = _scaling_rows()
    assets = {row["id"]: row for row in store.assets()}
    doc = docx.Document(str(TEMPLATE))
    style = doc.styles["Normal"]
    style.font.name = "Arial"
    style.font.size = Pt(11)
    images_expected = 0
    expected_assets: list[str] = []
    inserted_assets: list[str] = []
    skipped_assets: list[dict] = []
    for number, slot in enumerate(plan["slots"], start=1):
        question = store.load_question(slot["question_id"])
        category = str(slot.get("category") or "")
        heading = doc.add_paragraph()
        _tabs(heading)
        heading.paragraph_format.space_before = Pt(12)
        heading.paragraph_format.space_after = Pt(6)
        heading.paragraph_format.keep_with_next = True
        if number > 1:
            heading.paragraph_format.page_break_before = True
        run = heading.add_run(f"QUESTION {number}\t"
                              f"({question['marks']} marks)")
        _set_font(run, 12, bold=True)
        preamble = _preamble(question)
        subparts = list(question.get("subparts") or [])
        by_target: dict[tuple[str, int], list[dict]] = {}
        linked_assets = [assets[aid] for aid in question.get("assets") or []
                         if aid in assets]
        # A fallback page crop that duplicates an existing table recreation is
        # not inserted twice.
        if any(asset.get("kind") == "table" for asset in linked_assets):
            for asset in linked_assets:
                if asset.get("kind") == "page_crop":
                    skipped_assets.append({
                        "id": asset["id"], "question_id": question["id"],
                        "reason": "duplicate page-crop fallback; the table "
                                  "recreation is already inserted"})
            linked_assets = [asset for asset in linked_assets
                             if asset.get("kind") != "page_crop"]
        # Uncaptioned, very wide pictures are page watermarks, not diagrams.
        for asset in list(linked_assets):
            if (asset.get("kind") == "picture" and not asset.get("label")
                    and not asset.get("caption")
                    and (asset.get("width_px") or 0)
                    and (asset.get("height_px") or 1)
                    and asset["width_px"] / asset["height_px"] > 3.5):
                skipped_assets.append({
                    "id": asset["id"], "question_id": question["id"],
                    "reason": "decorative page watermark"})
        linked_assets = [
            asset for asset in linked_assets
            if not (asset.get("kind") == "picture"
                    and not asset.get("label") and not asset.get("caption")
                    and (asset.get("width_px") or 0)
                    and (asset.get("height_px") or 1)
                    and asset["width_px"] / asset["height_px"] > 3.5)]
        for asset in linked_assets:
            expected_assets.append(asset["id"])
            by_target.setdefault(_asset_target(asset, preamble, subparts),
                                 []).append(asset)
        intro, instructions = _split_preamble(preamble, linked_assets)
        schema = category == "sql"
        dash_spacing = category == "erd"
        if intro:
            _render_preamble(doc, intro, schema=schema,
                             dash_spacing=dash_spacing)
        lead_in = instructions.lower().startswith(
            ("based on", "the following", "figure", "table"))
        if instructions and lead_in:
            _render_preamble(doc, instructions, schema=schema,
                             dash_spacing=dash_spacing)
        for asset in by_target.get(("pre", -1), []):
            if _add_asset(doc, asset, scaling.get(asset["id"], {})):
                inserted_assets.append(asset["id"])
            if scaling.get(asset["id"], {}).get("mode") == "image":
                images_expected += 1
        if instructions and not lead_in:
            _render_preamble(doc, instructions, schema=schema,
                             dash_spacing=dash_spacing)
        for index, part in enumerate(subparts):
            _render_subpart(doc, part["label"], part.get("text") or "",
                            part.get("marks"))
            for asset in by_target.get(("part", index), []):
                if _add_asset(doc, asset, scaling.get(asset["id"], {})):
                    inserted_assets.append(asset["id"])
                if scaling.get(asset["id"], {}).get("mode") == "image":
                    images_expected += 1
    paper_docx = out / "paper.docx"
    paper_pdf = out / "paper.pdf"
    doc.save(str(paper_docx))
    pages = export_pdf(paper_docx, paper_pdf)
    _update_page_count(paper_docx, pages)
    pages = export_pdf(paper_docx, paper_pdf)
    qa = _qa(paper_pdf, plan, images_expected)
    missing_assets = sorted(set(expected_assets) - set(inserted_assets))
    qa["assets"] = {
        "expected": len(expected_assets),
        "inserted": len(inserted_assets),
        "skipped": skipped_assets,
        "missing": missing_assets,
    }
    if missing_assets:
        qa["problems"].append(
            "missing attachments: " + ", ".join(missing_assets))
    save_json(out / "plan.json", plan)
    save_json(out / "qa.json", qa)
    save_json(out / "meta.json",
              _library_meta(seed, plan, qa, paper_docx, paper_pdf))
    if qa["problems"]:
        raise RuntimeError(f"seed {seed} QA failed: {qa['problems']}")
    return {"seed": seed, "pages": pages, "images": qa["images"],
            "path": str(out)}


def _library_markdown(manifest: dict) -> str:
    lines = [
        "# ICT450 — V6 Library",
        "",
        f"Date: **{time.strftime('%Y-%m-%d', time.gmtime())}**",
        "",
        f"Library size: **{manifest['library_size']}** "
        f"(policy `{manifest['size_policy']}`); "
        f"reuse cap **{manifest['reuse_cap']}**.",
        "",
        "| Seed | Q1 | Q2 | Q3 | Q4 | Q5 | Marks | Pages | Attachments | Scheme |",
        "|---|---|---|---|---|---|---:|---:|---:|---:|",
    ]
    for row in manifest["seeds"]:
        cells = [row["question_id"] for row in row["questions"]]
        scheme = (f"{row['scheme_pages']} pages"
                  if row.get("scheme_pages") else "—")
        lines.append(
            f"| {row['seed']} | " + " | ".join(cells) +
            f" | {row['marks']} | {row['pages']} | "
            f"{row['assets_inserted']}/{row['assets_expected']} | "
            f"{scheme} |")
    lines += [
        "",
        "## Feasibility",
        "",
        f"- Approved questions: {manifest['feasibility']['approved_questions']}.",
        f"- Usable questions: {manifest['feasibility']['usable_questions']}.",
        f"- Excluded from selection: "
        f"{len(manifest['feasibility']['excluded_questions'])} "
        "(subpart label gap or marks do not reconcile).",
        "- By category: " + ", ".join(
            f"{key} {value}" for key, value in
            manifest["feasibility"]["by_category"].items()) + ".",
        f"- Distinct seeds without reuse: "
        f"{manifest['feasibility']['distinct_seeds_without_reuse']}.",
        f"- Capacity with reuse cap: "
        f"{manifest['feasibility']['capacity_with_reuse_cap']}.",
        "",
        "## Reuse",
        "",
        f"- Maximum uses of one question: "
        f"{manifest['reuse']['max_uses']} (cap {manifest['reuse_cap']}).",
    ]
    return "\n".join(lines) + "\n"


def build_library(seed_count: int = 20, *, reuse_cap: int = 4,
                  force: bool = False) -> dict:
    """Build the V6 Library cache and its feasibility/reuse manifests."""
    store = BankStore(BANK)
    questions = list(store.approved_questions())
    categories = _category_map()
    def _excluded(question: dict) -> list[str]:
        flags = [str(flag) for flag in (question.get("review_flags") or [])]
        reasons = []
        if "subpart label gap" in flags:
            reasons.append("subpart label gap")
        if any(flag.lower().startswith("marks ") for flag in flags):
            reasons.append("marks do not reconcile")
        return reasons

    usable = [question for question in questions
              if categories.get(str(question.get("id"))) in CATEGORIES
              and not _excluded(question)]
    excluded = [{"question_id": question["id"],
                 "reasons": _excluded(question)}
                for question in questions if _excluded(question)]
    cat_counts = Counter(str(categories[str(question["id"])])
                         for question in usable)
    capacity = min(cat_counts[category] * reuse_cap
                   for category in CATEGORIES)
    requested = min(int(seed_count), capacity)
    while requested > 0:
        try:
            plans = build_category_plans(questions, seed_count=requested,
                                         reuse_cap=reuse_cap)
        except ValueError:
            requested -= 1
            continue
        break
    if requested == 0:
        raise SystemExit("ICT450: no feasible seed plan")
    for plan in plans:
        validate_seed_plan(plan, store, expected_slots=5,
                           require_assets=True, require_content_hash=True,
                           check_part=True)
    cache_root = config.WEB_CACHE_DIR / SUBJECT
    cache_root.mkdir(parents=True, exist_ok=True)
    from src.app.jobs import cache_path
    rows = []
    reuse: Counter[str] = Counter()
    for seed, plan in enumerate(plans, start=1):
        seed_ids = [str(slot["question_id"]) for slot in plan["slots"]]
        reuse.update(seed_ids)
        out = cache_path("realistic", seed, None, subject=SUBJECT)
        if seed <= 3 and (OUT / f"seed_{seed:02d}" /
                          "paper.docx").exists():
            source = OUT / f"seed_{seed:02d}"
            out.mkdir(parents=True, exist_ok=True)
            for name in ("paper.docx", "paper.pdf", "plan.json", "qa.json"):
                shutil.copy2(source / name, out / name)
            qa = json.loads((out / "qa.json").read_text(encoding="utf-8"))
            save_json(out / "meta.json", _library_meta(
                seed, plan, qa, out / "paper.docx", out / "paper.pdf"))
            result = {"seed": seed, "cached": True, "path": str(out)}
        else:
            result = build_seed(seed, plan, force=force, out_dir=out)
        qa = json.loads((out / "qa.json").read_text(encoding="utf-8"))
        meta = json.loads((out / "meta.json").read_text(encoding="utf-8"))
        rows.append({
            "seed": seed,
            "marks": qa["marks_total"],
            "pages": qa["pages"],
            "source_questions": len(plan["slots"]),
            "assets_expected": qa.get("assets", {}).get("expected", 0),
            "assets_inserted": qa.get("assets", {}).get("inserted", 0),
            "assets_missing": qa.get("assets", {}).get("missing", []),
            "source_papers": meta["source_papers"],
            "questions": [
                {"slot": slot["slot"], "category": slot["category"],
                 "question_id": slot["question_id"],
                 "source_paper": slot["source_paper"],
                 "marks": slot["marks"]}
                for slot in plan["slots"]],
            "files": meta["files"],
            "qa_problems": qa.get("problems", []),
        })
        print(result, flush=True)
    reuse_rows = []
    for question_id, uses in sorted(reuse.items()):
        reuse_rows.append({
            "question_id": question_id,
            "uses": uses,
            "seeds": [row["seed"] for row in rows
                      if any(question["question_id"] == question_id
                             for question in row["questions"])],
        })
    reuse_payload = {
        "subject": SUBJECT,
        "reuse_cap": reuse_cap,
        "max_uses": max(reuse.values()),
        "within_cap": max(reuse.values()) <= reuse_cap,
        "questions": reuse_rows,
    }
    manifest = {
        "schema_version": 1,
        "subject": SUBJECT,
        "generated": time.time(),
        "library_size": len(plans),
        "size_policy": "min(20, feasible)",
        "reuse_cap": reuse_cap,
        "feasibility": {
            "approved_questions": len(questions),
            "usable_questions": len(usable),
            "excluded_questions": excluded,
            "by_category": dict(sorted(cat_counts.items())),
            "distinct_seeds_without_reuse": min(
                cat_counts[category] for category in CATEGORIES),
            "capacity_with_reuse_cap": capacity,
            "library_size": len(plans),
        },
        "reuse": {
            "reuse_cap": reuse_cap,
            "max_uses": max(reuse.values()),
            "within_cap": max(reuse.values()) <= reuse_cap,
        },
        "seeds": rows,
    }
    save_json(cache_root / "library_manifest.json", manifest)
    save_json(cache_root / "reuse_report.json", reuse_payload)
    (cache_root / "library_manifest.md").write_text(
        _library_markdown(manifest), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", default="1-3")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--library", action="store_true")
    args = parser.parse_args()
    if "-" in args.seeds:
        first, last = args.seeds.split("-")
        seeds = list(range(int(first), int(last) + 1))
    else:
        seeds = [int(value) for value in args.seeds.split(",")]
    if args.library:
        manifest = build_library(seed_count=max(seeds), force=args.force)
        print({"library_size": manifest["library_size"],
               "reuse_max": manifest["reuse"]["max_uses"],
               "within_cap": manifest["reuse"]["within_cap"]}, flush=True)
        return
    store = BankStore(BANK)
    questions = list(store.approved_questions())
    plans = build_category_plans(questions, seed_count=max(seeds),
                                 reuse_cap=4)
    for plan in plans:
        validate_seed_plan(plan, store, expected_slots=5,
                           require_assets=True, require_content_hash=True,
                           check_part=True)
    for seed in seeds:
        plan = plans[seed - 1]
        save_json(BANK / "plans" / f"seed_{seed:02d}.json", plan)
        print(build_seed(seed, plan, force=args.force), flush=True)


if __name__ == "__main__":
    main()
