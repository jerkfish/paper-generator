"""Build a draft, verbatim question bank for CSC429 from the layout layer.

The bank is intentionally conservative: every character of question text is
copied from ``data/tracking/csc429/layout/<paper_id>.json``.  No model is
used and no text is generated or paraphrased.  Marks, subparts and figure
references are recovered from geometry and are flagged when the evidence is
weak.

Run::

    python -m src.subjects.csc429.questions --force

Only files below ``data/tracking/csc429`` are written.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter, OrderedDict
from pathlib import Path
from typing import Any, Iterable

from src import config

SUBJECT = "CSC429"
TRACKING = config.TRACKING_DIR / "csc429"
OUTPUT_NAME = "question_bank_draft.json"
SCHEMA_VERSION = 1

# ---------------------------------------------------------------------------
# regular expressions
# ---------------------------------------------------------------------------

# ``QUESTION 1`` and the OCR spellings seen in the corpus:
# OUESTION, QUEST]ON, QUESTION 1O, QUESTION I.
_QUESTION_RE = re.compile(
    r"^[QO]\s*U\s*E\s*S\s*T\s*[\)\]\[]?\s*[I1l]?\s*[O0]?\s*N"
    r"\s*[.:]?\s*([0-9OIl]{1,3})\s*[.:]?$",
    re.I,
)
_PART_RE = re.compile(r"^PART\s*([AB])\b", re.I)

# ``(5 marks)`` and OCR damage such as ``('l mark)`` or ``5 marks)``.
_MARK_RE = re.compile(
    r"^[\(\[]?\s*['\"`]?\s*([0-9OIlSs]{1,2})\s*marks?\s*[\)\]]?$",
    re.I,
)

# Subparts: a)..h) and i)..vi) at the first/second indent.  ``(iv)`` is a
# layout artefact used by some OCR tables; the indent test rejects those.
_SUBPART_RE = re.compile(
    r"^(?:\(?([a-hA-H])\)|\(?((?:i{1,3}|iv|v|vi|vii))\))\s*",
    re.I,
)

_FIGURE_RE = re.compile(r"\b(Figure|Table)\s*(\d+)", re.I)

_CONFIDENTIAL_RE = re.compile(r"CONF[I!1]DENTIAL|^CONFIDENT$", re.I)
_HEADER_RE = re.compile(r"^(?:CS|CD)[A-Z0-9/\s]*CSC429$", re.I)
_HAK_RE = re.compile(r"(?:©|@)?\s*Hak\s*C[i1l]pta", re.I)
_DO_NOT_TURN_RE = re.compile(r"DO\s*NOT\s*TURN", re.I)
_END_RE = re.compile(r"^END\s+OF\s+(?:QUESTION\s+PAPER|EXAMINATION)$", re.I)
_BARE_PAGE_RE = re.compile(r"^\d{1,3}$")
_PRINTED_PAGES_RE = re.compile(
    r"^This\s+examination\s+paper\s+consists\s+of\s+.*printed\s+pages$", re.I
)

TOP_BAND = 0.10
BOTTOM_BAND = 0.90
QUESTION_LEFT_MARGIN = 0.35
SUBPART_LEFT_MARGIN = 0.30
MAX_MARK_DISTANCE = 250.0
MAX_QUESTION_PAGES = 2

MARK_SOURCES = {"explicit", "manual_verified", "grouped", "missing", "unsure"}

_MONTHS = {
    "JANUARY": 1,
    "FEBRUARY": 2,
    "MARCH": 3,
    "APRIL": 4,
    "MAY": 5,
    "JUNE": 6,
    "JULY": 7,
    "AUGUST": 8,
    "SEPTEMBER": 9,
    "OCTOBER": 10,
    "NOVEMBER": 11,
    "DECEMBER": 12,
}


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------


def _norm_ws(value: str) -> str:
    return " ".join(str(value).split())


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _as_bbox(raw: Any) -> list[float] | None:
    if not isinstance(raw, (list, tuple)) or len(raw) != 4:
        return None
    try:
        values = [float(item) for item in raw]
    except (TypeError, ValueError):
        return None
    if not all(math.isfinite(item) for item in values):
        return None
    x0, y0, x1, y1 = values
    if x1 < x0 or y1 < y0:
        return None
    return [round(item, 2) for item in values]


def _line_text(line: dict[str, Any]) -> str:
    return str(line.get("text", ""))


def _is_furniture(
    text: str, bbox: list[float], page_width: float, page_height: float
) -> bool:
    """True for running heads/feet, watermarks and bare page numbers."""
    x0, y0, x1, y1 = bbox
    if y1 < TOP_BAND * page_height:
        return True
    if y0 > BOTTOM_BAND * page_height:
        return True
    stripped = text.strip()
    if not stripped:
        return True
    if _CONFIDENTIAL_RE.search(stripped):
        return True
    if _HEADER_RE.match(stripped):
        return True
    if _HAK_RE.search(stripped):
        return True
    if _DO_NOT_TURN_RE.search(stripped):
        return True
    if _END_RE.match(stripped):
        return True
    if _PRINTED_PAGES_RE.match(stripped):
        return True
    # A bare number is only a page number near the top/bottom of the page;
    # mid-page bare numbers are table cells and must stay in the body.
    if _BARE_PAGE_RE.match(stripped) and (
        y0 < 0.15 * page_height or y0 > 0.85 * page_height
    ):
        return True
    return False


def _ocr_digit(raw: str) -> int | None:
    """Normalise a heading/mark number that OCR may have garbled."""
    value = (
        raw.upper()
        .replace("O", "0")
        .replace("I", "1")
        .replace("L", "1")
        .replace("S", "5")
    )
    if not value.isdigit():
        return None
    number = int(value)
    if 1 <= number <= 99:
        return number
    return None


def _parse_question_heading(text: str) -> tuple[int, bool] | None:
    """Return ``(question_no, ocr_variant)`` for an isolated heading line."""
    candidate = text.strip()
    # Some OCR outputs literal ``QUEST[I1]ON``; collapse the class notation.
    candidate = re.sub(r"\[[I1l]\]", "I", candidate)
    match = _QUESTION_RE.match(candidate)
    if not match:
        return None
    number = _ocr_digit(match.group(1))
    if number is None:
        return None
    word = re.sub(r"[^A-Za-z]", "", candidate).upper()
    variant = word != "QUESTION" or not match.group(1).isdigit()
    return number, variant


def _parse_part_heading(text: str) -> str | None:
    match = _PART_RE.match(text.strip())
    return match.group(1).upper() if match else None


def _parse_mark(text: str) -> int | None:
    match = _MARK_RE.match(text.strip())
    if not match:
        return None
    return _ocr_digit(match.group(1))


def _parse_subpart(text: str) -> tuple[str, int] | None:
    """Return ``(label, level)`` where letters are level 1 and romans level 2."""
    match = _SUBPART_RE.match(text.strip())
    if not match:
        return None
    if match.group(1):
        return match.group(1).lower(), 1
    return match.group(2).lower(), 2


def _normalise_ref(kind: str, number: str) -> str:
    return f"{kind.title()} {int(number)}"


def _figure_refs_with_pages(
    entries: Iterable[dict[str, Any]],
) -> tuple[list[str], dict[str, set[int]]]:
    """Return refs in appearance order plus the page(s) each ref occurs on."""
    refs: list[str] = []
    pages: dict[str, set[int]] = {}
    for entry in entries:
        for match in _FIGURE_RE.finditer(entry["text"]):
            label = _normalise_ref(match.group(1), match.group(2))
            if label not in pages:
                refs.append(label)
                pages[label] = set()
            pages[label].add(int(entry["page"]))
    return refs, pages


def _normalise_asset_label(value: str) -> str:
    match = re.search(r"\b(Figure|Table)\s*[_\-]?\s*(\d+)", value, re.I)
    if match:
        return _normalise_ref(match.group(1), match.group(2))
    return value.strip().lower()


def _add_flag(flags: list[str], flag: str) -> None:
    if flag not in flags:
        flags.append(flag)


# ---------------------------------------------------------------------------
# input loading
# ---------------------------------------------------------------------------


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _register_records(tracking: Path) -> list[dict[str, Any]]:
    register = tracking / "papers_register.json"
    if not register.exists():
        return []
    try:
        records = _load_json(register)
    except (OSError, ValueError):
        return []
    if not isinstance(records, list):
        return []
    return [row for row in records if isinstance(row, dict)]


def _duplicate_sources(tracking: Path) -> set[str]:
    return {
        str(row.get("source", ""))
        for row in _register_records(tracking)
        if row.get("duplicate_of")
    }


def _register_paper_id(record: dict[str, Any]) -> str:
    try:
        year = int(record.get("year"))
    except (TypeError, ValueError):
        year = 0
    month = _MONTHS.get(str(record.get("month", "")).upper())
    if year and month:
        return f"CSC429-{year}-{month:02d}"
    source = str(record.get("source", "")).strip()
    stem = re.sub(r"[^A-Za-z0-9]+", "-", Path(source).stem).strip("-")
    return f"CSC429-{stem or 'unknown'}"


def _page_image_pages(tracking: Path, paper_id: str) -> set[int] | None:
    """Page numbers with a captured image, or ``None`` when unknown."""
    manifest = tracking / "pages" / paper_id / "manifest.json"
    if not manifest.exists():
        return None
    try:
        payload = _load_json(manifest)
    except (OSError, ValueError):
        return None
    pages: set[int] = set()
    for page in payload.get("pages", []) or []:
        if not isinstance(page, dict):
            continue
        image = page.get("image")
        page_no = page.get("page")
        if image and page_no is not None:
            pages.add(int(page_no))
    return pages


def _asset_records(tracking: Path) -> list[dict[str, Any]] | None:
    """Load ``assets/manifest.json`` in whichever shape it was produced."""
    manifest = tracking / "assets" / "manifest.json"
    if not manifest.exists():
        return None
    try:
        payload = _load_json(manifest)
    except (OSError, ValueError):
        return None

    raw_records: list[dict[str, Any]] = []
    if isinstance(payload, list):
        raw_records = [item for item in payload if isinstance(item, dict)]
    elif isinstance(payload, dict):
        assets = payload.get("assets")
        if isinstance(assets, list):
            raw_records = [item for item in assets if isinstance(item, dict)]
        elif isinstance(assets, dict):
            raw_records = [
                {**value, "asset_id": value.get("asset_id", key)}
                for key, value in assets.items()
                if isinstance(value, dict)
            ]
        else:
            # A mapping of asset_id -> record.
            raw_records = [
                {**value, "asset_id": value.get("asset_id", key)}
                for key, value in payload.items()
                if isinstance(value, dict)
            ]

    records: list[dict[str, Any]] = []
    for item in raw_records:
        label = (
            item.get("label")
            or item.get("figure_label")
            or item.get("caption")
            or item.get("name")
        )
        kind = item.get("kind") or item.get("type")
        number = item.get("number") or item.get("index")
        if not label and kind and number is not None:
            label = f"{kind} {number}"
        if not label:
            continue
        asset_id = item.get("asset_id") or item.get("id")
        if asset_id is None:
            continue
        page = item.get("page")
        if page is None:
            page = item.get("source_page", item.get("page_no"))
        records.append(
            {
                "asset_id": str(asset_id),
                "label": _normalise_asset_label(str(label)),
                "page": int(page) if page is not None else None,
                "paper_id": str(
                    item.get("paper_id") or item.get("paper") or ""
                ),
            }
        )
    records.sort(key=lambda row: (row["label"], row["paper_id"], row["asset_id"]))
    return records


def _match_assets(
    refs: list[str],
    ref_pages: dict[str, set[int]],
    paper_id: str,
    records: list[dict[str, Any]] | None,
) -> tuple[list[str], list[str]]:
    """Return ``(asset_ids, unresolved_refs)`` preserving ref order.

    A reference is matched by label and by the page on which the reference
    text appears, which keeps ``Figure 2`` on page 1 distinct from
    ``Figure 2`` on page 2.  When a question cites a table/figure that was
    printed on an earlier page, the nearest same-paper asset is used as a
    fallback rather than losing the link.
    """
    if not refs:
        return [], []
    if not records:
        return [], list(refs)
    ids: list[str] = []
    unresolved: list[str] = []
    for ref in refs:
        pages = ref_pages.get(ref, set())
        candidates = [
            row
            for row in records
            if row["label"] == ref
            and (not row["paper_id"] or row["paper_id"] == paper_id)
        ]
        same_page = [
            row for row in candidates
            if row["page"] is None or not pages or row["page"] in pages
        ]
        matches = same_page
        if not matches and candidates:
            reference_page = min(pages) if pages else None
            if reference_page is not None:
                before = [
                    row for row in candidates
                    if row["page"] is not None and row["page"] <= reference_page
                ]
                if before:
                    nearest = max(row["page"] for row in before)
                    matches = [row for row in before if row["page"] == nearest]
                else:
                    nearest = min(
                        row["page"] for row in candidates
                        if row["page"] is not None
                    ) if any(row["page"] is not None for row in candidates) else None
                    matches = [
                        row for row in candidates if row["page"] == nearest
                    ] if nearest is not None else candidates
            else:
                matches = candidates[:1]
        if not matches:
            unresolved.append(ref)
            continue
        for row in matches:
            if row["asset_id"] not in ids:
                ids.append(row["asset_id"])
    return ids, unresolved


# ---------------------------------------------------------------------------
# layout parsing
# ---------------------------------------------------------------------------


def _layout_entries(
    layout: dict[str, Any],
    paper_id: str,
    unsure: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[int, float], bool]:
    """Flatten the layout into ordered, furniture-free line entries.

    Returns ``(entries, had_missing_boxes)``.
    """
    entries: list[dict[str, Any]] = []
    missing_boxes = 0
    for page in layout.get("pages", []) or []:
        if not isinstance(page, dict):
            continue
        try:
            page_no = int(page.get("page"))
            width = float(page.get("width"))
            height = float(page.get("height"))
        except (TypeError, ValueError):
            continue
        for line in page.get("lines", []) or []:
            if not isinstance(line, dict):
                continue
            text = _line_text(line)
            if not text.strip():
                continue
            bbox = _as_bbox(line.get("bbox"))
            if bbox is None:
                missing_boxes += 1
                continue
            if _is_furniture(text, bbox, width, height):
                continue
            x0, y0, x1, y1 = bbox
            entries.append(
                {
                    "page": page_no,
                    "text": text,
                    "bbox": bbox,
                    "x0": x0,
                    "y0": y0,
                    "x1": x1,
                    "y1": y1,
                    "width": width,
                    "is_mark": _parse_mark(text) is not None,
                }
            )
    entries.sort(
        key=lambda item: (
            item["page"],
            item["y0"],
            item["x0"],
            item["y1"],
            item["text"],
        )
    )
    if missing_boxes:
        unsure.append(
            {
                "paper_id": paper_id,
                "code": "missing_bbox",
                "detail": f"{missing_boxes} layout line(s) had no usable bbox",
            }
        )
    return entries, bool(missing_boxes)


def _build_blocks(
    entries: list[dict[str, Any]],
    paper_id: str,
    unsure: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], bool]:
    """Split entries into question blocks delimited by headings.

    Returns ``(blocks, part_was_assumed)``.
    """
    blocks: list[dict[str, Any]] = []
    current_part: str | None = None
    current: dict[str, Any] | None = None
    part_assumed = False
    seen_numbers: dict[str, set[int]] = {}
    inferred_part = False

    for entry in entries:
        text = entry["text"]
        left = entry["x0"] < QUESTION_LEFT_MARGIN * entry["width"]

        part = _parse_part_heading(text) if left else None
        if part:
            current = None
            current_part = part
            seen_numbers.setdefault(part, set())
            continue

        heading = _parse_question_heading(text) if left else None
        if heading:
            number, ocr_variant = heading
            part = current_part
            inferred_this_block = False
            if part is None:
                part = "A"
                current_part = "A"
                part_assumed = True
                seen_numbers.setdefault(part, set())
            elif (
                number == 1
                and part == "A"
                and 1 in seen_numbers.get("A", set())
                and "B" not in seen_numbers
            ):
                # A second Q1 without a PART B heading: the reset is the
                # strongest signal available for the part boundary.
                part = "B"
                current_part = "B"
                inferred_part = True
                inferred_this_block = True
                seen_numbers.setdefault(part, set())

            block = {
                "paper_id": paper_id,
                "part": part,
                "question_no": number,
                "heading_text": text,
                "heading_bbox": list(entry["bbox"]),
                "heading_page": entry["page"],
                "heading_ocr_variant": ocr_variant,
                "heading_recovered": False,
                "part_inferred": inferred_this_block,
                "lines": [],
            }
            blocks.append(block)
            current = block
            seen_numbers.setdefault(part, set()).add(number)
            continue

        if current is not None:
            current["lines"].append(entry)

    if current_part is None:
        unsure.append(
            {
                "paper_id": paper_id,
                "code": "no_part_heading",
                "detail": "no PART A/PART B heading was detected",
            }
        )
    if inferred_part:
        unsure.append(
            {
                "paper_id": paper_id,
                "code": "part_inferred",
                "detail": "second Q1 treated as PART B because no PART B heading was found",
            }
        )
    return blocks, part_assumed


def _recover_sequence(
    blocks: list[dict[str, Any]],
    paper_id: str,
    unsure: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Insert placeholders for missing question numbers within a part."""
    part_order: list[str] = []
    grouped: dict[str, list[dict[str, Any]]] = OrderedDict()
    for block in blocks:
        part = block["part"]
        if part not in grouped:
            grouped[part] = []
            part_order.append(part)
        grouped[part].append(block)

    output: list[dict[str, Any]] = []
    for part in part_order:
        part_blocks = grouped[part]
        detected = sorted({block["question_no"] for block in part_blocks})
        if not detected:
            output.extend(part_blocks)
            continue
        expected = set(range(1, max(detected) + 1))
        missing = sorted(expected - set(detected))
        if missing:
            if len(missing) > 1:
                unsure.append(
                    {
                        "paper_id": paper_id,
                        "code": "multiple_heading_gaps",
                        "detail": (
                            f"PART {part} is missing question heading(s) "
                            + ", ".join(str(number) for number in missing)
                        ),
                    }
                )
            for number in missing:
                placeholder = {
                    "paper_id": paper_id,
                    "part": part,
                    "question_no": number,
                    "heading_text": "",
                    "heading_bbox": None,
                    "heading_page": None,
                    "heading_ocr_variant": False,
                    "heading_recovered": True,
                    "part_inferred": False,
                    "lines": [],
                }
                unsure.append(
                    {
                        "paper_id": paper_id,
                        "code": "heading_recovered",
                        "detail": (
                            f"QUESTION {number} heading was absent from PART "
                            f"{part}; its text could not be separated "
                            "from the surrounding block"
                        ),
                    }
                )
                # Insert before the first block with a larger number.
                insert_at = len(part_blocks)
                for index, existing in enumerate(part_blocks):
                    if existing["question_no"] > number:
                        insert_at = index
                        break
                part_blocks.insert(insert_at, placeholder)
        # Duplicate numbers are not sequence gaps; they are flagged per
        # question below.  Keep their original reading order.
        output.extend(part_blocks)
    return output


