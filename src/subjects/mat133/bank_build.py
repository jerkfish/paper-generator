"""V2 question bank for MAT133, built from the raw MinerU dossiers.

Rules:

* the source is the raw working copy, never a v1 generated question;
* question and part text is kept as MinerU read it; whitespace is normalised
  only for hashes and duplicate detection;
* every part mark is taken from a printed ``(N marks)`` line; a missing mark is
  recorded as ``needs_fix``/``unsure``, never invented;
* every figure is cropped from the source page and linked to its question;
* a question is ``extracted`` or ``needs_fix`` until the owner approves the
  bank at Gate A.

Run:
    uv run python -m src.subjects.mat133.bank_build
    uv run python -m src.subjects.mat133.bank_build --papers MAT133-2008-OCT
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from src import config
from src.bank.duplicates import (cluster_duplicates, duplicate_map,
                                 near_duplicate_pairs)
from src.bank.quality import quality_band, quality_score
from src.bank.review import build_review_sheet
from src.bank.schema import normalize_text, question_content_hash
from src.bank.store import BankStore, save_json
from src.subjects.mat133.papers import SUBJECT

TRACKING = config.TRACKING_DIR / "mat133" / "v2"
BANK = TRACKING / "bank"
REGISTER = TRACKING / "papers_register.json"
STATUS = TRACKING / "extraction_status.json"
OCR_DIR = config.TRACKING_DIR / "mat133" / "paper_text"
V1_LOG = config.TRACKING_DIR / "mat133" / "question_log.json"

PART_RE = re.compile(r"(?mi)^[\s(]*([a-h])\s*\)\s*")
MARKS_RE = re.compile(r"\(\s*(\d{1,3})\s*marks?\s*\)", re.I)
QUESTION_HEAD_RE = re.compile(r"(?mi)^\s*QUESTION\s+(\d{1,3})\s*$")
ROMAN_RE = re.compile(r"(?mi)^[\s(]*(i{1,4}|v|vi{0,3})\s*\)\s*")
APPENDIX_RE = re.compile(r"(?is)\bEND OF QUESTION PAPER\b.*$")
NOISE_LINE_RE = re.compile(
    r"(?i)^\s*(CONFIDENTIAL|©?\s*Hak Cipta.*|CS/.*MAT133.*|"
    r"END OF QUESTION PAPER.*)\s*$")

TOPIC_PATTERNS: dict[str, tuple[str, ...]] = {
    "functions": (
        r"\bfunction\b", r"\bdomain\b", r"\brange\b", r"\bcomposite\b",
        r"\bcomposition\b", r"\binverse\b", r"\bpiecewise\b",
        r"\btransform", r"\beven\b", r"\bodd\b", r"\bf\s*\("),
    "inequalities": (
        r"\binequalit", r"\binterval notation", r"\bnumber line",
        r"\b<=\b", r"\b>=\b", r"[<>]"),
    "absolute_value": (r"\babsolute\b", r"\|\s*[^|]{1,40}\|"),
    "lines": (r"\bline\b", r"\bslope\b", r"\bperpendicular\b",
              r"\bparallel\b", r"\bintercept\b"),
    "circles": (r"\bcircle\b", r"\bcenter\b", r"\bcentre\b",
                r"\bradius\b", r"\btangent\b"),
    "parabolas": (r"\bparabola\b", r"\bvertex\b", r"\bdirectrix\b",
                  r"\bfocus\b"),
    "complex_numbers": (
        r"\bcomplex\b", r"\bimaginary\b", r"\bmodulus\b", r"\bargument\b",
        r"\ba\s*\+\s*bi\b", r"\bi\^"),
    "systems_of_equations": (
        r"\bsystems?\s+of\s+equations?\b", r"\bsimultaneous",
        r"\bsolve\s+the\s+system\b"),
    "systems_of_inequalities": (
        r"\bsystem\s+of\s+inequalities\b", r"\bfeasible\s+region\b",
        r"\bshaded\s+region\b"),
    "polynomials": (
        r"\bpolynomial\b", r"\bfactor\b", r"\bremainder\b",
        r"\bsynthetic\s+division\b", r"\blong\s+division\b"),
    "exponential_logarithmic": (
        r"\blog\b", r"\bln\b", r"\bexponential\b", r"\be\s*\^",
        r"\bexponent"),
    "trigonometry": (
        r"\bsin\b", r"\bcos\b", r"\btan\b", r"\bsec\b", r"\bcsc\b",
        r"\bcot\b", r"\btrigonometric\b", r"\bidentity\b", r"\bangle\b"),
    "circular_measure": (
        r"\barc\b", r"\bsector\b", r"\bradian", r"\btheta\b",
        r"\bcircular\b"),
    "triangle_geometry": (
        r"\btriangle\b", r"\bsine\s+rule\b", r"\bcosine\s+rule\b",
        r"\barea\s+of\s+the\s+triangle\b"),
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _topic_tags(text: str) -> list[str]:
    lowered = text.lower()
    scores: dict[str, int] = {}
    for topic, patterns in TOPIC_PATTERNS.items():
        score = sum(len(re.findall(pattern, lowered)) for pattern in patterns)
        if score:
            scores[topic] = score
    if not scores:
        return ["other"]
    ordered = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    top_score = ordered[0][1]
    return [topic for topic, score in ordered if score == top_score]


def _question_topics(text: str, parts: list[dict]) -> list[str]:
    tags = _topic_tags(text)
    if tags != ["other"]:
        return tags
    v1_topics = [str(part.get("v1_topic") or "") for part in parts
                 if part.get("v1_topic")]
    if not v1_topics:
        return tags
    return [Counter(v1_topics).most_common(1)[0][0]]


def _clean_question_text(text: str) -> str:
    text = QUESTION_HEAD_RE.sub("", text, count=1)
    text = APPENDIX_RE.split(text)[0]
    lines = [line for line in text.splitlines()
             if not NOISE_LINE_RE.match(line)]
    return "\n".join(lines).strip()


def _part_segments(text: str) -> list[dict]:
    matches = list(PART_RE.finditer(text))
    if not matches:
        return [{"label": "", "text": text.strip(), "start": 0}]
    parts = []
    preamble = text[:matches[0].start()].strip()
    if preamble:
        parts.append({"label": "", "text": preamble, "start": 0})
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        parts.append({
            "label": match.group(1).lower(),
            "text": text[match.end():end].strip(),
            "start": match.start(),
        })
    return parts


def _marks_in(text: str) -> list[int]:
    return [int(value) for value in MARKS_RE.findall(text)]


def _v1_log_entries(paper_file: str, question_no: int) -> dict[str, dict]:
    """Return the approved v1 question-log entries for one paper question.

    The v1 log is the playbook compatibility source for taxonomy and question
    metadata.  It is used only to cross-check or recover a mark/topic when the
    raw MinerU text does not expose it; the bank text itself stays MinerU.
    """
    payload = _load(V1_LOG, {})
    stem = Path(paper_file).stem
    rows: dict[str, dict] = {}
    for entry in payload.get("entries") or []:
        if str(entry.get("paper_stem") or Path(
                str(entry.get("paper") or "")).stem) != stem:
            continue
        if str(entry.get("question")) != str(question_no):
            continue
        label = str(entry.get("part") or "").lower()
        if label:
            rows[label] = entry
    return rows


def _ocr_part_marks(paper_file: str, question_no: int) -> dict[str, int]:
    """Read printed part marks from the legacy OCR page text as a fallback.

    This is the same paper's OCR, not a v1 generated question.  Only a part
    with exactly one printed mark is accepted; ambiguous mark blocks are left
    for Gate A.
    """
    path = OCR_DIR / f"{Path(paper_file).stem}.txt"
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    heading = re.compile(
        rf"(?mi)^\s*QUESTION\s+{int(question_no)}\s*$")
    match = heading.search(text)
    if not match:
        return {}
    following = re.search(r"(?mi)^\s*QUESTION\s+\d{1,3}\s*$",
                          text[match.end():])
    section = text[match.end():match.end() + following.start()
                   if following else len(text)]
    labels = list(re.finditer(r"(?mi)^\s*([a-h])\s*\)", section))
    marks: dict[str, int] = {}
    for index, label in enumerate(labels):
        end = labels[index + 1].start() if index + 1 < len(labels) else len(section)
        part = section[label.end():end]
        values = _marks_in(part)
        if len(values) == 1:
            marks[label.group(1).lower()] = values[0]
    return marks


def _part_marks(text: str) -> tuple[int | None, str]:
    values = _marks_in(text)
    if not values:
        return None, "no printed (N marks) line in this part"
    nested = len(ROMAN_RE.findall(text))
    if len(values) == 1:
        return values[0], ""
    if nested and len(values) <= nested:
        return sum(values), "sum of the nested marks"
    if values[-1] == sum(values[:-1]):
        return values[-1], "last mark equals the sum of the nested marks"
    return sum(values), "sum of multiple printed marks"


def _merged_part_warning(text: str) -> str:
    values = list(MARKS_RE.finditer(text))
    nested = list(ROMAN_RE.finditer(text))
    if len(values) < 2:
        return ""
    if not nested:
        return "multiple printed marks without nested labels; possible merged parts"
    if values[0].start() < nested[0].start():
        return "first mark appears before a nested group; possible merged part"
    return ""


def _build_parts(text: str) -> tuple[list[dict], list[str]]:
    reasons = []
    parts = []
    for segment in _part_segments(text):
        marks, note = _part_marks(segment["text"])
        label = segment["label"]
        if not label and segment["text"]:
            reasons.append("unnumbered preamble text before the first part")
        if marks is None:
            reasons.append(
                f"part {label or '?'} has no printed marks: {note}")
        warning = _merged_part_warning(segment["text"])
        if warning:
            reasons.append(f"part {label or '?'}: {warning}")
        parts.append({
            "label": label,
            "text": segment["text"],
            "marks": marks,
            "marks_mineru": marks,
            "marks_note": note,
            "merged_warning": warning,
            "nested_labels": [m.group(1).lower()
                              for m in ROMAN_RE.finditer(segment["text"])],
        })
    return parts, reasons


def _asset_question_index(asset: dict, questions: list[dict]) -> int | None:
    index = asset.get("question_index")
    if isinstance(index, int) and 0 <= index < len(questions):
        return index
    label = str(asset.get("label") or "")
    if label:
        for position, question in enumerate(questions):
            if label in (question.get("refs") or []):
                return position
    return None


def _save_asset_image(source: Path, target: Path) -> bool:
    try:
        with Image.open(source) as image:
            image = image.convert("RGB")
            target.parent.mkdir(parents=True, exist_ok=True)
            image.save(target, format="PNG")
        return True
    except Exception:
        return False


def _crop_page_bbox(pdf_path: Path, page_idx: int, bbox: list[float],
                    target: Path) -> bool:
    """Crop the original page at the MinerU block bbox (300 dpi fallback)."""
    if not pdf_path.is_file():
        return False
    try:
        import pymupdf
        with pymupdf.open(str(pdf_path)) as pdf:
            if not 0 <= int(page_idx) < len(pdf):
                return False
            page = pdf[int(page_idx)]
            width, height = page.rect.width, page.rect.height
            x0, y0, x1, y1 = [float(value) for value in bbox]
            if max(x0, y0, x1, y1) <= 1000:
                x0, y0 = x0 / 1000 * width, y0 / 1000 * height
                x1, y1 = x1 / 1000 * width, y1 / 1000 * height
            clip = pymupdf.Rect(
                max(0, x0), max(0, y0),
                min(width, x1), min(height, y1))
            if clip.is_empty:
                clip = page.rect
            pix = page.get_pixmap(dpi=300, clip=clip, alpha=False)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(pix.tobytes("png"))
        return True
    except Exception:
        return False


def _paper_questions(paper: dict, dossier: dict, bank: BankStore) -> tuple[list[dict], list[dict], list[dict]]:
    questions = []
    assets = []
    unsure = []
    source_pdf = config.PAPERS_ROOT / SUBJECT / str(paper.get("file") or "")
    normalized_questions = dossier.get("questions") or []
    assigned_source_assets: set[str] = set()
    for index, source in enumerate(normalized_questions):
        qid = source["question_id"]
        text = _clean_question_text(str(source.get("text") or ""))
        parts, part_reasons = _build_parts(text)
        question_no = int(source.get("number") or 0)
        suffix = str(source.get("question_id") or "").split(
            f"-Q{question_no}", 1)[-1]
        repeated_question = bool(suffix)
        ocr_marks = ({} if repeated_question else _ocr_part_marks(
            str(paper.get("file") or ""), question_no))
        v1_entries = ({} if repeated_question else _v1_log_entries(
            str(paper.get("file") or ""), question_no))
        recovered = []
        for part in parts:
            label = str(part.get("label") or "")
            v1_entry = v1_entries.get(label) or {}
            v1_marks = v1_entry.get("marks")
            part["v1_topic"] = v1_entry.get("topic", "")
            part["marks_v1"] = int(v1_marks) if v1_marks is not None else ""
            part["marks_ocr"] = ocr_marks.get(label, "")
            if part.get("marks") is not None:
                part["marks_source"] = "mineru"
                if label in ocr_marks and int(ocr_marks[label]) != int(
                        part["marks"]):
                    part["marks_conflict"] = ocr_marks[label]
                    part_reasons.append(
                        f"part {label}: MinerU marks {part['marks']} vs "
                        f"legacy OCR {ocr_marks[label]}")
                if v1_marks is not None and int(v1_marks) != int(
                        part["marks"]):
                    part["marks_conflict_v1"] = v1_marks
                    part_reasons.append(
                        f"part {label}: MinerU marks {part['marks']} vs "
                        f"v1 question log {int(v1_marks)}")
                continue
            if v1_marks is not None:
                part["marks"] = int(v1_marks)
                part["marks_source"] = "v1_question_log"
                part["marks_note"] = (
                    "recovered from the approved v1 question log; "
                    f"confidence={v1_entry.get('confidence', 'unknown')}")
                recovered.append({
                    "part": label,
                    "marks": int(v1_marks),
                    "source": "v1_question_log",
                    "evidence": v1_entry.get("evidence", "")[:400],
                })
                if label in ocr_marks and int(ocr_marks[label]) != int(
                        v1_marks):
                    part_reasons.append(
                        f"part {label}: v1 question log marks "
                        f"{int(v1_marks)} vs legacy OCR {ocr_marks[label]}")
                continue
            if label in ocr_marks:
                part["marks"] = int(ocr_marks[label])
                part["marks_source"] = "legacy_ocr"
                part["marks_note"] = (
                    "recovered from the same paper's OCR page text")
                recovered.append({
                    "part": label,
                    "marks": int(ocr_marks[label]),
                    "source": "legacy_ocr",
                })
        if recovered:
            part_reasons = [
                reason for reason in part_reasons
                if not any(
                    reason.startswith(f"part {item['part']} has no printed ")
                    for item in recovered)
            ]
        known_parts = [part for part in parts if part.get("marks") is not None]
        marks = sum(int(part["marks"]) for part in known_parts)
        complete = len(known_parts) == len(parts) and all(
            part.get("label") for part in parts)
        refs = sorted(set(source.get("refs") or []),
                      key=lambda value: (
                          value.split()[0], int(value.split()[1])))
        linked_assets = []
        for asset in dossier.get("assets") or []:
            if _asset_question_index(asset, normalized_questions) != index:
                continue
            assigned_source_assets.add(str(asset.get("asset_id") or ""))
            label = str(asset.get("label") or "")
            kind = ("table" if str(asset.get("kind")) == "table"
                    else "figure" if label.lower().startswith("figure")
                    else "picture")
            sequence = len(linked_assets) + 1
            aid = f"A-{qid}-{('T' if kind == 'table' else 'F')}{sequence}"
            image = Path(str(asset.get("img_path") or ""))
            target = bank.assets_dir / f"{aid}.png"
            copied = bool(image.is_file()) and _save_asset_image(image, target)
            treatment = "original_crop"
            if not copied:
                copied = _crop_page_bbox(
                    source_pdf, int(asset.get("page_idx", 0)),
                    asset.get("bbox") or [], target)
                treatment = "page_crop_bbox"
            record = {
                "id": aid,
                "question_id": qid,
                "kind": kind,
                "path": str(target) if copied else "",
                "source_paper": paper["paper_id"],
                "source_file": paper["file"],
                "source_page": int(asset.get("page_idx", 0)) + 1,
                "bbox": asset.get("bbox") or [],
                "dpi": 300 if treatment == "page_crop_bbox" else None,
                "sha256": _sha256(target) if copied else "",
                "caption": str(asset.get("caption") or label or aid),
                "label": label,
                "treatment": treatment,
                "verdict": "pending",
                "provenance": asset.get("provenance") or {},
                "table_html": str(asset.get("table_html") or ""),
            }
            if not copied:
                record["verdict"] = "pending"
                record["issue"] = "MinerU image file missing"
                unsure.append({
                    "question_id": qid,
                    "item": f"asset {aid} has no readable image crop",
                    "blocking": True,
                    "opened": _now()[:10],
                })
            bank.save_asset(record)
            assets.append(record)
            linked_assets.append(aid)
        for fallback in dossier.get("fallback") or []:
            if fallback.get("question_id") != source.get("question_id"):
                continue
            sequence = len(linked_assets) + 1
            aid = f"A-{qid}-C{sequence}"
            image = Path(str(fallback.get("path") or ""))
            target = bank.assets_dir / f"{aid}.png"
            copied = bool(image.is_file()) and _save_asset_image(image, target)
            label = str(fallback.get("label") or "")
            record = {
                "id": aid,
                "question_id": qid,
                "kind": "page_crop",
                "path": str(target) if copied else "",
                "source_paper": paper["paper_id"],
                "source_file": paper["file"],
                "source_page": int(fallback.get("page_idx", 0)) + 1,
                "bbox": [],
                "dpi": 300,
                "sha256": _sha256(target) if copied else "",
                "caption": label or aid,
                "label": label,
                "treatment": "page_crop_fallback",
                "verdict": "pending",
                "reason": fallback.get("reason", ""),
            }
            bank.save_asset(record)
            assets.append(record)
            linked_assets.append(aid)
        assets_by_label = {str(asset.get("label") or "").lower(): asset["id"]
                           for asset in assets
                           if asset.get("question_id") == qid}
        unresolved = [ref for ref in refs
                      if ref.lower() not in assets_by_label]
        reasons = list(part_reasons)
        if repeated_question and any(
                part.get("marks") is None for part in parts):
            reasons.append(
                "repeated question number in the same PDF; v1-log and OCR "
                "mark fallbacks are scoped to the first question set")
        if not text or len(text) < 40:
            reasons.append("question text is too short")
        if marks <= 0:
            reasons.append("no printed marks could be read")
        if unresolved:
            reasons.append("unresolved references: " + ", ".join(unresolved))
        if any(not asset.get("path") for asset in assets
               if asset.get("question_id") == qid):
            reasons.append("one or more image crops are missing")
        status = "needs_fix" if reasons else "extracted"
        if status == "needs_fix":
            for reason in reasons:
                unsure.append({
                    "question_id": qid,
                    "item": reason,
                    "blocking": True,
                    "opened": _now()[:10],
                })
        blocks = [{
            "text": text,
            "normalised": normalize_text(text),
            "page": int(source.get("page_idx", 0)) + 1,
            "bbox": source.get("bbox") or [],
        }]
        question = {
            "id": qid,
            "source_paper": paper["paper_id"],
            "source_file": paper["file"],
            "pages": sorted({int(source.get("page_idx", 0)) + 1,
                             *[asset["source_page"] for asset in assets
                               if asset.get("question_id") == qid]}),
            "part": f"Q{source.get('number')}",
            "question_no": int(source.get("number") or index + 1),
            "slot_hint": f"Q{source.get('number')}",
            "marks": marks,
            "subpart_marks": [
                {"label": part["label"], "marks": int(part["marks"]),
                 "source": part.get("marks_source", "")}
                for part in parts if part.get("marks") is not None],
            "marks_complete": complete,
            "marks_recovered": recovered,
            "native_text": text,
            "native_text_blocks": blocks,
            "parts": parts,
            "native_tables": [],
            "assets": linked_assets,
            "refs": refs,
            "unresolved_refs": unresolved,
            "topic_tags": _question_topics(text, parts),
            "v1_topics": sorted({str(part.get("v1_topic"))
                                 for part in parts if part.get("v1_topic")}),
            "duplicate_cluster": "",
            "status": status,
            "quality_score": 0.0,
            "content_hash": "",
            "parse_notes": reasons,
            "source": {
                "parser": "mineru",
                "model": dossier.get("model", ""),
                "paper_id": paper["paper_id"],
                "question_id": source["question_id"],
                "dossier": paper.get("_dossier", ""),
            },
        }
        question["content_hash"] = question_content_hash(question)
        questions.append(question)
    for asset in dossier.get("assets") or []:
        source_id = str(asset.get("asset_id") or "")
        if source_id in assigned_source_assets:
            continue
        target = (bank.root / "unassigned" /
                  f"{paper['paper_id']}-{source_id}.png")
        copied = _save_asset_image(
            Path(str(asset.get("img_path") or "")), target)
        if not copied:
            copied = _crop_page_bbox(
                source_pdf, int(asset.get("page_idx", 0)),
                asset.get("bbox") or [], target)
        unsure.append({
            "paper_id": paper["paper_id"],
            "asset_id": source_id,
            "path": str(target) if copied else "",
            "item": (f"unassigned MinerU {asset.get('kind', 'asset')} "
                     f"{source_id} on page "
                     f"{int(asset.get('page_idx', 0)) + 1}; review before "
                     "Gate A"),
            "blocking": True,
            "opened": _now()[:10],
        })
    return questions, assets, unsure


def build(papers: list[str] | None = None, *, model: str = "vlm") -> dict:
    register = _load(REGISTER, {})
    if not register:
        raise SystemExit(
            f"{REGISTER} is missing; run src.subjects.mat133.papers first")
    status = _load(STATUS, {})
    wanted = {code.upper() for code in papers or []}
    bank = BankStore(BANK).ensure()
    all_questions: list[dict] = []
    all_assets: list[dict] = []
    all_unsure: list[dict] = []
    papers_done = []
    models: set[str] = set()
    for paper in register.get("unique_papers") or []:
        if wanted and paper["paper_id"].upper() not in wanted:
            continue
        entry = (status.get("papers") or {}).get(paper["paper_id"]) or {}
        if entry.get("status") != "done":
            continue
        cache = Path(entry.get("cache_dir") or "")
        normalized = cache / "review" / "normalized.json"
        if not normalized.is_file():
            all_unsure.append({
                "paper_id": paper["paper_id"],
                "item": "normalized.json is missing",
                "blocking": True,
                "opened": _now()[:10],
            })
            continue
        dossier = json.loads(normalized.read_text(encoding="utf-8"))
        models.add(str(entry.get("model") or dossier.get("model") or ""))
        paper = dict(paper)
        paper["_dossier"] = str(normalized)
        questions, assets, unsure = _paper_questions(paper, dossier, bank)
        all_questions.extend(questions)
        all_assets.extend(assets)
        all_unsure.extend(unsure)
        papers_done.append(paper["paper_id"])
    duplicate_clusters = cluster_duplicates(all_questions)
    duplicate_lookup = duplicate_map(all_questions)
    for question in all_questions:
        question["duplicate_cluster"] = duplicate_lookup.get(
            question["id"], question["id"])
        assets = {asset["id"]: asset for asset in all_assets
                  if asset.get("question_id") == question["id"]}
        question["quality_score"] = quality_score(question, assets)
        question["quality_band"] = quality_band(question["quality_score"])
        bank.save_question(question)
    near_pairs = near_duplicate_pairs(all_questions)
    expected_papers = [paper["paper_id"]
                       for paper in register.get("unique_papers") or []]
    missing_papers = [paper_id for paper_id in expected_papers
                      if paper_id not in papers_done]
    counts = {
        "papers": len(papers_done),
        "papers_expected": len(expected_papers),
        "papers_missing": len(missing_papers),
        "questions": len(all_questions),
        "extracted": sum(1 for q in all_questions
                         if q["status"] == "extracted"),
        "needs_fix": sum(1 for q in all_questions
                         if q["status"] == "needs_fix"),
        "rejected": 0,
        "assets": len(all_assets),
        "fallback_assets": sum(1 for a in all_assets
                               if a["treatment"] == "page_crop_fallback"),
        "references": sum(len(q.get("refs") or []) for q in all_questions),
        "unresolved_references": sum(
            len(q.get("unresolved_refs") or []) for q in all_questions),
        "duplicate_clusters": sum(1 for cluster in duplicate_clusters
                                  if cluster["count"] > 1),
        "near_duplicate_pairs": len(near_pairs),
        "unsure": len(all_unsure),
        "marks_total": sum(int(q.get("marks") or 0) for q in all_questions),
    }
    topic_counts: dict[str, int] = {}
    for question in all_questions:
        for topic in question.get("topic_tags") or ["other"]:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
    index = {
        "schema_version": 2,
        "subject": SUBJECT,
        "generated_on": _now(),
        "model": model,
        "counts": counts,
        "topics": dict(sorted(topic_counts.items())),
        "papers": papers_done,
        "missing_papers": missing_papers,
        "questions": [{
            "id": q["id"],
            "source_paper": q["source_paper"],
            "marks": q["marks"],
            "status": q["status"],
            "topic_tags": q["topic_tags"],
            "quality_score": q["quality_score"],
            "quality_band": q["quality_band"],
            "refs": q["refs"],
            "assets": q["assets"],
        } for q in all_questions],
    }
    save_json(BANK / "index.json", index)
    save_json(BANK / "unsure.json", {
        "subject": SUBJECT, "generated_on": _now(), "items": all_unsure})
    save_json(BANK / "duplicates.json", {
        "exact": duplicate_clusters, "near": near_pairs})
    save_json(BANK / "corrections.json", {})
    save_json(BANK / "approvals.json", {
        "subject": SUBJECT,
        "gate_a": {"status": "pending", "by": "", "on": "", "evidence": []},
    })
    save_json(BANK / "answers.json", {"by_qid": {}})
    extra_assets = []
    for item in all_unsure:
        if not item.get("asset_id") or not item.get("path"):
            continue
        path = Path(str(item["path"]))
        if not path.is_file():
            continue
        extra_assets.append({
            "id": item["asset_id"],
            "label": item.get("paper_id", ""),
            "kind": "picture",
            "page": "",
            "treatment": "unassigned",
            "review_path": f"../unassigned/{path.name}",
        })
    review = build_review_sheet(
        bank, bank.review_dir, subject=SUBJECT,
        title="MAT133 v2 question bank", extra_assets=extra_assets)
    _write_paper_index(index, bank.review_dir)
    _write_marks_csv(all_questions, bank.review_dir)
    report = _gate_report(index, all_questions, all_assets, all_unsure,
                          review)
    save_json(BANK / "gate1_report.json", report)
    (BANK / "gate1_report.md").write_text(
        _gate_report_md(report, all_questions), encoding="utf-8")
    return {"counts": counts, "review": str(review),
            "report": str(BANK / "gate1_report.md")}


def _write_marks_csv(questions: list[dict], review_dir: Path) -> Path:
    path = review_dir / "marks.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "paper", "question_id", "part", "mineru_marks", "v1_marks",
            "ocr_marks", "used_marks", "used_source", "question_status",
            "note"])
        for question in questions:
            for part in question.get("parts") or []:
                writer.writerow([
                    question["source_paper"],
                    question["id"],
                    part.get("label", ""),
                    part.get("marks_mineru", ""),
                    part.get("marks_v1", ""),
                    part.get("marks_ocr", ""),
                    part.get("marks", ""),
                    part.get("marks_source", ""),
                    question["status"],
                    part.get("marks_note", "")
                    or part.get("merged_warning", ""),
                ])
    return path


def _write_paper_index(index: dict, review_dir: Path) -> Path:
    groups: dict[str, list[dict]] = {}
    for question in index.get("questions") or []:
        groups.setdefault(question["source_paper"], []).append(question)
    rows = []
    for paper, questions in sorted(groups.items()):
        links = ", ".join(
            f"<a href='index.html#{question['id']}'>{question['id']}</a>"
            for question in questions)
        marks = sum(int(question.get("marks") or 0) for question in questions)
        needs_fix = sum(1 for question in questions
                        if question.get("status") == "needs_fix")
        rows.append(
            f"<tr><td>{paper}</td><td>{len(questions)}</td>"
            f"<td>{marks}</td><td>{needs_fix}</td><td>{links}</td></tr>")
    page = """<!doctype html>
