"""V2 database-aware bank for the ICT450 pilot.

Rules from the Phase 4 amendment:

* SQL/code text is kept exactly as extracted, including indentation and line
  breaks; nothing is “fixed”.
* A native table is accepted only when the PDF text layer and the MinerU HTML
  agree on every row's token sequence and cell count; otherwise the page crop
  is kept.
* Figures, ER diagrams, flowcharts and code images are cropped from the source
  page and linked by caption, then by position.
* Every unresolved reference is reported, not invented.

Run:
    uv run python -m src.subjects.ict450.bank_build
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

import pymupdf
from PIL import Image

from src import config
from src.bank.duplicates import cluster_duplicates, near_duplicate_pairs
from src.bank.quality import quality_band, quality_score
from src.bank.review import build_review_sheet
from src.bank.schema import normalize_text, question_content_hash
from src.bank.store import BankStore, save_json
from src.subjects.ict450.papers import SUBJECT

TRACKING = config.TRACKING_DIR / "ict450" / "v2"
BANK = TRACKING / "bank"
REGISTER = TRACKING / "papers_register.json"
STATUS = TRACKING / "extraction_status.json"
REPORT_JSON = BANK / "gate1_report.json"
REPORT_MD = BANK / "gate1_report.md"

MARKS_RE = re.compile(r"\(?\s*(\d{1,3})\s*marks?\s*\)?", re.I)
TOP_LABEL_RE = re.compile(r"(?m)^\s*\(?([a-h])\)\s*")
ROMAN_LABEL_RE = re.compile(r"(?m)^\s*\(?(i|ii|iii|iv|v|vi|vii)\)\s*", re.I)
MARK_LINE_RE = re.compile(r"^\s*\(\s*\d{1,3}\s*marks?\s*\)\s*$", re.I)
QUESTION_LINE_RE = re.compile(r"^\s*QUESTION\s+\d{1,3}\s*$", re.I)
NOISE_LINE_RE = re.compile(
    r"^\s*(CONFIDENTIAL|©?\s*Hak Cipta.*|CD/.*ICT450.*|"
    r"CS/.*ICT450.*|\d{1,2})\s*$", re.I)
# MinerU returns markdown text; these escapes are formatting, not source
# characters.  Undo them without touching whitespace, indentation or SQL.
MARKDOWN_ESCAPE_RE = re.compile(r"\\([_%*#\[\]()>+.!-])")
REF_RE = re.compile(r"\b(Figure|Table)\s+(\d+)\b", re.I)
CODE_RE = re.compile(
    r"(\bSELECT\b[\s\S]{0,200}?\bFROM\b|"
    r"\bINSERT\s+INTO\s+\w+\s*\(|"
    r"\bUPDATE\s+\w+\s+SET\b|"
    r"\bDELETE\s+FROM\s+\w+|"
    r"\bCREATE\s+TABLE\s+\w+\s*\(|"
    r"\bALTER\s+TABLE\s+\w+|"
    r"\bDROP\s+TABLE\s+\w+)", re.I)


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: str | None = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._row = []
        elif tag in {"td", "th"}:
            self._cell = ""

    def handle_endtag(self, tag):
        if tag in {"td", "th"} and self._row is not None:
            self._row.append(self._cell or "")
            self._cell = None
        elif tag == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell += data


def html_rows(html: str) -> list[list[str]]:
    parser = _TableParser()
    parser.feed(html or "")
    return parser.rows


def _tokens(value: str) -> list[str]:
    cleaned = re.sub(r"[^0-9A-Za-z]+", " ", str(value or "")).lower()
    return [token for token in cleaned.split() if token]


def _row_tokens(rows: list[list[str]]) -> list[list[str]]:
    return [[token for cell in row for token in _tokens(cell)]
            for row in rows]


def _page_rows(pdf_path: Path, page_idx: int,
               bbox: list[float]) -> list[list[str]]:
    with pymupdf.open(str(pdf_path)) as pdf:
        page = pdf[page_idx]
        width, height = page.rect.width, page.rect.height
        x0, y0, x1, y1 = [float(value) for value in bbox]
        if max(x0, y0, x1, y1) <= 1000:
            x0, y0 = x0 / 1000 * width, y0 / 1000 * height
            x1, y1 = x1 / 1000 * width, y1 / 1000 * height
        words = page.get_text("words", clip=pymupdf.Rect(x0, y0, x1, y1))
    lines: dict[int, list[tuple[float, str]]] = defaultdict(list)
    for word in words:
        y = (float(word[1]) + float(word[3])) / 2
        lines[round(y / 4)].append((float(word[0]), str(word[4])))
    rows = []
    for key in sorted(lines):
        rows.append([text for _, text in sorted(lines[key])])
    return rows


def native_table_check(html: str, pdf_path: Path, page_idx: int,
                       bbox: list[float]) -> dict:
    rows = html_rows(html)
    if not rows:
        return {"accepted": False, "reason": "MinerU table HTML is empty"}
    widths = {len(row) for row in rows}
    if len(widths) != 1:
        return {"accepted": False,
                "reason": "MinerU table has merged or uneven cells",
                "html_rows": len(rows), "html_widths": sorted(widths)}
    pdf_rows = _page_rows(pdf_path, page_idx, bbox)
    if not pdf_rows:
        return {"accepted": False,
                "reason": "PDF has no text layer at the table position",
                "html_rows": len(rows)}
    left = [tokens for tokens in _row_tokens(rows)]
    right = [[token for word in row for token in _tokens(word)]
             for row in pdf_rows]
    if len(left) != len(right):
        return {"accepted": False,
                "reason": "row count differs",
                "html_rows": len(left), "pdf_rows": len(right)}
    for index, (html_row, pdf_row) in enumerate(zip(left, right)):
        if html_row != pdf_row:
            return {"accepted": False,
                    "reason": f"row {index + 1} text differs",
                    "html_row": html_row, "pdf_row": pdf_row}
    return {"accepted": True, "reason": "cell text and counts match",
            "rows": len(rows), "columns": widths.pop()}


def _crop_page(page_png: Path, bbox: list[float], out: Path) -> None:
    with Image.open(page_png) as source:
        image = source.convert("RGB")
        width, height = image.size
        x0, y0, x1, y1 = [float(value) for value in bbox]
        if max(x0, y0, x1, y1) <= 1000:
            x0, y0 = x0 / 1000 * width, y0 / 1000 * height
            x1, y1 = x1 / 1000 * width, y1 / 1000 * height
        box = (max(0, int(x0)), max(0, int(y0)),
               min(width, int(x1)), min(height, int(y1)))
        out.parent.mkdir(parents=True, exist_ok=True)
        image.crop(box).save(out, "PNG")


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _asset_kind(kind: str, caption: str, label: str = "") -> str:
    lower = f"{label} {caption}".lower()
    if lower.strip().startswith("table"):
        return "table"
    if lower.strip().startswith("figure"):
        return ("diagram"
                if any(word in lower for word in ("erd", "er diagram",
                                                  "diagram", "flowchart",
                                                  "schema"))
                else "figure")
    if any(word in lower for word in ("erd", "er diagram", "diagram",
                                      "flowchart", "schema")):
        return "diagram"
    if "figure" in lower:
        return "figure"
    return "table" if kind == "table" else "picture"


def _question_text(question: dict, blocks: list[dict]) -> tuple[str, str]:
    """Return ``(exact_text, clean_text)`` for one question.

    ``exact_text`` preserves MinerU's line breaks and indentation, undoing only
    Markdown punctuation escapes (``TEAM\\_ID`` -> ``TEAM_ID``).  ``clean_text``
    additionally removes the question heading, standalone mark lines and page
    header/footer noise; it never collapses spaces or line breaks inside
    SQL/code.
    """
    parts = []
    for block_id in question.get("blocks") or []:
        index = int(str(block_id)[1:]) - 1
        if 0 <= index < len(blocks):
            parts.append(str(blocks[index].get("text") or ""))
    raw = "\n".join(part for part in parts if part.strip())
    exact = MARKDOWN_ESCAPE_RE.sub(r"\1", raw)
    kept: list[str] = []
    heading_dropped = False
    for line in exact.splitlines():
        if not heading_dropped and QUESTION_LINE_RE.match(line):
            heading_dropped = True
            continue
        if MARK_LINE_RE.match(line) or NOISE_LINE_RE.match(line):
            continue
        kept.append(line)
    clean = "\n".join(kept).strip()
    return exact, clean


def _marks_layout(exact: str) -> dict:
    text = exact or ""
    marks = [(match.start(), int(match.group(1)))
             for match in MARKS_RE.finditer(text)]
    if not marks:
        return {"marks": None, "subparts": [], "marks_missing": True,
                "subpart_gap": False, "subpart_text": []}
    top = [(match.start(), match.group(1).lower())
           for match in TOP_LABEL_RE.finditer(text)]
    roman = [(match.start(), match.group(1).lower())
             for match in ROMAN_LABEL_RE.finditer(text)]
    if not top:
        return {"marks": marks[0][1], "subparts": [],
                "marks_missing": False, "subpart_gap": False,
                "subpart_text": []}
    subparts = []
    for index, (start, label) in enumerate(top):
        end = top[index + 1][0] if index + 1 < len(top) else len(text)
        nested = [(pos, name) for pos, name in roman if start < pos < end]
        local_marks = [value for pos, value in marks if start < pos < end]
        nested_expected = [f"i", "ii", "iii", "iv", "v", "vi", "vii"]
        gap = bool(nested) and nested[0][1] != "i"
        seen = [name for _, name in nested]
        gap = gap or any(seen[index] != nested_expected[index]
                         for index in range(min(len(seen),
                                                len(nested_expected))))
        full = text[start:end].strip()
        subparts.append({
            "label": label,
            "marks": sum(local_marks) if local_marks else None,
            "text": full,
            "nested_labels": seen,
            "has_nested_gap": gap,
        })
    return {
        "marks": sum(part["marks"] for part in subparts
                     if part["marks"] is not None),
        "subparts": subparts,
        "marks_missing": not any(part["marks"] for part in subparts),
        "subpart_gap": any(part["has_nested_gap"] for part in subparts),
        "subpart_text": [],
    }


def _paper_month(full_md: str) -> str:
    from src.subjects.ict450.papers import cover_month
    return cover_month(full_md[:4000])


def _build_question(paper: dict, question: dict, blocks: list[dict],
                    cache_dir: Path, pdf_path: Path, page_cache: Path,
                    assets: dict[str, dict], store: BankStore,
                    counter: list[int]) -> dict:
    qid = question["question_id"]
    exact, clean = _question_text(question, blocks)
    layout = _marks_layout(exact)
    pages = sorted({int(blocks[int(str(block)[1:]) - 1].get("page_idx", 0)) + 1
                    for block in question.get("blocks") or []
                    if 0 <= int(str(block)[1:]) - 1 < len(blocks)})
    refs = list(question.get("refs") or [])
    linked = []
    unresolved = []
    for aid in question.get("assets") or []:
        asset = assets.get(aid)
        if asset:
            linked.append(asset)
    linked_labels = {str(asset.get("label", "")).lower()
                     for asset in linked if asset.get("label")}
    for ref in refs:
        if ref.lower() not in linked_labels:
            unresolved.append(ref)
    code_like = bool(CODE_RE.search(clean))
    mentions_sql = bool(re.search(r"\bSQL\b", clean, re.I))
    question_record = {
        "schema_version": 2,
        "id": qid,
        "subject": SUBJECT,
        "source_paper": paper["paper_id"],
        "source_file": paper["file"],
        "source_pdf": str(pdf_path),
        "pages": pages,
        "part": "",
        "marks": layout["marks"],
        "subpart_marks": [
            {"label": part["label"], "marks": part["marks"],
             "nested_labels": part["nested_labels"]}
            for part in layout["subparts"]
        ],
        "subparts": [
            {"label": part["label"], "text": part["text"],
             "marks": part["marks"]}
            for part in layout["subparts"]
        ],
        "status": "extracted",
        "native_text_blocks": [{
            "id": question["question_id"],
            "page": pages[0] if pages else int(question.get("page_idx", 0)) + 1,
            "text": clean,
            "normalised": normalize_text(clean),
            "source_blocks": list(question.get("blocks") or []),
        }],
        "exact_text": exact,
        "exact_text_hash": hashlib.sha256(exact.encode("utf-8")).hexdigest(),
        "contains_sql_or_code": code_like,
        "mentions_sql": mentions_sql,
        "preserve_exact_text": True,
        "refs": refs,
        "refs_unresolved": unresolved,
        "assets": [asset["id"] for asset in linked],
        "fallback_assets": [],
        "topic_primary": "unclassified",
        "topic_tags": [],
        "review_flags": [],
        "quality_notes": [],
        "cache_dir": str(cache_dir),
    }
    if layout["marks_missing"]:
        question_record["review_flags"].append("marks missing")
    if layout["subpart_gap"]:
        question_record["review_flags"].append("subpart label gap")
    if unresolved:
        question_record["review_flags"].append("unresolved reference")
    if code_like:
        question_record["review_flags"].append("contains SQL/code")
    question_record["content_hash"] = question_content_hash(question_record)
    return question_record


def _build_assets(paper: dict, dossier: dict, questions: list[dict],
                  blocks: list[dict], cache_dir: Path, pdf_path: Path,
                  page_cache: Path, store: BankStore,
                  counter: list[int], unsure: list[dict],
                  discarded: list[dict]) -> dict[str, dict]:
    assets: dict[str, dict] = {}
    for asset in dossier.get("assets") or []:
        counter[0] += 1
        aid = f"{paper['paper_id']}-A{counter[0]:02d}"
        page = int(asset.get("page_idx", 0))
        label = str(asset.get("label") or "")
        caption = str(asset.get("caption") or "")
        kind = _asset_kind(str(asset.get("kind") or ""), caption, label)
        page_png = page_cache / f"page_{page + 1:03d}.png"
        crop = store.assets_dir / f"{aid}.png"
        _crop_page(page_png, asset.get("bbox") or [0, 0, 1000, 1000], crop)
        if (kind in {"picture", "figure", "diagram"} and not label
                and not caption and asset.get("question_index") is None):
            with Image.open(crop) as image:
                width, height = image.size
            if height and width / height > 3.5:
                discarded.append({
                    "id": aid,
                    "paper_id": paper["paper_id"],
                    "page": page + 1,
                    "kind": kind,
                    "reason": "unlinked, uncaptioned wide image (likely a "
                              "watermark or banner)",
                    "path": str(crop),
                })
                crop.unlink()
                continue
        native = native_table_check(asset.get("table_html") or "", pdf_path,
                                    page, asset.get("bbox") or [])
        treatment = "native_table" if native.get("accepted") else "crop"
        linked_by = "caption" if label else "position"
        record = {
            "schema_version": 2,
            "id": aid,
            "subject": SUBJECT,
            "source_paper": paper["paper_id"],
            "source_file": paper["file"],
            "source_pdf": str(pdf_path),
            "kind": kind,
            "label": label,
            "caption": caption,
            "page": page + 1,
            "content_bbox": asset.get("bbox") or [],
            "caption_bbox": None,
            "treatment": treatment,
            "verdict": "pending",
            "sha256": _sha256(crop),
            "crop_path": str(crop),
            "linked_by": linked_by,
            "native_check": native,
            "native_table": None,
            "mineru_asset": asset.get("asset_id"),
            "mineru_table_html": asset.get("table_html") or "",
        }
        if native.get("accepted"):
            rows = html_rows(asset.get("table_html") or "")
            record["native_table"] = {
                "rows": [{"cells": [{"text": cell, "colspan": 1}
                                    for cell in row]} for row in rows]
            }
        if kind in {"figure", "diagram", "picture"}:
            owner_index = asset.get("question_index")
            owner = (questions[owner_index]
                     if isinstance(owner_index, int)
                     and 0 <= owner_index < len(questions) else {})
            if owner.get("mentions_sql") and not owner.get(
                    "contains_sql_or_code"):
                record["code_asset"] = True
                unsure.append({
                    "code": "CODE_IMAGE",
                    "stage": "V2_bank",
                    "paper_id": paper["paper_id"],
                    "page": page + 1,
                    "detail": "image asset in a SQL/code question; keep the "
                              "crop and verify no code text was lost",
                    "path": str(crop),
                })
        save_json(store.asset_path(aid), record)
        assets[asset.get("asset_id")] = record
    for fallback in dossier.get("fallback") or []:
        counter[0] += 1
        aid = f"{paper['paper_id']}-F{counter[0]:02d}"
        page = int(fallback.get("page_idx", 0))
        label = str(fallback.get("label") or "")
        source = Path(fallback.get("path") or "")
        crop = store.assets_dir / f"{aid}.png"
        if source.is_file():
            with Image.open(source) as image:
                image.convert("RGB").save(crop, "PNG")
        record = {
            "schema_version": 2,
            "id": aid,
            "subject": SUBJECT,
            "source_paper": paper["paper_id"],
            "source_file": paper["file"],
            "source_pdf": str(pdf_path),
            "kind": "page_crop",
            "label": label,
            "caption": "",
            "page": page + 1,
            "content_bbox": [],
            "caption_bbox": None,
            "treatment": "page_crop_fallback",
            "verdict": "pending",
            "sha256": _sha256(crop) if crop.is_file() else "",
            "crop_path": str(crop),
            "linked_by": "fallback",
            "native_check": {"accepted": False,
                             "reason": fallback.get("reason", "")},
            "native_table": None,
            "mineru_asset": fallback.get("asset_id"),
            "mineru_table_html": "",
        }
        save_json(store.asset_path(aid), record)
        assets[fallback.get("asset_id")] = record
        unsure.append({
            "code": "REFERENCE_FALLBACK",
            "stage": "V2_bank",
            "paper_id": paper["paper_id"],
            "page": page + 1,
            "detail": f"{label or 'reference'} has no MinerU asset; page crop "
                      "kept",
            "path": str(crop),
        })
    return assets


def build() -> dict:
    register = json.loads(REGISTER.read_text(encoding="utf-8"))
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    store = BankStore(BANK)
    # Rebuild generated artifacts; keep owner approvals/corrections.
    for path in (store.questions_dir, store.assets_dir, store.review_dir):
        if path.exists():
            shutil.rmtree(path)
    for name in ("index.json", "unsure.json", "duplicates.json",
                 "gate1_report.json", "gate1_report.md"):
        path = BANK / name
        if path.exists():
            path.unlink()
    store.ensure()
    unsure: list[dict] = []
    discarded: list[dict] = []
    built_questions: list[dict] = []
    paper_rows: list[dict] = []
    counter = [0]
    for paper in register.get("unique_papers") or []:
        entry = (status.get("papers") or {}).get(paper["paper_id"]) or {}
        if entry.get("status") != "done":
            unsure.append({
                "code": "EXTRACTION_MISSING",
                "stage": "V2_bank",
                "paper_id": paper["paper_id"],
                "page": None,
                "detail": entry.get("error", "no MinerU dossier"),
                "path": str(STATUS),
            })
            continue
        cache_dir = Path(entry.get("cache_dir") or "")
        normalized_path = cache_dir / "review" / "normalized.json"
        dossier = json.loads(normalized_path.read_text(encoding="utf-8"))
        content_path = Path(dossier.get("content_list") or "")
        blocks = json.loads(content_path.read_text(encoding="utf-8"))
        pdf_path = config.PAPERS_ROOT / SUBJECT / paper["file"]
        page_cache = cache_dir / "review" / "pages"
        paper_assets: dict[str, dict] = {}
        paper_questions: list[dict] = []
        # Build assets first so question linking can see them.
        raw_questions = dossier.get("questions") or []
        for question in raw_questions:
            record = _build_question(paper, question, blocks, cache_dir,
                                     pdf_path, page_cache, paper_assets,
                                     store, counter)
            paper_questions.append(record)
        paper_assets = _build_assets(paper, dossier, paper_questions, blocks,
                                     cache_dir, pdf_path, page_cache, store,
                                     counter, unsure, discarded)
        # Re-run linking now that assets exist.
        fallbacks_by_qid: dict[str, list[dict]] = defaultdict(list)
        for fallback in dossier.get("fallback") or []:
            fallbacks_by_qid[str(fallback.get("question_id"))].append(fallback)
        for index, question in enumerate(raw_questions):
            record = paper_questions[index]
            linked = [paper_assets[aid] for aid in question.get("assets") or []
                      if aid in paper_assets]
            fallback_by_id = {
                asset["id"]: asset for asset in paper_assets.values()
                if asset.get("linked_by") == "fallback"}
            fallback_ids = [
                paper_assets[item["asset_id"]]["id"]
                for item in fallbacks_by_qid.get(question["question_id"], [])
                if item.get("asset_id") in paper_assets]
            labels = {str(asset.get("label", "")).lower()
                      for asset in linked if asset.get("label")}
            unresolved = [ref for ref in record.get("refs") or []
                          if ref.lower() not in labels]
            unlabeled = [asset for asset in linked if not asset.get("label")]
            if len(unresolved) == 1 and len(unlabeled) == 1:
                ref = unresolved[0]
                wants_table = ref.lower().startswith("table")
                asset = unlabeled[0]
                if (asset.get("kind") == "table") == wants_table:
                    asset["label"] = ref
                    asset["linked_by"] = "position"
                    save_json(store.asset_path(asset["id"]), asset)
                    labels.add(ref.lower())
                    unresolved = []
                    for fallback_id in list(fallback_ids):
                        fallback = fallback_by_id.get(fallback_id)
                        if fallback and fallback.get("label", "").lower() == (
                                ref.lower()):
                            fallback["superseded_by"] = asset["id"]
                            save_json(store.asset_path(fallback_id), fallback)
                            fallback_ids.remove(fallback_id)
                            unsure[:] = [
                                item for item in unsure
                                if not (item.get("code") == "REFERENCE_FALLBACK"
                                        and item.get("path")
                                        == fallback.get("crop_path"))]
            record["assets"] = [asset["id"] for asset in linked] + fallback_ids
            record["fallback_assets"] = fallback_ids
            record["refs_unresolved"] = unresolved
            record["review_flags"] = [
                flag for flag in record.get("review_flags") or []
                if flag not in {"unresolved reference", "contains SQL/code"}]
            record["content_hash"] = question_content_hash(record)
            for asset in linked:
                if asset.get("treatment") == "crop":
                    record["quality_notes"].append(
                        f"{asset.get('label') or asset['id']} kept as a crop")
            if record.get("contains_sql_or_code"):
                record["review_flags"].append("contains SQL/code")
            if record["refs_unresolved"]:
                record["review_flags"].append("unresolved reference")
                for ref in record["refs_unresolved"]:
                    unsure.append({
                        "code": "UNRESOLVED_REFERENCE",
                        "stage": "V2_bank",
                        "paper_id": paper["paper_id"],
                        "question_id": record["id"],
                        "page": record["pages"][0] if record["pages"] else None,
                        "detail": f"{ref} is referenced but no linked asset "
                                  "carries that caption",
                        "path": str(cache_dir / "review" / "normalized.json"),
                    })
            save_json(store.question_path(record["id"]), record)
        paper_questions_built = paper_questions
        linked_ids = {aid for row in paper_questions_built
                      for aid in row.get("assets") or []}
        for asset in paper_assets.values():
            if asset["id"] in linked_ids or asset.get("superseded_by"):
                continue
            unsure.append({
                "code": "UNLINKED_ASSET",
                "stage": "V2_bank",
                "paper_id": paper["paper_id"],
                "page": asset.get("page"),
                "detail": f"{asset.get('kind')} asset "
                          f"{asset.get('label') or asset['id']} has no "
                          "caption or position link to a question",
                "path": asset.get("crop_path"),
            })
        # Marks consistency: compare each question with the modal total in
        # the paper.  A deviation is reported, never corrected.
        totals = [row["marks"] for row in paper_questions_built
                  if isinstance(row.get("marks"), int) and row["marks"] > 0]
        modal = Counter(totals).most_common(1)[0][0] if totals else None
        for row in paper_questions_built:
            if modal is not None and row.get("marks") != modal:
                row["marks_suspect"] = True
                row["review_flags"].append(
                    f"marks {row.get('marks')} differ from paper mode {modal}")
                if row["status"] == "extracted":
                    row["status"] = "needs_fix"
                unsure.append({
                    "code": "MARKS_MISMATCH",
                    "stage": "V2_bank",
                    "paper_id": paper["paper_id"],
                    "question_id": row["id"],
                    "page": row["pages"][0] if row["pages"] else None,
                    "detail": f"visible marks {row.get('marks')} differ from "
                              f"the paper's modal question total {modal}; "
                              "a sub-part may be missing",
                    "path": str(cache_dir / "review" / "normalized.json"),
                })
            row["review_flags"] = sorted(set(row.get("review_flags") or []))
            if row.get("review_flags"):
                if row["status"] == "extracted":
                    row["status"] = "needs_fix"
            assets_map = {asset["id"]: asset for asset in paper_assets.values()}
            row["quality_score"] = quality_score(row, assets_map)
            row["quality_band"] = quality_band(row["quality_score"])
            save_json(store.question_path(row["id"]), row)
            built_questions.append(row)
        month = _paper_month(
            (cache_dir / "full.md").read_text(encoding="utf-8")
            if (cache_dir / "full.md").is_file() else "")
        if month and month != paper.get("month_year"):
            unsure.append({
                "code": "MONTH_MISMATCH",
                "stage": "V1_extract",
                "paper_id": paper["paper_id"],
                "page": 1,
                "detail": f"register month {paper.get('month_year')} but "
                          f"MinerU cover says {month}",
                "path": str(cache_dir / "full.md"),
            })
        if not month and paper.get("month_source") != "pdf_text":
            unsure.append({
                "code": "MONTH_UNVERIFIED",
                "stage": "V1_extract",
                "paper_id": paper["paper_id"],
                "page": 1,
                "detail": f"cover has no readable month/year; paper id "
                          f"{paper['paper_id']} is provisional",
                "path": str(cache_dir / "full.md"),
            })
        paper_rows.append({
            "paper_id": paper["paper_id"],
            "file": paper["file"],
            "pages": paper["pages"],
            "month_from_cover": month,
            "questions": len(paper_questions_built),
            "assets": len(paper_assets),
            "modal_marks": modal,
            "unresolved_refs": sum(
                len(row.get("refs_unresolved") or [])
                for row in paper_questions_built),
        })
    clusters = cluster_duplicates(built_questions)
    for cluster in clusters:
        if cluster["count"] < 2:
            continue
        for qid in cluster["ids"]:
            record = store.load_question(qid)
            if record:
                record["duplicate_cluster"] = cluster["canonical_id"]
                save_json(store.question_path(qid), record)
    duplicate_clusters = [row for row in clusters if row["count"] > 1]
    questions = list(store.questions())
    near_duplicates = near_duplicate_pairs(questions)
    all_assets = list(store.assets())
    linked_asset_ids = {aid for row in questions
                        for aid in row.get("assets") or []}
    unlinked_assets = [row for row in all_assets
                       if row.get("id") not in linked_asset_ids
                       and not row.get("superseded_by")]
    kinds = Counter(str(row.get("kind")) for row in all_assets)
    statuses = Counter(str(row.get("status")) for row in questions)
    unresolved = sum(len(row.get("refs_unresolved") or [])
                     for row in built_questions)
    low_quality = [row for row in built_questions
                   if row.get("quality_band") == "low"]
    needs_fix = [row for row in questions
                 if row.get("status") == "needs_fix"]
    scores = [row.get("quality_score", 0.0) for row in questions]
    index = {
        "schema_version": 2,
        "subject": SUBJECT,
        "generated_on": datetime.now(timezone.utc).isoformat(),
        "papers": len(paper_rows),
        "questions": len(questions),
        "assets": sum(kinds.values()),
        "asset_kinds": dict(sorted(kinds.items())),
        "status": dict(sorted(statuses.items())),
        "duplicate_clusters": len(duplicate_clusters),
        "duplicate_questions": sum(row["count"] - 1
                                   for row in duplicate_clusters),
        "near_duplicate_pairs": len(near_duplicates),
        "unresolved_references": unresolved,
        "unlinked_assets": len(unlinked_assets),
        "decorative_images_skipped": len(discarded),
        "low_quality": len(low_quality),
        "needs_fix": len(needs_fix),
        "quality_average": round(sum(scores) / len(scores), 3) if scores else 0,
        "native_tables": sum(1 for row in store.assets()
                             if row.get("treatment") == "native_table"),
        "crops": sum(1 for row in store.assets()
                     if row.get("treatment") == "crop"),
        "fallback_crops": sum(1 for row in store.assets()
                              if row.get("treatment") == "page_crop_fallback"),
        "code_questions": sum(1 for row in questions
                              if row.get("contains_sql_or_code")),
        "sql_answer_questions": sum(1 for row in questions
                                    if row.get("mentions_sql")),
        "exact_text_questions": sum(1 for row in questions
                                    if row.get("preserve_exact_text")),
        "unsure": len(unsure),
        "paper_rows": paper_rows,
    }
    save_json(BANK / "index.json", index)
    save_json(BANK / "unsure.json", {
        "schema_version": 2, "subject": SUBJECT, "items": unsure})
    save_json(BANK / "duplicates.json", {
        "schema_version": 2, "subject": SUBJECT,
        "clusters": duplicate_clusters,
        "near_duplicates": near_duplicates})
    if not store.corrections_path.exists():
        save_json(store.corrections_path,
                  {"schema_version": 2, "subject": SUBJECT, "by_qid": {}})
    if not store.approvals_path.exists():
        save_json(store.approvals_path,
                  {"schema_version": 1, "by_qid": {}})
    build_review_sheet(store, store.review_dir, subject=SUBJECT,
                       title="ICT450 question bank")
    report = {
        "schema_version": 2,
        "subject": SUBJECT,
        "stage": "V2_bank",
        "gate": "A",
        "status": "awaiting_owner_review",
        "generated_on": datetime.now(timezone.utc).isoformat(),
        "index": index,
        "unsure": unsure,
        "decorative_images_skipped": discarded,
        "low_quality": [
            {"id": row["id"], "marks": row.get("marks"),
             "score": row.get("quality_score"),
             "flags": row.get("review_flags")}
            for row in low_quality],
        "needs_fix": [
            {"id": row["id"], "marks": row.get("marks"),
             "page": (row.get("pages") or [None])[0],
             "flags": row.get("review_flags")}
            for row in needs_fix],
        "mineru": {
            "model": status.get("model"),
            "documents_uploaded": (status.get("summary") or {}).get(
                "documents_uploaded", 0),
            "daily_limit": 5000,
            "cost_usd": 0.0,
        },
        "what_changed": [
            "Built the ICT450 v2 bank from the MinerU VLM dossiers.",
            "Kept SQL/code text blocks exact; no SQL was rewritten.",
            "Accepted native tables only on an exact PDF/HTML row match.",
            "Kept page crops for every figure, diagram and unmatched table.",
            "Recorded unresolved references, mark gaps and low-quality items.",
            "Generated the CSC429-style review sheet.",
        ],
    }
    save_json(REPORT_JSON, report)
    lines = [
        "# ICT450 — V2 bank / Gate A report",
        "",
        f"Status: **{report['status']}**",
        "",
        "## Counts",
        "",
        f"- Papers: {index['papers']}",
        f"- Questions: {index['questions']}",
        f"- Assets: {index['assets']} ("
        + ", ".join(f"{key}={value}" for key, value
                    in index["asset_kinds"].items()) + ")",
        f"- Question status: "
        + ", ".join(f"{key}={value}" for key, value
                    in index["status"].items()),
        f"- Duplicate clusters: {index['duplicate_clusters']} "
        f"({index['duplicate_questions']} duplicate questions)",
        f"- Near-duplicate pairs (review aid): "
        f"{index['near_duplicate_pairs']}",
        f"- Unresolved references: {index['unresolved_references']}",
        f"- Unlinked assets: {index['unlinked_assets']}",
        f"- Decorative images skipped: "
        f"{index['decorative_images_skipped']}",
        f"- Needs-fix questions: {index['needs_fix']}",
        f"- Low-quality questions: {index['low_quality']}",
        f"- SQL/code text blocks kept exact: {index['code_questions']}",
        f"- Questions that ask for SQL: {index['sql_answer_questions']}",
        f"- Questions with exact-text hashes: {index['exact_text_questions']}",
        f"- Native tables accepted: {index['native_tables']}",
        f"- Table/figure crops: {index['crops']}",
        f"- Page-crop fallbacks: {index['fallback_crops']}",
        "",
        "## MinerU",
        "",
        f"- Model: {report['mineru']['model']}",
        f"- Documents uploaded: {report['mineru']['documents_uploaded']} "
        f"of {report['mineru']['daily_limit']} daily",
        f"- Cost: ${report['mineru']['cost_usd']:.2f}",
        "",
        "## Paper detail",
        "",
        "| Paper | Pages | Questions | Assets | Modal marks | Unresolved |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in paper_rows:
        lines.append(
            f"| {row['paper_id']} | {row['pages']} | {row['questions']} | "
            f"{row['assets']} | {row['modal_marks']} | "
            f"{row['unresolved_refs']} |")
    lines += ["", "## Needs-fix questions", ""]
    if not needs_fix:
        lines.append("None.")
    else:
        lines += ["| Question | Marks | Page | Flags |", "|---|---:|---:|---|"]
        for row in needs_fix:
            lines.append(
                f"| {row['id']} | {row.get('marks')} | "
                f"{(row.get('pages') or [None])[0]} | "
                f"{'; '.join(row.get('review_flags') or [])} |")
    lines += ["", "## Low-quality questions", ""]
    if not low_quality:
        lines.append("None.")
    else:
        lines += ["| Question | Marks | Score | Flags |", "|---|---:|---:|---|"]
        for row in low_quality:
            lines.append(
                f"| {row['id']} | {row.get('marks')} | "
                f"{row.get('quality_score')} | "
                f"{'; '.join(row.get('review_flags') or [])} |")
    lines += ["", "## Duplicate clusters", ""]
    if not duplicate_clusters:
        lines.append("None.")
    for cluster in duplicate_clusters:
        lines.append(
            f"- canonical `{cluster['canonical_id']}` — "
            f"{cluster['count']} questions: "
            + ", ".join(f"`{qid}`" for qid in cluster["ids"]))
    if near_duplicates:
        lines += ["", "Potential repeats (Jaccard >= 0.70):", ""]
        for pair in near_duplicates:
            lines.append(
                f"- `{pair['left']}` ~ `{pair['right']}` "
                f"(score {pair['score']})")
    lines += [
        "",
        "## Table treatment",
        "",
        "A table is native only when the PDF text layer and MinerU HTML agree",
        "on every row's token sequence and cell count. Otherwise the source",
        "crop is kept. Scanned pages without a text layer always keep the crop.",
        "",
    ]
    lines += ["", "## Decorative images skipped", ""]
    if not discarded:
        lines.append("None.")
    for item in discarded:
        lines.append(
            f"- {item['paper_id']} page {item['page']} — {item['reason']} — "
            f"`{item['path']}`")
    lines += ["", "## Unsure items", ""]
    if not unsure:
        lines.append("None.")
    for item in unsure:
        lines.append(
            f"- `{item['code']}` — {item.get('paper_id', '')} "
            f"page {item.get('page', '?')} — {item.get('detail', '')} — "
            f"`{item.get('path', '')}`")
    lines += [
        "",
        "## Gate A",
        "",
        "Review `bank/review/index.html`, then record the owner decision.",
        "No answers, templates or seeds were built.",
        "",
    ]
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = build()
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"{SUBJECT}: {report['index']['questions']} questions, "
              f"{report['index']['assets']} assets, "
              f"{report['index']['unsure']} unsure items; "
              f"status={report['status']}")
        print(REPORT_MD)


if __name__ == "__main__":
    main()