# ---------------------------------------------------------------------------
# question construction
# ---------------------------------------------------------------------------


def _span(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "page": entry["page"],
        "bbox": list(entry["bbox"]),
        "text": entry["text"],
    }


def _detect_subparts(
    body: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[int, int | None]]:
    """Return subpart records and a body-index -> subpart-index map.

    The map is ``None`` for preamble lines before the first subpart.
    """
    starts: list[int] = []
    labels: list[str] = []
    levels: list[int] = []
    for index, entry in enumerate(body):
        if entry["x0"] >= SUBPART_LEFT_MARGIN * entry["width"]:
            continue
        parsed = _parse_subpart(entry["text"])
        if not parsed:
            continue
        label, level = parsed
        starts.append(index)
        labels.append(label)
        levels.append(level)

    if not starts:
        return [], {}

    subparts: list[dict[str, Any]] = []
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(body)
        subparts.append(
            {
                "label": labels[position],
                "level": levels[position],
                "start": start,
                "end": end,
                "is_parent": False,
                "lines": body[start:end],
            }
        )

    # Roman items indented under a preceding letter make that letter a
    # parent/instruction item rather than a mark-bearing sub-question.
    last_letter: dict[str, int] = {}
    last_letter_index: int | None = None
    for index, subpart in enumerate(subparts):
        if subpart["level"] == 1:
            last_letter_index = index
        elif subpart["level"] == 2 and last_letter_index is not None:
            parent = subparts[last_letter_index]
            child = subpart
            child_x = body[child["start"]]["x0"]
            parent_x = body[parent["start"]]["x0"]
            if child_x >= parent_x + 4:
                parent["is_parent"] = True

    mapping: dict[int, int | None] = {}
    for index, subpart in enumerate(subparts):
        for body_index in range(subpart["start"], subpart["end"]):
            mapping[body_index] = index
    for body_index in range(0, starts[0]):
        mapping[body_index] = None
    return subparts, mapping


