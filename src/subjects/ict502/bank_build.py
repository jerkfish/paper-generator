"""V2 question bank for ICT502, built from the MinerU dossiers.

The normalised MinerU question text drops a few parts that cross a page or
table boundary (for example ICT502-2024-JUL-Q2 b).  This builder therefore
reads the paper-level ``full.md`` as its primary text source, splits it on the
printed QUESTION headings and on a repeated ``a)`` after ``b)`` (a heading lost
by MinerU), and keeps the normalised dossier for refs, pages and assets.

Rules:

* the source is the raw working copy, never an invented question;
* question and part text is kept as MinerU read it; whitespace is normalised
  only for hashes and duplicate detection;
* a part mark is the sum of the printed ``(N marks)`` lines inside that part;
  missing marks are recovered from the same paper's OCR text or a page-render
  override, never invented;
* every figure/table is cropped from the source page and linked to its
  question; unassigned crops are reported for Gate A;
* a question is ``extracted`` or ``needs_fix`` until the owner approves the
  bank at Gate A.

Run:
    uv run python -m src.subjects.ict502.bank_build
    uv run python -m src.subjects.ict502.bank_build --papers ICT502-2026-FEB
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

from PIL import Image

from src import config
from src.bank.duplicates import (cluster_duplicates, duplicate_map,
                                 near_duplicate_pairs)
from src.bank.quality import quality_band, quality_score
from src.bank.review import build_review_sheet
from src.bank.schema import normalize_text, question_content_hash
from src.bank.store import BankStore, save_json

SUBJECT = "ICT502"

TRACKING = config.TRACKING_DIR / "ict502"
BANK = TRACKING / "bank"
REGISTER = TRACKING / "papers_register.json"
STATUS = TRACKING / "extraction_status.json"
OVERRIDES = TRACKING / "marks_overrides.json"
EXCLUSIONS = TRACKING / "asset_exclusions.json"
TEXT_CORRECTIONS = TRACKING / "text_corrections.json"
ASSET_OVERRIDES = TRACKING / "asset_overrides.json"
OCR_DIR = TRACKING / "paper_text"

QUESTION_HEAD_RE = re.compile(r"(?mi)^#{0,4}\s*QUESTION\s+(\d{1,3})\s*$")
LABEL_RE = re.compile(r"(?mi)^\s*#{0,4}\s*([a-h])\s*\)\s*")
PART_RE = re.compile(r"(?mi)^[\s(]*([a-h])\s*\)\s*")
MARKS_RE = re.compile(r"\(\s*(\d+(?:\.\d+)?)\s*marks?\s*\)", re.I)
OCR_MARKS_RE = re.compile(r"\(\s*(\d+(?:\.\d+)?)\s*ma[a-z*]*\s*\)", re.I)
ROMAN_RE = re.compile(r"(?mi)^[\s(]*(i{1,4}|v|vi{0,3})\s*\)\s*")
APPENDIX_RE = re.compile(r"(?is)\bEND OF QUESTION PAPER\b.*$")
NOISE_LINE_RE = re.compile(
    r"(?i)^\s*(CONFIDENTIAL|©?\s*Hak Cipta.*|CD/.*ICT502.*|"
    r"CS/.*ICT502.*|END OF QUESTION PAPER.*)\s*$")
MONTH_CODE = {
    "JANUARY": "JAN", "FEBRUARY": "FEB", "MARCH": "MAR", "APRIL": "APR",
    "MAY": "MAY", "JUNE": "JUN", "JULY": "JUL", "AUGUST": "AUG",
    "SEPTEMBER": "SEP", "OCTOBER": "OCT", "NOVEMBER": "NOV",
    "DECEMBER": "DEC",
}

TOPIC_PATTERNS: dict[str, tuple[str, ...]] = {
    "file_system": (
        r"\bfile[- ]based\b", r"\bfile system\b", r"\bdata redundancy\b",
        r"\bdata inconsistency\b", r"\bprogram[- ]data dependence\b",
        r"\bapplication program\b"),
    "database_concepts": (
        r"\bdatabase approach\b", r"\bdbms\b", r"\bdata independence\b",
        r"\bansi[- ]sparc\b", r"\bthree[- ]level architecture\b",
        r"\bschema\b", r"\binstance\b", r"\bdata model\b",
        r"\bdatabase administrator\b", r"\bdba\b"),
    "data_warehouse": (
        r"\bdata warehouse\b", r"\bdata mart\b", r"\bdata mining\b",
        r"\bolap\b", r"\brolap\b", r"\bmolap\b", r"\bholap\b",
        r"\bdata cube\b", r"\bdice\b", r"\bslice\b", r"\bfact table\b",
        r"\bdimension table\b", r"\betl\b", r"\bstar schema\b",
        r"\bsnowflake\b"),
    "relational_model": (
        r"\brelational model\b", r"\brelation\b", r"\btuple\b",
        r"\battribute\b", r"\bdomain\b", r"\bprimary key\b",
        r"\bforeign key\b", r"\bcandidate key\b", r"\bintegrity\b",
        r"\brelational algebra\b", r"\brelational schema\b"),
    "erd": (
        r"\bentity[- ]relationship\b", r"\berd\b", r"\bcardinality\b",
        r"\bmodality\b", r"\bweak entity\b", r"\bspeciali[sz]ation\b",
        r"\bgenerali[sz]ation\b", r"\baggregation\b"),
    "normalization": (
        r"\bnormalization\b", r"\bnormalisation\b", r"\b1nf\b", r"\b2nf\b",
        r"\b3nf\b", r"\bbcnf\b", r"\bfunctional dependency\b",
        r"\banomaly\b", r"\bdecomposition\b"),
    "sql": (
        r"\bsql\b", r"\bselect\b", r"\bjoin\b", r"\bddl\b", r"\bdml\b",
        r"\bview\b", r"\btrigger\b", r"\bstored procedure\b",
        r"\bconstraint\b"),
    "query_processing": (
        r"\bquery processing\b", r"\bquery decomposition\b",
        r"\bheuristic\b", r"\bsemantic analysis\b", r"\bquery tree\b",
        r"\bcost[- ]based\b", r"\boptimization\b", r"\bconjunctive normal form\b",
        r"\bcnf\b"),
    "distributed_db": (
        r"\bdistributed database\b", r"\bddbms\b", r"\bfragmentation\b",
        r"\bhorizontal\b", r"\bvertical\b", r"\bmixed fragmentation\b",
        r"\ballocation\b", r"\breplication\b", r"\btransparency\b",
        r"\bcorrectness rules?\b"),
    "transaction": (
        r"\btransaction\b", r"\bacid\b", r"\bcommit\b", r"\brollback\b",
        r"\bschedule\b", r"\bserializab", r"\bprecedence graph\b",
        r"\bconflict\b", r"\bnon[- ]serial\b"),
    "concurrency_control": (
        r"\blocking\b", r"\b2pl\b", r"\btwo[- ]phase locking\b",
        r"\bdeadlock\b", r"\bwait[- ]die\b", r"\bwound[- ]wait\b",
        r"\btimestamp\b", r"\bread lock\b", r"\bwrite lock\b"),
    "recovery": (
        r"\brecovery\b", r"\bcheckpoint\b", r"\bimmediate update\b",
        r"\bdeferred update\b", r"\blog\b", r"\bbuffer\b", r"\bfailure\b",
        r"\bcrash\b", r"\brestore\b"),
    "database_development": (
        r"\bdatabase development life cycle\b", r"\bddlc\b", r"\bsdlc\b",
        r"\bsystem definition\b", r"\brequirement", r"\bfeasibility\b",
        r"\bimplementation\b", r"\bmaintenance\b"),
    "object_oriented": (
        r"\bobject[- ]oriented\b", r"\boodbms\b", r"\bordbms\b",
        r"\buml\b", r"\bobject[- ]relational\b"),
    "big_data_nosql": (
        r"\bnosql\b", r"\bbig data\b", r"\bhadoop\b", r"\bxml\b",
        r"\bsemi[- ]structured\b", r"\bdistributed file\b"),
    "security": (
        r"\bauthori[sz]ation\b", r"\bauthentication\b", r"\bprivilege\b",
        r"\bsecurity\b", r"\bbackup\b", r"\brestore\b"),
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


def _fix_mark_spacing(text: str) -> str:
    def half(match: re.Match) -> str:
        return str(int(match.group(1)) + 0.5)
    needle = chr(92) + "frac{1}{2}"
    text = re.sub(r"(\d+)\s*" + re.escape(needle), half, text)
    text = re.sub(r"\(\s*(\d+(?:\.\d+)?)\s*mark\s*s\s*\)",
                  r"(\g<1> marks)", text, flags=re.I)
    text = re.sub(r"\(\s*(\d+(?:\.\d+)?)\s*marks?\s*\)",
                  r"(\g<1> marks)", text, flags=re.I)
    return text


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
    return [topic for topic, _score in ordered[:3]]


def _apply_text_corrections(qid: str, text: str) -> str:
    corrections = (_load(TEXT_CORRECTIONS, {}).get("corrections") or [])
    for row in corrections:
        if str(row.get("question_id")) != qid:
            continue
        find = str(row.get("find") or "")
        replace = str(row.get("replace") or "")
        if find and find in text:
            text = text.replace(find, replace)
    return text


def _latex_to_text(value: str) -> str:
    """Make a MinerU ``$$...$$`` block readable without changing its words."""
    value = value.replace("\\\\", "\n")
    value = value.replace("\\wedge", " ∧ ").replace("\\vee", " ∨ ")
    value = re.sub(r"\\(?:mathrm|mathbf|mathit|text|textit|textbf)\s*\{",
                   "", value)
    value = value.replace("\\begin{array}{l}", "")
    value = value.replace("\\end{array}", "")
    value = re.sub(r"\\(?:quad|,|;|!)", " ", value)
    value = value.replace("\\%", "%").replace("\\ ", " ")
    value = re.sub(r"\\([A-Za-z]+)", r"\1", value)
    value = re.sub(r"\{([^{}]*)\}", r"\1", value)
    value = value.replace("{", "").replace("}", "")
    value = re.sub(r"[ \t]{2,}", " ", value)
    return re.sub(r"\n{2,}", "\n", value)


def _clean_md(text: str) -> str:
    text = _fix_mark_spacing(text)
    text = re.sub(r"(?is)<table.*?</table>", "", text)
    text = re.sub(r"(?im)^!\[[^\]]*\]\([^)]*\)\s*$", "", text)
    text = re.sub(r"(?ms)^```[^\n]*\n(.*?)^```\s*$", r"\1", text)
    text = re.sub(r"(?s)\$\$(.*?)\$\$",
                  lambda match: _latex_to_text(match.group(1)), text)
    text = re.sub(r"(?m)^#{1,4}\s*", "", text)
    # MinerU escapes markdown punctuation in printed prose/code.
    text = text.replace(chr(92) + "-", "-")
    text = text.replace(chr(92) + "_", "_")
    text = text.replace(chr(92) + "*", "*")
    text = re.sub(r"</?su[bp]>", "", text, flags=re.I)
    text = APPENDIX_RE.split(text)[0]
    lines = [line for line in text.splitlines()
             if not NOISE_LINE_RE.match(line)]
    text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _question_chunks(full_md: str) -> list[str]:
    """Split a MinerU ``full.md`` into question chunks.

    Two papers lose a QUESTION heading when a question starts after a page
    break.  Their chunk is split at the next top-level ``a)`` that follows a
    ``b)``, which is the only label restart in these papers.
    """
    heads = list(QUESTION_HEAD_RE.finditer(full_md))
    chunks: list[str] = []
    for index, match in enumerate(heads):
        end = heads[index + 1].start() if index + 1 < len(heads) else len(full_md)
        body = _clean_md(full_md[match.end():end])
        labels = list(LABEL_RE.finditer(body))
        splits: list[int] = []
        seen_b = False
        for label in labels:
            letter = label.group(1).lower()
            if letter == "b":
                seen_b = True
            elif letter == "a" and seen_b:
                splits.append(label.start())
                seen_b = False
        previous = 0
        for position in splits:
            chunks.append(body[previous:position].strip())
            previous = position
        chunks.append(body[previous:].strip())
    return [chunk for chunk in chunks if chunk]


def _part_segments(text: str) -> tuple[str, list[dict]]:
    matches = list(PART_RE.finditer(text))
    if not matches:
        return "", [{"label": "", "text": text.strip(), "start": 0}]
    preamble = text[:matches[0].start()].strip()
    parts = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        parts.append({
            "label": match.group(1).lower(),
            "text": text[match.end():end].strip(),
            "start": match.start(),
        })
    return preamble, parts


def _marks_in(text: str) -> list[float]:
    return [float(value) for value in MARKS_RE.findall(text)]


def _part_marks(text: str) -> tuple[float | None, str]:
    values = _marks_in(text)
    if not values:
        return None, "no printed (N marks) line in this part"
    if len(values) == 1:
        return values[0], ""
    return sum(values), "sum of the printed marks"


def _nested_labels(text: str) -> list[str]:
    return [match.group(1).lower() for match in ROMAN_RE.finditer(text)]


def _build_parts(text: str) -> tuple[str, list[dict], list[str]]:
    """Return ``(stem, parts, reasons)`` for one question chunk."""
    stem, segments = _part_segments(text)
    reasons: list[str] = []
    if not any(segment["label"] for segment in segments):
        # A whole-question task (for example the 2025-FEB Q4 ERD).
        marks, note = _part_marks(text)
        if marks is None:
            reasons.append("no printed marks in the question")
        return "", [{
            "label": "",
            "text": text.strip(),
            "marks": marks,
            "marks_mineru": marks,
            "marks_note": note,
            "nested_labels": _nested_labels(text),
        }], reasons
    parts = []
    for segment in segments:
        marks, note = _part_marks(segment["text"])
        label = segment["label"]
        if not label:
            reasons.append("unnumbered text after the question stem")
            continue
        if marks is None:
            reasons.append(f"part {label} has no printed marks: {note}")
        parts.append({
            "label": label,
            "text": segment["text"],
            "marks": marks,
            "marks_mineru": marks,
            "marks_note": note,
            "nested_labels": _nested_labels(segment["text"]),
        })
    return stem, parts, reasons


def _paper_rows() -> list[dict]:
    register = _load(REGISTER, [])
    if isinstance(register, dict):
        register = register.get("unique_papers") or []
    rows = []
    for row in register:
        if row.get("is_duplicate"):
            continue
        source = str(row.get("source") or row.get("file") or "")
        month = str(row.get("month") or "").strip().upper()
        year = str(row.get("year") or "").strip()
        code = MONTH_CODE.get(month, month[:3])
        if not source or not year or not code:
            continue
        paper_id = f"{SUBJECT}-{year}-{code}"
        rows.append({
            "paper_id": paper_id,
            "file": source,
            "pages": int(row.get("pages") or 0),
        })
    return rows


def _ocr_section(paper_file: str, question_no: int) -> str:
    path = OCR_DIR / f"{Path(paper_file).stem}.txt"
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    headings = list(re.finditer(rf"(?mi)^\s*QUESTION\s+{int(question_no)}\s*$",
                                text))
    if not headings:
        return ""
    match = headings[0]
    following = re.search(r"(?mi)^\s*QUESTION\s+\d{1,3}\s*$",
                          text[match.end():])
    end = match.end() + following.start() if following else len(text)
    return text[match.end():end]


def _ocr_marks(paper_file: str, question_no: int) -> dict:
    """Return OCR part/whole marks for one question.

    The OCR text uses a few broken spellings of "marks" (``mafts``,
    ``ma*s``), so the tolerant pattern is deliberately wider than the page
    text pattern.  The values are evidence only; the caller decides whether to
    use them.
    """
    section = _ocr_section(paper_file, question_no)
    if not section:
        return {"parts": {}, "whole": None, "count": 0}
    labels = list(re.finditer(r"(?mi)^\s*([a-h])\s*\)", section))
    parts: dict[str, float] = {}
    if labels:
        for index, label in enumerate(labels):
            end = (labels[index + 1].start() if index + 1 < len(labels)
                   else len(section))
            values = [float(value) for value in
                      OCR_MARKS_RE.findall(section[label.end():end])]
            if values:
                parts[label.group(1).lower()] = sum(values)
        count = len(parts)
        return {"parts": parts, "whole": None, "count": count}
    values = [float(value) for value in OCR_MARKS_RE.findall(section)]
    return {"parts": {}, "whole": sum(values) if values else None,
            "count": len(values)}


def _asset_question_no(paper_id: str, asset: dict) -> int | None:
    key = f"{paper_id}/{asset.get('asset_id')}"
    assignments = (_load(ASSET_OVERRIDES, {}).get("asset_assignments") or {})
    assignment = assignments.get(key)
    if isinstance(assignment, dict):
        if assignment.get("question_no") is not None:
            return int(assignment["question_no"])
        if assignment.get("question_id"):
            return int(str(assignment["question_id"]).rsplit("-Q", 1)[-1])
    index = asset.get("question_index")
    if isinstance(index, int):
        return index + 1
    return None


class _TableParser(HTMLParser):
    """Turn a MinerU ``<table>`` into the review sheet's native-table shape."""

    def __init__(self) -> None:
        super().__init__()
        self.rows: list[dict] = []
        self.row: dict | None = None
        self.cell: dict | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "tr":
            self.row = {"cells": []}
        elif tag in {"td", "th"} and self.row is not None:
            values = dict(attrs)
            try:
                colspan = int(values.get("colspan") or 1)
            except ValueError:
                colspan = 1
            self.cell = {"text": "", "colspan": colspan}
        elif tag == "br" and self.cell is not None:
            self.cell["text"] += " "

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell["text"] += data

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"td", "th"} and self.row is not None and self.cell is not None:
            self.row["cells"].append({
                "text": re.sub(r"\s+", " ", self.cell["text"]).strip(),
                "colspan": self.cell["colspan"],
            })
            self.cell = None
        elif tag == "tr" and self.row is not None:
            if self.row["cells"]:
                self.rows.append(self.row)
            self.row = None