<html><head><meta charset="utf-8">
<title>MAT133 v2 bank — by paper</title>
<style>
body { font-family: Arial, sans-serif; margin: 2rem; }
table { border-collapse: collapse; }
td, th { border: 1px solid #aaa; padding: .3rem .5rem; }
</style></head><body>
<h1>MAT133 v2 bank — by paper</h1>
<p><a href="index.html">Open the full review sheet</a></p>
<table><tr><th>Paper</th><th>Questions</th><th>Marks</th>
<th>Needs fix</th><th>Questions</th></tr>
""" + "\n".join(rows) + """
</table></body></html>
"""
    path = review_dir / "index_by_paper.html"
    path.write_text(page, encoding="utf-8")
    return path


def _gate_report(index: dict, questions: list[dict], assets: list[dict],
                 unsure: list[dict], review: Path) -> dict:
    by_paper: dict[str, dict] = {}
    for question in questions:
        row = by_paper.setdefault(question["source_paper"], {
            "paper": question["source_paper"], "questions": 0,
            "marks": 0, "needs_fix": 0})
        row["questions"] += 1
        row["marks"] += int(question.get("marks") or 0)
        row["needs_fix"] += int(question["status"] == "needs_fix")
    return {
        "schema_version": 2,
        "subject": SUBJECT,
        "generated_on": _now(),
        "gate": "A",
        "status": "pending",
        "counts": index["counts"],
        "topics": index["topics"],
        "papers": sorted(by_paper.values(), key=lambda row: row["paper"]),
        "missing_papers": index.get("missing_papers") or [],
        "needs_fix": [{
            "id": question["id"],
            "source_paper": question["source_paper"],
            "marks": question["marks"],
            "reasons": question.get("parse_notes") or [],
        } for question in questions if question["status"] == "needs_fix"],
        "unsure": unsure,
        "review_sheet": str(review),
        "marks_csv": str(BANK / "review" / "marks.csv"),
        "assets_dir": str(BANK / "assets"),
        "questions_dir": str(BANK / "questions"),
        "owner_approval": {
            "required": True,
            "approved": False,
            "by": "",
            "on": "",
            "note": "",
        },
    }


def _gate_report_md(report: dict, questions: list[dict]) -> str:
    counts = report["counts"]
    lines = [
        "# MAT133 v2 — Gate A bank review",
        "",
        f"Generated: {report['generated_on']}",
        "Status: **pending owner approval**",
        "",
        "## Counts",
        "",
        f"- Papers processed: {counts['papers']} of "
        f"{counts['papers_expected']} "
        f"({counts['papers_missing']} missing a V1 dossier)",
        f"- Questions: {counts['questions']} "
        f"({counts['extracted']} extracted, {counts['needs_fix']} needs fix)",
        f"- Marks captured: {counts['marks_total']}",
        f"- Assets: {counts['assets']} "
        f"({counts['fallback_assets']} page-crop fallbacks)",
        f"- References: {counts['references']} "
        f"({counts['unresolved_references']} unresolved)",
        f"- Exact duplicate clusters: {counts['duplicate_clusters']}",
        f"- Near-duplicate pairs (review aid): {counts['near_duplicate_pairs']}",
        f"- Open unsure items: {counts['unsure']}",
        "",
        "## Papers",
        "",
        "| Paper | Questions | Marks | Needs fix |",
        "|---|---:|---:|---:|",
    ]
    for row in report["papers"]:
        lines.append(
            f"| {row['paper']} | {row['questions']} | {row['marks']} | "
            f"{row['needs_fix']} |")
    lines += ["", "## Missing papers", ""]
    if report.get("missing_papers"):
        for paper_id in report["missing_papers"]:
            lines.append(f"- `{paper_id}` has no V1 dossier")
    else:
        lines.append("None: every unique paper has a dossier.")
    lines += ["", "## Needs fix", ""]
    if not report["needs_fix"]:
        lines.append("None.")
    for row in report["needs_fix"]:
        lines.append(f"- `{row['id']}` ({row['marks']} marks): "
                     + "; ".join(row["reasons"]))
    unassigned = [item for item in report.get("unsure") or []
                  if item.get("asset_id")]
    lines += ["", "## Unassigned assets", ""]
    if not unassigned:
        lines.append("None.")
    for item in unassigned:
        lines.append(
            f"- `{item.get('paper_id')}` / `{item.get('asset_id')}`: "
            f"{item.get('item')} (`{item.get('path', '')}`)")
    lines += [
        "",
        "## Review",
        "",
        f"- Sheet: `{report['review_sheet']}`",
        f"- Marks table: `{report.get('marks_csv', '')}`",
        f"- Questions: `{report['questions_dir']}`",
        f"- Assets: `{report['assets_dir']}`",
        "",
        "Gate A is not approved. Review the sheet, correct marks/assets and "
        "record the owner approval in `bank/approvals.json`.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--papers", nargs="*", default=None)
    parser.add_argument("--model", default="vlm")
    args = parser.parse_args()
    result = build(args.papers, model=args.model)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