def _associate_marks(
    body: list[dict[str, Any]],
    marks: list[dict[str, Any]],
    subparts: list[dict[str, Any]],
    body_to_subpart: dict[int, int | None],
) -> tuple[list[dict[str, Any]], bool, list[str]]:
    """Attach mark blocks to the nearest preceding body line.

    Returns ``(mark_records, ambiguous, details)``.  A record has the parsed
    value, the anchoring subpart index (or ``None`` for a question with no
    subparts) and its geometric evidence.
    """
    records: list[dict[str, Any]] = []
    ambiguous = False
    details: list[str] = []

    for mark in marks:
        value = _parse_mark(mark["text"])
        if value is None:  # defensive: only mark candidates reach here
            continue
        anchor_index: int | None = None
        anchor: dict[str, Any] | None = None
        for index, entry in enumerate(body):
            if entry["page"] < mark["page"]:
                anchor_index = index
                anchor = entry
            elif entry["page"] == mark["page"] and entry["y0"] <= mark["y0"]:
                anchor_index = index
                anchor = entry
            elif entry["page"] > mark["page"]:
                break
        distance = None
        if anchor is None:
            ambiguous = True
            details.append(f"mark {value} has no preceding body line")
            subpart_index = None
        else:
            if anchor["page"] == mark["page"]:
                distance = round(mark["y0"] - anchor["y0"], 1)
            subpart_index = body_to_subpart.get(anchor_index)
            if subparts and subpart_index is None:
                ambiguous = True
                details.append(
                    f"mark {value} follows preamble text, not a subpart"
                )
            if distance is not None and distance > MAX_MARK_DISTANCE:
                ambiguous = True
                details.append(
                    f"mark {value} is {distance}pt below its candidate line"
                )
        records.append(
            {
                "value": value,
                "subpart_index": subpart_index,
                "distance": distance,
                "page": mark["page"],
                "bbox": list(mark["bbox"]),
            }
        )
    return records, ambiguous, details