def _native_table(table_html: str) -> dict:
    if not table_html or "<table" not in table_html.lower():
        return {}
    parser = _TableParser()
    try:
        parser.feed(table_html)
    except Exception:
        return {}
    return {"rows": parser.rows} if parser.rows else {}


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
            if max(x0, y0, x1, y1) <= 1.0:
                x0, y0 = x0 * width, y0 * height
                x1, y1 = x1 * width, y1 * height
            clip = pymupdf.Rect(max(0, x0), max(0, y0),
                                min(width, x1), min(height, y1))
            if clip.is_empty:
                clip = page.rect
            pix = page.get_pixmap(dpi=300, clip=clip, alpha=False)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(pix.tobytes("png"))
        return True
    except Exception:
        return False


def _apply_marks_overrides(qid: str, parts: list[dict]) -> None:
    payload = ((_load(OVERRIDES, {}).get("overrides") or {}).get(qid) or {})
    override_parts = payload.get("parts") or {}
    for part in parts:
        label = str(part.get("label") or "")
        if label not in override_parts:
            continue
        value = float(override_parts[label])
        if part.get("marks") is not None and float(part["marks"]) != value:
            part["marks_conflict_mineru"] = part["marks"]
        part["marks"] = value
        part["marks_source"] = "page_render"
        part["marks_note"] = str(payload.get("evidence") or "")


def _apply_ocr_marks(parts: list[dict], ocr: dict, qid: str) -> None:
    for part in parts:
        label = str(part.get("label") or "")
        ocr_value = (ocr.get("parts") or {}).get(label)
        part["marks_ocr"] = ocr_value if ocr_value is not None else ""
        if part.get("marks_source") == "page_render":
            continue
        if part.get("marks") is None and ocr_value is not None:
            part["marks"] = ocr_value
            part["marks_source"] = "ocr"
            part["marks_note"] = "recovered from the same paper's OCR text"
            continue
        if (ocr_value is not None and part.get("marks") is not None
                and float(ocr_value) != float(part["marks"])):
            part["marks_conflict"] = ocr_value
        if part.get("marks") is not None:
            part.setdefault("marks_source", "mineru")


def _link_assets(paper: dict, dossier: dict, bank: BankStore,
                 questions: dict[int, dict]) -> tuple[list[dict], list[dict]]:
    assets: list[dict] = []
    unsure: list[dict] = []
    source_pdf = config.PAPERS_ROOT / SUBJECT / str(paper["file"])
    exclusions = _load(EXCLUSIONS, {}).get("assets") or {}
    assigned: set[str] = set()

    def add_asset(question_no: int, source_id: str, kind: str, label: str,
                  caption: str, page_idx: int, bbox: list[float],
                  image: Path | None, treatment: str,
                  provenance: dict, table_html: str = "",
                  allow_crop: bool = True) -> None:
        question = questions.get(question_no)
        if question is None:
            return
        qid = question["id"]
        sequence = len(question["_asset_records"]) + 1
        letter = "T" if kind == "table" else "F"
        aid = f"A-{qid}-{letter}{sequence}"
        target = bank.assets_dir / f"{aid}.png"
        copied = bool(image and image.is_file()
                      and _save_asset_image(image, target))
        if not copied and allow_crop:
            copied = _crop_page_bbox(source_pdf, page_idx, bbox, target)
            treatment = "page_crop_bbox"
        record = {
            "id": aid,
            "question_id": qid,
            "kind": kind,
            "path": str(target) if copied else "",
            "source_paper": paper["paper_id"],
            "source_file": paper["file"],
            "source_page": int(page_idx) + 1,
            "bbox": bbox,
            "dpi": 300 if treatment == "page_crop_bbox" else None,
            "sha256": _sha256(target) if copied else "",
            "caption": caption or label or aid,
            "label": label,
            "treatment": treatment,
            "verdict": "pending",
            "provenance": provenance,
            "table_html": table_html,
            "native_table": _native_table(table_html),
        }
        if not copied:
            record["issue"] = "no readable image crop"
            unsure.append({
                "question_id": qid,
                "item": f"asset {aid} has no readable image crop",
                "blocking": True,
                "opened": _now()[:10],
            })
        bank.save_asset(record)
        assets.append(record)
        question["_asset_records"].append(record)
        question["assets"].append(aid)
        assigned.add(source_id)

    # Page crops first so a recovered Figure 2 precedes the MinerU Figure 3.
    for spec in (_load(ASSET_OVERRIDES, {}).get("page_crops") or []):
        if str(spec.get("paper_id")) != paper["paper_id"]:
            continue
        label = str(spec.get("label") or "")
        kind = str(spec.get("kind") or
                   ("figure" if label.lower().startswith("figure")
                    else "picture"))
        add_asset(int(spec.get("question_no") or 0), "", kind, label,
                  str(spec.get("caption") or label),
                  int(spec.get("page_idx") or 0), spec.get("bbox") or [],
                  Path(str(spec.get("image") or "")) if spec.get("image")
                  else None,
                  str(spec.get("treatment") or "page_crop_bbox"),
                  {"source": "page crop override"},
                  allow_crop=True)

    for asset in dossier.get("assets") or []:
        source_id = str(asset.get("asset_id") or "")
        key = f"{paper['paper_id']}/{source_id}"
        if key in exclusions or source_id in assigned:
            continue
        question_no = _asset_question_no(paper["paper_id"], asset)
        if question_no is None:
            target = (bank.root / "unassigned" /
                      f"{paper['paper_id']}-{source_id}.png")
            copied = _save_asset_image(Path(str(asset.get("img_path") or "")),
                                       target)
            if not copied:
                copied = _crop_page_bbox(source_pdf,
                                         int(asset.get("page_idx", 0)),
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
            continue
        label = str(asset.get("label") or "")
        assigned_kind = str((_load(ASSET_OVERRIDES, {}).get(
            "asset_assignments") or {}).get(key, {}).get("kind") or "")
        kind = (assigned_kind
                or ("figure" if label.lower().startswith("figure")
                    else "table" if label.lower().startswith("table")
                    or str(asset.get("kind")) == "table"
                    else "picture"))
        add_asset(question_no, source_id, kind, label,
                  str(asset.get("caption") or label),
                  int(asset.get("page_idx", 0)), asset.get("bbox") or [],
                  Path(str(asset.get("img_path") or "")),
                  "original_crop",
                  asset.get("provenance") or {},
                  str(asset.get("table_html") or ""))
    return assets, unsure


def _paper_questions(paper: dict, dossier: dict,
                     bank: BankStore) -> tuple[list[dict], list[dict], list[dict]]:
    questions: list[dict] = []
    unsure: list[dict] = []
    source_pdf = config.PAPERS_ROOT / SUBJECT / str(paper["file"])
    normalized_questions = dossier.get("questions") or []
    cache = Path(str(paper.get("_cache") or ""))
    full_md_path = cache / "full.md"
    full_md = (full_md_path.read_text(encoding="utf-8", errors="replace")
               if full_md_path.is_file() else "")
    chunks = _question_chunks(full_md) if full_md else []
    expected = len(normalized_questions)
    if len(chunks) != expected:
        unsure.append({
            "paper_id": paper["paper_id"],
            "item": (f"full.md produced {len(chunks)} question chunks for "
                     f"{expected} normalised questions; using the normalised "
                     "question text"),
            "blocking": True,
            "opened": _now()[:10],
        })
        chunks = [str(question.get("text") or "")
                  for question in normalized_questions]

    normalized_by_number = {
        int(question.get("number") or 0): question
        for question in normalized_questions}
    content_pages: dict[str, int] = {}
    content_list = str(dossier.get("content_list") or "")
    if content_list and Path(content_list).is_file():
        try:
            rows = json.loads(Path(content_list).read_text(encoding="utf-8"))
            content_pages = {
                f"B{position:04d}": int(row.get("page_idx", 0)) + 1
                for position, row in enumerate(rows)
            }
        except (OSError, ValueError, TypeError):
            content_pages = {}

    for index, chunk in enumerate(chunks):
        number = index + 1
        source = normalized_by_number.get(number) or {}
        qid = f"{paper['paper_id']}-Q{number}"
        text = _apply_text_corrections(qid, _clean_md(chunk))
        stem, parts, reasons = _build_parts(text)
        _apply_marks_overrides(qid, parts)
        ocr = _ocr_marks(paper["file"], number)
        _apply_ocr_marks(parts, ocr, qid)
        known_parts = [part for part in parts
                       if part.get("marks") is not None]
        marks = sum(float(part["marks"]) for part in known_parts)
        complete = bool(parts) and len(known_parts) == len(parts)
        if not parts:
            reasons.append("no parts found")
        if marks <= 0:
            reasons.append("no printed marks could be read")
        if len(text) < 40:
            reasons.append("question text is too short")
        refs = sorted(set(source.get("refs") or []),
                      key=lambda value: (
                          str(value).split()[0],
                          int(str(value).split()[1])
                          if len(str(value).split()) > 1
                          and str(value).split()[1].isdigit() else 0))
        start_page = int(source.get("page_idx", 0)) + 1
        pages = {start_page}
        for block_id in source.get("blocks") or []:
            page = content_pages.get(str(block_id))
            if page and page >= start_page:
                pages.add(page)
        pages = sorted(pages)
        block = {
            "text": text,
            "normalised": normalize_text(text),
            "page": pages[0],
            "bbox": source.get("bbox") or [],
        }
        question = {
            "id": qid,
            "source_paper": paper["paper_id"],
            "source_file": paper["file"],
            "pages": pages,
            "part": f"Q{number}",
            "slot": str(number),
            "question_no": number,
            "slot_hint": f"Q{number}",
            "marks": int(marks) if float(marks).is_integer() else marks,
            "subpart_marks": [
                {"label": part["label"], "marks": part["marks"],
                 "source": part.get("marks_source", "")}
                for part in parts if part.get("marks") is not None],
            "marks_complete": complete,
            "marks_ocr": (ocr.get("parts") or {}),
            "stem": stem,
            "native_text": text,
            "native_text_blocks": [block],
            "native_tables": [],
            "parts": parts,
            "assets": [],
            "refs": refs,
            "unresolved_refs": [],
            "topic_tags": _topic_tags(text),
            "duplicate_cluster": "",
            "status": "extracted",
            "quality_score": 0.0,
            "content_hash": "",
            "parse_notes": reasons,
            "source": {
                "parser": "mineru",
                "model": dossier.get("model", ""),
                "paper_id": paper["paper_id"],
                "question_id": source.get("question_id", ""),
                "dossier": paper.get("_dossier", ""),
                "text_source": "full.md",
            },
            "_asset_records": [],
        }
        questions.append(question)

    questions_by_number = {question["question_no"]: question
                           for question in questions}
    assets, asset_unsure = _link_assets(paper, dossier, bank, questions_by_number)
    unsure.extend(asset_unsure)

    # Resolve refs and finalise each question after asset linking.
    for question in questions:
        linked = question.pop("_asset_records")
        labels = {str(asset.get("label") or "").lower()
                  for asset in linked}
        labels |= {re.sub(r"\.0$", "", label) for label in labels}
        unresolved = []
        for ref in question.get("refs") or []:
            key = str(ref).lower()
            key = re.sub(r"\.0$", "", key)
            if key not in labels:
                unresolved.append(ref)
        question["unresolved_refs"] = unresolved
        question["pages"] = sorted(
            set(question["pages"])
            | {asset["source_page"] for asset in linked})
        reasons = list(question.get("parse_notes") or [])
        if unresolved:
            reasons.append("unresolved references: " + ", ".join(unresolved))
        if any(not asset.get("path") for asset in linked):
            reasons.append("one or more image crops are missing")
        if reasons:
            question["status"] = "needs_fix"
            for reason in reasons:
                unsure.append({
                    "question_id": question["id"],
                    "item": reason,
                    "blocking": True,
                    "opened": _now()[:10],
                })
        question["parse_notes"] = reasons
        question["content_hash"] = question_content_hash(question)
    return questions, assets, unsure


def _prune(bank: BankStore, questions: set[str], assets: set[str],
           unassigned: set[str]) -> None:
    for path in bank.questions_dir.glob("*.json"):
        if path.stem not in questions:
            path.unlink()
    for path in bank.assets_dir.glob("*"):
        if path.is_file() and path.stem not in assets:
            path.unlink()
    for path in (bank.root / "unassigned").glob("*.png"):
        if path.name not in unassigned:
            path.unlink()


def build(papers: list[str] | None = None, *, model: str = "vlm") -> dict:
    rows = _paper_rows()
    if not rows:
        raise SystemExit(f"{REGISTER} is missing; run the V0 register first")
    status = _load(STATUS, {})
    wanted = {code.upper() for code in papers or []}
    bank = BankStore(BANK).ensure()
    all_questions: list[dict] = []
    all_assets: list[dict] = []
    all_unsure: list[dict] = []
    papers_done = []
    for paper in rows:
        if wanted and paper["paper_id"].upper() not in wanted:
            continue
        entry = (status.get("papers") or {}).get(paper["paper_id"]) or {}
        if entry.get("status") != "done":
            all_unsure.append({
                "paper_id": paper["paper_id"],
                "item": "no completed V1 extraction",
                "blocking": True,
                "opened": _now()[:10],
            })
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
        paper = dict(paper)
        paper["_cache"] = str(cache)
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
        linked = {asset["id"]: asset for asset in all_assets
                  if asset.get("question_id") == question["id"]}
        question["quality_score"] = quality_score(question, linked)
        question["quality_band"] = quality_band(question["quality_score"])
        bank.save_question(question)
    near_pairs = near_duplicate_pairs(all_questions)
    exclusions = _load(EXCLUSIONS, {}).get("assets") or {}
    expected_papers = sorted(wanted) if wanted else [
        paper["paper_id"] for paper in rows]
    missing_papers = [paper_id for paper_id in expected_papers
                      if paper_id not in papers_done]
    counts = {
        "papers": len(papers_done),
        "papers_expected": len(expected_papers),
        "papers_missing": len(missing_papers),
        "questions": len(all_questions),
        "extracted": sum(1 for question in all_questions
                         if question["status"] == "extracted"),
        "needs_fix": sum(1 for question in all_questions
                         if question["status"] == "needs_fix"),
        "rejected": 0,
        "assets": len(all_assets),
        "fallback_assets": sum(1 for asset in all_assets
                               if asset["treatment"] == "page_crop_fallback"),
        "references": sum(len(question.get("refs") or [])
                          for question in all_questions),
        "unresolved_references": sum(
            len(question.get("unresolved_refs") or [])
            for question in all_questions),
        "duplicate_clusters": sum(1 for cluster in duplicate_clusters
                                  if cluster["count"] > 1),
        "near_duplicate_pairs": len(near_pairs),
        "unsure": len(all_unsure),
        "excluded_assets": len(exclusions),
        "marks_total": sum(float(question.get("marks") or 0)
                           for question in all_questions),
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
        "excluded_assets": exclusions,
        "questions": [{
            "id": question["id"],
            "source_paper": question["source_paper"],
            "marks": question["marks"],
            "status": question["status"],
            "topic_tags": question["topic_tags"],
            "quality_score": question["quality_score"],
            "quality_band": question["quality_band"],
            "refs": question["refs"],
            "assets": question["assets"],
        } for question in all_questions],
    }
    save_json(BANK / "index.json", index)
    _prune(
        bank,
        {question["id"] for question in all_questions},
        {asset["id"] for asset in all_assets},
        {Path(str(item["path"])).name for item in all_unsure
         if item.get("path")})
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
        title="ICT502 v2 question bank", extra_assets=extra_assets)
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
            "paper", "question_id", "part", "mineru_marks", "ocr_marks",
            "used_marks", "used_source", "question_status", "note"])
        for question in questions:
            for part in question.get("parts") or []:
                writer.writerow([
                    question["source_paper"],
                    question["id"],
                    part.get("label", ""),
                    part.get("marks_mineru", ""),
                    part.get("marks_ocr", ""),
                    part.get("marks", ""),
                    part.get("marks_source", ""),
                    question["status"],
                    part.get("marks_note", ""),
                ])
    return path