def _mark_partition(records: list[dict[str, Any]]) -> dict[int, int]:
    """Sum mark values per subpart (a subpart may have two blocks)."""
    assigned: dict[int, int] = {}
    for record in records:
        index = record["subpart_index"]
        if index is None:
            continue
        assigned[index] = assigned.get(index, 0) + int(record["value"])
    return assigned


def _leaf_indices(subparts: list[dict[str, Any]], assigned: dict[int, int]) -> list[int]:
    return [
        index
        for index, subpart in enumerate(subparts)
        if not subpart["is_parent"] or index in assigned
    ]


def _group_size(
    subparts: list[dict[str, Any]],
    leaves: list[int],
    previous_mark_leaf: int | None,
    current_index: int,
) -> int:
    if current_index not in leaves:
        return 1
    current_position = leaves.index(current_index)
    if previous_mark_leaf is None:
        return current_position + 1
    try:
        previous_position = leaves.index(previous_mark_leaf)
    except ValueError:
        return 1
    return max(1, current_position - previous_position)


def _build_question(
    block: dict[str, Any],
    source_file: str,
    source_kind: str,
    page_images: set[int] | None,
    asset_records: list[dict[str, Any]] | None,
    questions_used_ids: set[str],
    unsure: list[dict[str, Any]],
) -> dict[str, Any]:
    paper_id = block["paper_id"]
    part = block["part"]
    number = block["question_no"]
    heading_recovered = bool(block["heading_recovered"])

    all_lines = block["lines"]
    body = [entry for entry in all_lines if not entry["is_mark"]]
    mark_lines = [entry for entry in all_lines if entry["is_mark"]]

    review_flags: list[str] = []
    if block["heading_ocr_variant"]:
        _add_flag(review_flags, "ocr_heading_variant")
    if block["part_inferred"]:
        _add_flag(review_flags, "part_inferred")
    if heading_recovered:
        _add_flag(review_flags, "heading_recovered")

    text = "\n".join(entry["text"] for entry in body)
    source_spans = [_span(entry) for entry in body]
    pages = sorted(
        {entry["page"] for entry in body}
        | ({block["heading_page"]} if block["heading_page"] else set())
    )

    subparts, body_to_subpart = _detect_subparts(body)
    if not subparts:
        main_lines = body
        subparts = [
            {
                "label": "main",
                "level": 1,
                "start": 0,
                "end": len(body),
                "is_parent": False,
                "lines": main_lines,
            }
        ]
        body_to_subpart = {index: 0 for index in range(len(body))}

    mark_records, ambiguous, mark_details = _associate_marks(
        body, mark_lines, subparts, body_to_subpart
    )
    assigned = _mark_partition(mark_records)
    leaves = _leaf_indices(subparts, assigned)

    # Walk marks and leaf order to label grouped/explicit subpart marks.
    ordered_records = sorted(
        [record for record in mark_records if record["subpart_index"] is not None],
        key=lambda record: record["subpart_index"],
    )
    subpart_marks_source: dict[int, str] = {}
    covered: set[int] = set()
    previous_leaf: int | None = None
    for record in ordered_records:
        index = record["subpart_index"]
        assert index is not None
        size = _group_size(subparts, leaves, previous_leaf, index)
        if size >= 2:
            covered.update(leaves[: leaves.index(index) + 1])
            subpart_marks_source[index] = "grouped"
            for covered_index in leaves[: leaves.index(index)]:
                subpart_marks_source.setdefault(covered_index, "grouped")
        elif index not in subpart_marks_source:
            subpart_marks_source[index] = "explicit"
        if index in leaves:
            previous_leaf = index

    question_marks = sum(record["value"] for record in mark_records) or None

    marked_leaves = [index for index in leaves if index in assigned]
    accounted = set(assigned) | covered
    uncovered_leaves = [index for index in leaves if index not in accounted]
    if question_marks is None:
        marks_source = "missing"
        _add_flag(review_flags, "missing_marks")
        unsure.append(
            {
                "paper_id": paper_id,
                "question_id": f"{paper_id}-{part}{number}",
                "code": "missing_marks",
                "detail": "no (N marks) block was associated with this question",
            }
        )
    elif ambiguous:
        marks_source = "unsure"
        _add_flag(review_flags, "ambiguous_marks")
        unsure.append(
            {
                "paper_id": paper_id,
                "question_id": f"{paper_id}-{part}{number}",
                "code": "ambiguous_marks",
                "detail": "; ".join(mark_details) or "mark association uncertain",
            }
        )
    elif uncovered_leaves:
        # Some leaves are neither marked nor covered by a grouped block.
        # Do not invent values for them.
        marks_source = "unsure"
        _add_flag(review_flags, "missing_marks")
        unsure.append(
            {
                "paper_id": paper_id,
                "question_id": f"{paper_id}-{part}{number}",
                "code": "missing_marks",
                "detail": "one or more subparts have no mark block",
            }
        )
    elif any(source == "grouped" for source in subpart_marks_source.values()):
        marks_source = "grouped"
    elif marked_leaves or not subparts:
        marks_source = "explicit"
    else:
        marks_source = "missing"

    if marks_source not in MARK_SOURCES:  # defensive
        marks_source = "unsure"

    # ---- subpart payloads -------------------------------------------------
    subpart_payloads: list[dict[str, Any]] = []
    for index, subpart in enumerate(subparts):
        line_texts = [entry["text"] for entry in subpart["lines"]]
        subpart_text = "\n".join(line_texts)
        refs, ref_pages = _figure_refs_with_pages(subpart["lines"])
        sub_ids, _ = _match_assets(
            refs, ref_pages, paper_id, asset_records
        )
        bbox = (
            list(subpart["lines"][0]["bbox"]) if subpart["lines"] else None
        )
        if index in assigned:
            sub_marks = assigned[index]
            sub_source = subpart_marks_source.get(index, "explicit")
        elif index in covered:
            sub_marks = None
            sub_source = "grouped"
        else:
            sub_marks = None
            sub_source = "missing"
        subpart_payloads.append(
            {
                "label": subpart["label"],
                "text": subpart_text,
                "marks": sub_marks,
                "marks_source": sub_source,
                "bbox": bbox,
                "figure_refs": refs,
                "asset_ids": sub_ids,
            }
        )

    # ---- references and assets -------------------------------------------
    refs, ref_pages = _figure_refs_with_pages(body)
    question_pages = set(pages)
    asset_ids, unresolved = _match_assets(
        refs, ref_pages, paper_id, asset_records
    )
    if not refs:
        asset_status = "missing"
    elif not unresolved and asset_ids:
        asset_status = "linked"
    else:
        have_pages = (
            True
            if page_images is None
            else all(page in page_images for page in question_pages)
        )
        asset_status = "page_only" if have_pages else "missing"
    # When an assets manifest exists, an unmatched reference is a real
    # provenance gap and is reported.  Without the manifest we only know that
    # page-level images may exist, so page_only is the honest status.
    if refs and asset_records is not None and unresolved:
        _add_flag(review_flags, "unresolved_reference")
        unsure.append(
            {
                "paper_id": paper_id,
                "question_id": f"{paper_id}-{part}{number}",
                "code": "unresolved_reference",
                "detail": "reference(s) without a matching asset: "
                + ", ".join(unresolved),
            }
        )
    elif refs and asset_status == "missing":
        _add_flag(review_flags, "unresolved_reference")
        unsure.append(
            {
                "paper_id": paper_id,
                "question_id": f"{paper_id}-{part}{number}",
                "code": "unresolved_reference",
                "detail": "reference(s) without an asset or page image: "
                + ", ".join(refs),
            }
        )

    if len(pages) > MAX_QUESTION_PAGES:
        _add_flag(review_flags, "question_spans_many_pages")
        unsure.append(
            {
                "paper_id": paper_id,
                "question_id": f"{paper_id}-{part}{number}",
                "code": "long_question",
                "detail": f"question spans {len(pages)} pages",
            }
        )
    if not body and not heading_recovered:
        _add_flag(review_flags, "empty_question")
        unsure.append(
            {
                "paper_id": paper_id,
                "question_id": f"{paper_id}-{part}{number}",
                "code": "empty_question",
                "detail": "question heading had no body lines",
            }
        )
    if source_kind == "ocr":
        _add_flag(review_flags, "ocr_source")

    # ---- confidence -------------------------------------------------------
    confidence = 0.9 if source_kind == "ocr" else 0.98
    if heading_recovered:
        confidence -= 0.5
    if question_marks is None:
        confidence -= 0.25
    if marks_source == "grouped":
        confidence -= 0.03
    if ambiguous:
        confidence -= 0.2
    if block["heading_ocr_variant"]:
        confidence -= 0.03
    if len(pages) > MAX_QUESTION_PAGES:
        confidence -= 0.15
    if refs and asset_status == "missing":
        confidence -= 0.1
    if not body:
        confidence -= 0.3
    confidence = round(max(0.0, min(1.0, confidence)), 2)

    base_id = f"{paper_id}-{part}{number}"
    question_id = base_id
    suffix = 2
    while question_id in questions_used_ids:
        question_id = f"{base_id}-{suffix}"
        suffix += 1
    questions_used_ids.add(question_id)
    if question_id != base_id:
        _add_flag(review_flags, "duplicate_question_no")
        unsure.append(
            {
                "paper_id": paper_id,
                "question_id": question_id,
                "code": "duplicate_question_no",
                "detail": f"duplicate heading number {part}{number}",
            }
        )

    return {
        "question_id": question_id,
        "paper_id": paper_id,
        "source_file": source_file,
        "part": part,
        "question_no": number,
        "slot": f"{part}{number}",
        "text": text,
        "text_sha256": _sha256(text),
        "marks": question_marks,
        "marks_source": marks_source,
        "pages": pages,
        "subparts": subpart_payloads,
        "figure_refs": refs,
        "asset_ids": asset_ids,
        "asset_status": asset_status,
        "confidence": confidence,
        "review_flags": review_flags,
        "source_spans": source_spans,
        "heading_bbox": block["heading_bbox"],
        "heading_recovered": heading_recovered,
        "_unresolved_refs": len(unresolved),
    }