def _write_paper_index(index: dict, review_dir: Path, *,
                       filename: str = "index_by_paper.html",
                       sheet: str = "index.html",
                       statuses: set[str] | None = None,
                       heading: str = "ICT502 v2 bank — by paper") -> Path:
    groups: dict[str, list[dict]] = {}
    for question in index.get("questions") or []:
        if statuses is not None and question.get("status") not in statuses:
            continue
        groups.setdefault(question["source_paper"], []).append(question)
    rows = []
    for paper, questions in sorted(groups.items()):
        links = ", ".join(
            f"<a href='{sheet}#{question['id']}'>{question['id']}</a>"
            for question in questions)
        marks = sum(float(question.get("marks") or 0)
                    for question in questions)
        needs_fix = sum(1 for question in questions
                        if question.get("status") == "needs_fix")
        rows.append(
            f"<tr><td>{paper}</td><td>{len(questions)}</td>"
            f"<td>{marks}</td><td>{needs_fix}</td><td>{links}</td></tr>")
    page = f"""<!doctype html>
<html><head><meta charset="utf-8">
<title>{heading}</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 2rem; }}
table {{ border-collapse: collapse; }}
td, th {{ border: 1px solid #aaa; padding: .3rem .5rem; }}
</style></head><body>
<h1>{heading}</h1>
<p><a href="{sheet}">Open the review sheet</a></p>
<table><tr><th>Paper</th><th>Questions</th><th>Marks</th>
<th>Needs fix</th><th>Questions</th></tr>
{chr(10).join(rows)}
</table></body></html>
"""
    path = review_dir / filename
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
        row["marks"] += float(question.get("marks") or 0)
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
        "excluded_assets": index.get("excluded_assets") or {},
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
        "# ICT502 v2 — Gate A bank review",
        "",
        f"Generated: {report['generated_on']}",
        ("Status: **approved by owner**"
         if report.get("status") == "approved"
         else "Status: **pending owner approval**"),
        "",
        "## Counts",
        "",
        f"- Papers processed: {counts['papers']} of "
        f"{counts['papers_expected']} "
        f"({counts['papers_missing']} missing a V1 dossier)",
        f"- Questions: {counts['questions']} "
        f"({counts.get('approved', 0)} approved, "
        f"{counts['needs_fix']} needs fix, "
        f"{counts.get('rejected', 0)} rejected)",
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
    lines += ["", "## Excluded non-question assets", ""]
    excluded = report.get("excluded_assets") or {}
    if not excluded:
        lines.append("None.")
    for key, item in sorted(excluded.items()):
        if isinstance(item, str):
            lines.append(f"- `{key}`: {item}")
        else:
            lines.append(
                f"- `{key}`: {item.get('reason', '')} "
                f"(verdict: {item.get('verdict', '')})")
    lines += [
        "",
        "## Review",
        "",
        f"- Sheet: `{report['review_sheet']}`",
        f"- Marks table: `{report.get('marks_csv', '')}`",
        f"- Questions: `{report['questions_dir']}`",
        f"- Assets: `{report['assets_dir']}`",
        "",
        ("Gate A is **approved**. The bank may be used for V3/V4; rejected "
         "and needs_fix records stay unselectable."
         if report.get("status") == "approved"
         else "Gate A is not approved. Review the sheet, correct marks/assets "
              "and record the owner approval in `bank/approvals.json`."),
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