# ---------------------------------------------------------------------------
# paper-level orchestration
# ---------------------------------------------------------------------------


def _paper_record(
    paper_id: str,
    source_file: str,
    source_kind: str,
    page_count: int,
    questions: list[dict[str, Any]],
    unsure_before: int,
    unsure_after: int,
    status: str = "ok",
) -> dict[str, Any]:
    by_part = Counter(question["part"] for question in questions)
    return {
        "paper_id": paper_id,
        "source_file": source_file,
        "source_kind": source_kind,
        "pages": page_count,
        "question_count": len(questions),
        "by_part": dict(sorted(by_part.items())),
        "with_marks": sum(1 for q in questions if q["marks"] is not None),
        "missing_marks": sum(1 for q in questions if q["marks"] is None),
        "with_assets": sum(1 for q in questions if q["asset_ids"]),
        "figure_refs": sum(len(q["figure_refs"]) for q in questions),
        "unsure": max(0, unsure_after - unsure_before),
        "status": status,
    }


def build_question_bank(
    tracking_dir: Path | str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Build the draft bank and write it under ``tracking_dir``.

    ``tracking_dir`` defaults to ``data/tracking/csc429``.  The function is
    deterministic and performs no network or model calls.  A full rebuild is
    cheap, so ``force`` is accepted for CLI compatibility but the draft is
    always regenerated from the current layout files.
    """
    tracking = Path(tracking_dir) if tracking_dir is not None else TRACKING
    layout_dir = tracking / "layout"
    unsure: list[dict[str, Any]] = []
    papers: list[dict[str, Any]] = []
    questions: list[dict[str, Any]] = []
    questions_used_ids: set[str] = set()

    duplicate_sources = _duplicate_sources(tracking)
    asset_records = _asset_records(tracking)
    layout_sources: set[str] = set()
    layout_ids: set[str] = set()

    layout_paths = sorted(layout_dir.glob("*.json")) if layout_dir.exists() else []

    for layout_path in layout_paths:
        try:
            layout = _load_json(layout_path)
        except (OSError, ValueError) as exc:
            unsure.append(
                {
                    "paper_id": layout_path.stem,
                    "code": "bad_layout_json",
                    "detail": f"could not read layout: {exc}",
                }
            )
            continue
        if not isinstance(layout, dict):
            unsure.append(
                {
                    "paper_id": layout_path.stem,
                    "code": "bad_layout_json",
                    "detail": "layout root is not an object",
                }
            )
            continue

        paper_id = str(layout.get("paper_id") or layout_path.stem)
        source_file = str(layout.get("paper") or "")
        if source_file and source_file in duplicate_sources:
            continue
        layout_sources.add(source_file)
        layout_ids.add(paper_id)
        source_kind = str(layout.get("source_kind") or "")
        page_count = len(layout.get("pages", []) or [])
        unsure_start = len(unsure)

        try:
            entries, _missing = _layout_entries(layout, paper_id, unsure)
            if not entries:
                raise ValueError("layout contains no usable lines")
            blocks, _part_assumed = _build_blocks(entries, paper_id, unsure)
            if not blocks:
                unsure.append(
                    {
                        "paper_id": paper_id,
                        "code": "no_questions_found",
                        "detail": "no QUESTION heading matched in the layout",
                    }
                )
                papers.append(
                    _paper_record(
                        paper_id,
                        source_file,
                        source_kind,
                        page_count,
                        [],
                        unsure_start,
                        len(unsure),
                        status="no_questions",
                    )
                )
                continue
            blocks = _recover_sequence(blocks, paper_id, unsure)
            page_images = _page_image_pages(tracking, paper_id)
            paper_questions: list[dict[str, Any]] = []
            for block in blocks:
                question = _build_question(
                    block,
                    source_file,
                    source_kind,
                    page_images,
                    asset_records,
                    questions_used_ids,
                    unsure,
                )
                paper_questions.append(question)
                questions.append(question)
            papers.append(
                _paper_record(
                    paper_id,
                    source_file,
                    source_kind,
                    page_count,
                    paper_questions,
                    unsure_start,
                    len(unsure),
                )
            )
        except Exception as exc:  # noqa: BLE001 - one bad paper must not abort
            unsure.append(
                {
                    "paper_id": paper_id,
                    "code": "paper_failed",
                    "detail": f"{type(exc).__name__}: {exc}",
                }
            )
            papers.append(
                _paper_record(
                    paper_id,
                    source_file,
                    source_kind,
                    page_count,
                    [],
                    unsure_start,
                    len(unsure),
                    status="failed",
                )
            )

    # Registered unique papers without a layout are still reported, with an
    # explicit unsure entry, rather than being silently dropped.
    for record in _register_records(tracking):
        source = str(record.get("source", ""))
        if not source or record.get("duplicate_of"):
            continue
        if source in layout_sources:
            continue
        paper_id = _register_paper_id(record)
        if paper_id in layout_ids:
            continue
        unsure_start = len(unsure)
        unsure.append(
            {
                "paper_id": paper_id,
                "code": "no_layout_coordinates",
                "detail": f"no layout JSON found for {source}",
            }
        )
        papers.append(
            _paper_record(
                paper_id,
                source,
                str(record.get("source_kind") or ""),
                0,
                [],
                unsure_start,
                len(unsure),
                status="no_layout",
            )
        )

    papers.sort(key=lambda row: row["paper_id"])
    questions.sort(
        key=lambda row: (
            row["paper_id"],
            row["part"],
            row["question_no"],
            row["question_id"],
        )
    )

    summary = _summary(papers, questions, unsure)
    for question in questions:
        question.pop("_unresolved_refs", None)
    bank = {
        "schema_version": SCHEMA_VERSION,
        "subject": SUBJECT,
        "generated_by": "src.subjects.csc429.questions",
        "llm_used": False,
        "cost_usd": 0,
        "papers": papers,
        "questions": questions,
        "summary": summary,
        "unsure": unsure,
    }
    _validate(bank)

    output = tracking / OUTPUT_NAME
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(bank, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return bank


def _summary(
    papers: list[dict[str, Any]],
    questions: list[dict[str, Any]],
    unsure: list[dict[str, Any]],
) -> dict[str, Any]:
    by_part = Counter(question["part"] for question in questions)
    figure_questions = sum(1 for q in questions if q["figure_refs"])
    return {
        "papers": len(papers),
        "questions": len(questions),
        "by_part": dict(sorted(by_part.items())),
        "with_marks": sum(1 for q in questions if q["marks"] is not None),
        "with_assets": sum(1 for q in questions if q["asset_ids"]),
        "missing_marks": sum(1 for q in questions if q["marks"] is None),
        "unresolved_refs": sum(
            int(q.get("_unresolved_refs", 0)) for q in questions
        ),
        "figure_table_questions": figure_questions,
        "figure_refs": sum(len(q["figure_refs"]) for q in questions),
        "heading_recovered": sum(
            1 for q in questions if q["heading_recovered"]
        ),
        "unsure": len(unsure),
        "subparts": sum(len(q["subparts"]) for q in questions),
    }


def _validate(bank: dict[str, Any]) -> None:
    """Cheap structural checks; raises on internal inconsistency."""
    for question in bank["questions"]:
        normalised_text = _norm_ws(question["text"])
        normalised_spans = _norm_ws(
            " ".join(span["text"] for span in question["source_spans"])
        )
        if normalised_text != normalised_spans:
            raise AssertionError(
                f"text/span mismatch for {question['question_id']}"
            )
        if question["marks_source"] not in MARK_SOURCES:
            raise AssertionError(
                f"bad marks_source for {question['question_id']}"
            )
        if question["text_sha256"] != _sha256(question["text"]):
            raise AssertionError(
                f"bad text hash for {question['question_id']}"
            )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build the CSC429 draft question bank from layout JSON"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="rebuild even if a draft already exists (always rebuilds today)",
    )
    parser.add_argument(
        "--tracking",
        type=Path,
        default=None,
        help="override data/tracking/csc429 (used by tests)",
    )
    args = parser.parse_args(argv)

    bank = build_question_bank(tracking_dir=args.tracking, force=args.force)
    summary = bank["summary"]
    output = (args.tracking or TRACKING) / OUTPUT_NAME
    print(f"wrote {output}")
    print(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
