"""Build three CSC429 pilot seeds from the real question bank.

Presentation rules for this refinement:

* a figure is captured from the original page;
* a table is recreated as a native Word table from the layout layer;
* a figure region that is mostly prose is recreated as native text;
* captions are never captured into an asset or printed as a separate block;
* every lettered/roman sub-part starts a new paragraph (a visible ``¶``).

Questions are still real past-paper questions, shuffled across source papers,
and no question text or diagram is invented.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import shutil
from pathlib import Path
from statistics import median

import docx
from PIL import Image
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from src import config
from src.assemble.pdf_export import export_pdf
from src.subjects.csc429.tables import (
    extract_table,
    figure_question_assets,
    table_question_assets,
)

SUBJECT = "CSC429"
TRACKING = config.TRACKING_DIR / "csc429"
BANK = TRACKING / "question_bank_draft.json"
ASSETS = TRACKING / "assets" / "manifest.json"
LAYOUT = TRACKING / "layout"
TEMPLATE = (config.subject_reference_dir(SUBJECT)
            / "CSC429 TEMPLATE.docx")
OUT_ROOT = config.PROJECT_ROOT / "outputs" / "pilot" / SUBJECT
PART_A_MARKS = [5, 5, 5, 5, 10, 10, 10, 10, 10, 10]

SUBPART_START = re.compile(
    r"^(?:\(?[a-hA-H]\)|\(?(?:i{1,3}|iv|v|vi|vii)\))\s*")
CAPTION_RE = re.compile(
    r"^\s*(?:Figure|Fig\.?|Table)\s*\d+[A-Za-z]?\s*[:.\-–]?", re.I)
REF_RE = re.compile(r"\b(Figure|Table)\s*(\d+)", re.I)
PROMPT_MARK_RE = re.compile(
    r"^(?:QUESTION\s+\d|Question\s+\d|"
    r"\(?[a-hA-H]\)|\(?(?:i{1,3}|iv|v|vi|vii)\))", re.I)
LABEL_ONLY_RE = re.compile(
    r"^\(?(?:[a-hA-H]|i{1,3}|iv|v|vi|vii)\)$")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _asset_index(manifest: dict) -> dict[str, dict]:
    return {row["asset_id"]: row for row in manifest.get("assets", [])}


def _layout_index() -> dict[str, dict]:
    return {path.stem: _load(path) for path in sorted(LAYOUT.glob("*.json"))}


def _layout_page(layouts: dict[str, dict], asset: dict) -> dict | None:
    paper = layouts.get(asset.get("paper_id", ""))
    if not paper:
        return None
    for page in paper.get("pages", []):
        if int(page.get("page", 0)) == int(asset.get("page", 0)):
            return page
    return None


def _span_in_box(span: dict, box: list[float]) -> bool:
    x0, y0, x1, y1 = span.get("bbox", [0, 0, 0, 0])
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if box[0] <= cx <= box[2] and box[1] <= cy <= box[3]:
        return True
    area = max(1.0, (x1 - x0) * (y1 - y0))
    ox = max(0.0, min(x1, box[2]) - max(x0, box[0]))
    oy = max(0.0, min(y1, box[3]) - max(y0, box[1]))
    return ox * oy / area > 0.6


def _box(asset: dict) -> list[float]:
    return list(asset.get("content_bbox") or asset.get("bbox_pdf") or [0, 0, 0, 0])


def _question_span_boxes(question: dict) -> list[tuple[int, list[float]]]:
    return [(int(span.get("page", 0)), list(span.get("bbox", [0, 0, 0, 0])))
            for span in question.get("source_spans") or []]


def _is_question_span(line: dict, page: int,
                      spans: list[tuple[int, list[float]]]) -> bool:
    bbox = list(line.get("bbox", [0, 0, 0, 0]))
    for span_page, span_bbox in spans:
        if span_page != page:
            continue
        # Same physical line as a question source span.
        if _span_in_box({"bbox": bbox}, span_bbox):
            return True
    return False


def _primary_refs(question: dict) -> set[str]:
    """References in the opening preamble; later typo references are ignored."""
    refs: set[str] = set()
    previous = None
    for span in question.get("source_spans") or []:
        text = " ".join(str(span.get("text", "")).split())
        bbox = list(span.get("bbox", [0, 0, 0, 0]))
        if previous is not None:
            same_page = int(span.get("page", 0)) == previous[0]
            gap = bbox[1] - previous[1]
            if not same_page or gap > 20:
                break
        found = REF_RE.findall(text)
        if found:
            refs.update(f"{kind.title()} {int(number)}"
                        for kind, number in found)
        if SUBPART_START.match(text):
            break
        previous = (int(span.get("page", 0)), bbox[3])
    if not refs:
        refs = set(question.get("figure_refs") or [])
    return refs


def _asset_area(asset: dict) -> float:
    box = _box(asset)
    return max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1])


def _question_assets(question: dict, assets: dict[str, dict]) -> list[dict]:
    """Keep referenced assets and only the largest crop per label."""
    refs = _primary_refs(question)
    candidates = [
        assets[asset_id] for asset_id in question.get("asset_ids", [])
        if asset_id in assets
        and (not refs or str(assets[asset_id].get("label", "")) in refs)
    ]
    if not candidates:
        candidates = [assets[asset_id] for asset_id in question.get("asset_ids", [])
                      if asset_id in assets]
    rank = {"high": 3, "medium": 2, "low": 1}
    best: dict[tuple[str, str], dict] = {}
    for asset in candidates:
        key = (str(asset.get("kind", "")), str(asset.get("label", "")))
        current = best.get(key)
        if current is None:
            best[key] = asset
            continue
        asset_score = (rank.get(str(asset.get("confidence")), 0),
                       _asset_area(asset))
        current_score = (rank.get(str(current.get("confidence")), 0),
                         _asset_area(current))
        if asset_score > current_score:
            best[key] = asset
    return sorted(best.values(), key=lambda row: (
        int(row.get("page", 0)), float(_box(row)[1]), str(row.get("label", ""))))


def _expanded_lines(asset: dict, page: dict | None) -> list[dict]:
    """Lines in the asset's vertical band across the usable page width."""
    if not page:
        return []
    box = _box(asset)
    page_width = float(page.get("width", 600))
    left, right = 0.03 * page_width, 0.97 * page_width
    label = str(asset.get("label", ""))
    lines = []
    for line in page.get("lines", []):
        x0, y0, x1, y1 = list(line.get("bbox", [0, 0, 0, 0]))
        cy = (y0 + y1) / 2
        if not (box[1] - 2 <= cy <= box[3] + 2):
            continue
        if x1 < left or x0 > right:
            continue
        text = " ".join(str(line.get("text", "")).split())
        if not text or CAPTION_RE.match(text):
            continue
        if label and text.lower().startswith(label.lower()):
            continue
        lines.append({"text": text, "bbox": [float(x0), float(y0),
                                             float(x1), float(y1)]})
    lines.sort(key=lambda item: (item["bbox"][1], item["bbox"][0]))
    return lines


def _mixed_start(lines: list[dict], fallback: float) -> float:
    """Return the first line after a prompt block separated by a wide gap."""
    if len(lines) < 2:
        return fallback
    markers = [bool(PROMPT_MARK_RE.match(line["text"])) for line in lines]
    for index in range(len(lines) - 1):
        gap = lines[index + 1]["bbox"][1] - lines[index]["bbox"][3]
        if gap > 20 and any(markers[: index + 1]):
            return lines[index + 1]["bbox"][1]
    return fallback


def _asset_text_lines(asset: dict, page: dict | None, question: dict,
                      *, expand: bool = False) -> list[dict]:
    """Return source lines inside an asset, excluding captions/labels."""
    if not page:
        return []
    lines = _expanded_lines(asset, page) if expand else []
    if not expand:
        box = _box(asset)
        label = str(asset.get("label", ""))
        for line in page.get("lines", []):
            bbox = list(line.get("bbox", [0, 0, 0, 0]))
            if not _span_in_box({"bbox": bbox}, box):
                continue
            text = " ".join(str(line.get("text", "")).split())
            if not text or CAPTION_RE.match(text):
                continue
            if label and text.lower().startswith(label.lower()):
                continue
            lines.append({"text": text, "bbox": bbox})
        lines.sort(key=lambda item: (item["bbox"][1], item["bbox"][0]))
    return lines


def _is_mixed_asset(asset: dict, page: dict | None, question: dict) -> bool:
    box = _box(asset)
    if box[3] - box[1] < 40 or not page:
        return False
    label = str(asset.get("label", ""))
    lines = []
    for line in page.get("lines", []):
        x0, y0, x1, y1 = list(line.get("bbox", [0, 0, 0, 0]))
        if not (box[1] - 2 <= (y0 + y1) / 2 <= box[3] + 2):
            continue
        text = " ".join(str(line.get("text", "")).split())
        if not text or CAPTION_RE.match(text):
            continue
        if label and text.lower().startswith(label.lower()):
            continue
        width = max(1.0, x1 - x0)
        overlap = max(0.0, min(x1, box[2]) - max(x0, box[0]))
        if overlap / width >= 0.40:
            lines.append({"text": text, "bbox": [x0, y0, x1, y1]})
    lines.sort(key=lambda item: (item["bbox"][1], item["bbox"][0]))
    start = _mixed_start(lines, box[1])
    lines = [line for line in lines if line["bbox"][1] >= start - 1]
    prose = [
        line for line in lines
        if len(line["text"]) >= 30 and len(line["text"].split()) >= 4
    ]
    flags = " ".join(asset.get("review_flags", []))
    return (len(prose) >= 2
            or sum(len(line["text"]) for line in prose) >= 120
            or (bool(prose) and "prose_column" in flags))


def _mixed_lines(asset: dict, page: dict | None) -> list[dict]:
    box = _box(asset)
    lines = _asset_text_lines(asset, page, {}, expand=True)
    start = _mixed_start(lines, box[1])
    return [
        line for line in lines
        if line["bbox"][1] >= start - 1
        and not SUBPART_START.match(line["text"])
        and not re.match(r"^(?:QUESTION|Question|Figure|Table)\b",
                         line["text"], re.I)
        and len(line["text"]) >= 8
    ]


def _presentation_box(asset: dict, page: dict | None,
                      question: dict) -> list[float] | None:
    """Trim a question prompt that the crop accidentally included above a figure."""
    box = _box(asset)
    if not page:
        return box
    lines = _asset_text_lines(asset, page, question)
    start = _mixed_start(lines, box[1])
    if start > box[1] + 3:
        box = [box[0], start - 2, box[2], box[3]]
    if box[2] - box[0] < 40 or box[3] - box[1] < 15:
        return None
    return [round(value, 2) for value in box]


def _figure_box(asset: dict, page: dict | None,
                question: dict) -> list[float] | None:
    """Return the delivered figure box, widening label-only side columns."""
    box = _presentation_box(asset, page, question)
    if box is None or not page:
        return box
    page_width = float(page.get("width", 600))
    lines = _expanded_lines(asset, page)
    prompts = [
        line for line in lines
        if (PROMPT_MARK_RE.match(line["text"])
            or re.match(r"^Question\s+\d", line["text"], re.I))
        and line["bbox"][3] <= box[1] + 20
    ]
    if prompts:
        box = [box[0], max(box[1], max(line["bbox"][3] for line in prompts) + 4),
               box[2], box[3]]
    if box[2] - box[0] >= 0.60 * page_width:
        return box
    outside = [
        line for line in lines
        if not PROMPT_MARK_RE.match(line["text"])
        and not re.match(r"^Question\s+\d", line["text"], re.I)
        and not (box[0] - 2 <= (line["bbox"][0] + line["bbox"][2]) / 2
                 <= box[2] + 2)
    ]
    if len(outside) >= 2 and all(len(line["text"]) < 30 for line in outside):
        return [round(0.05 * page_width, 2), box[1],
                round(0.95 * page_width, 2), box[3]]
    return box


# ---------------------------------------------------------------------------
# selection
# ---------------------------------------------------------------------------


def _review_blocked(question: dict) -> bool:
    flags = " ".join(question.get("review_flags", []))
    return "ambiguous" in flags or "unresolved" in flags


def _table_ready(question: dict, assets: dict[str, dict],
                 layouts: dict[str, dict]) -> bool:
    selected_tables = [
        asset for asset in _question_assets(question, assets)
        if asset.get("kind") == "table"
    ]
    if not selected_tables:
        return False
    for asset in selected_tables:
        page = _layout_page(layouts, asset)
        if not page:
            return False
        if layouts.get(asset.get("paper_id", ""), {}).get(
                "source_kind") != "text":
            return False
        if extract_table(asset, page) is None:
            return False
    return True


def _refs_covered(question: dict, assets: dict[str, dict]) -> bool:
    refs = _primary_refs(question)
    selected = {str(asset.get("label", ""))
                for asset in _question_assets(question, assets)}
    return all(ref in selected for ref in refs)


def _usable(question: dict, assets: dict[str, dict],
            layouts: dict[str, dict]) -> bool:
    if _review_blocked(question):
        return False
    if question.get("marks") not in {5, 10, 20}:
        return False
    if question.get("figure_refs") and not question.get("asset_ids"):
        return False
    if not _refs_covered(question, assets):
        return False
    if table_question_assets(question, assets):
        return _table_ready(question, assets, layouts)
    return True


def _mixed_ready(question: dict, assets: dict[str, dict],
                 layouts: dict[str, dict]) -> bool:
    for asset in _question_assets(question, assets):
        if asset.get("kind") != "figure":
            continue
        if _is_mixed_asset(asset, _layout_page(layouts, asset), question):
            return True
    return False


def _pick(pool: list[dict], count: int, used_ids: set[str],
          papers: set[str], rng: random.Random,
          *, prefer_mixed: bool = False) -> list[dict]:
    def eligible(items: list[dict]) -> list[dict]:
        out = [
            question for question in items
            if question["question_id"] not in used_ids
            and question["paper_id"] not in papers
        ]
        rng.shuffle(out)
        return out

    source = eligible(pool)
    ordered: list[dict] = []
    if prefer_mixed:
        mixed = [q for q in source if q.get("_mixed")]
        ordered.extend(mixed[:1])
        ordered.extend(q for q in source if q not in mixed)
    else:
        ordered = source
    chosen: list[dict] = []
    for question in ordered:
        if len(chosen) >= count:
            break
        if question["paper_id"] in papers:
            continue
        chosen.append(question)
        used_ids.add(question["question_id"])
        papers.add(question["paper_id"])
    return chosen


def _mark_question(question: dict, assets: dict[str, dict],
                   layouts: dict[str, dict]) -> dict:
    copy = dict(question)
    copy["_mixed"] = _mixed_ready(copy, assets, layouts)
    return copy


def plan_seed(seed: int, bank: dict, assets: dict[str, dict],
              used_ids: set[str], layouts: dict[str, dict] | None = None,
              *, require_table: bool = True) -> dict:
    layouts = layouts or {}
    rng = random.Random(seed)
    questions = [
        _mark_question(question, assets, layouts)
        for question in bank["questions"]
        if _usable(question, assets, layouts)
    ]
    part_a = [q for q in questions if q["part"] == "A"]
    part_b = [q for q in questions if q["part"] == "B" and q["marks"] == 20]
    five = [q for q in part_a if q["marks"] == 5]
    ten = [q for q in part_a if q["marks"] == 10]
    figure_five = [q for q in five if figure_question_assets(q, assets)]
    figure_ten = [q for q in ten if figure_question_assets(q, assets)]
    table_b = [q for q in part_b if table_question_assets(q, assets)]

    papers: set[str] = set()
    selected_five = _pick(figure_five, 2, used_ids, papers, rng,
                          prefer_mixed=True)
    selected_ten = _pick(figure_ten, 2, used_ids, papers, rng,
                         prefer_mixed=True)
    if require_table:
        selected_b = _pick(table_b, 1, used_ids, papers, rng)
        if not selected_b:
            selected_b = _pick(part_b, 1, used_ids, papers, rng)
    else:
        selected_b = _pick(part_b, 1, used_ids, papers, rng)
    plain_five_pool = [
        q for q in five if not figure_question_assets(q, assets)]
    plain_ten_pool = [
        q for q in ten if not figure_question_assets(q, assets)]
    plain_five = _pick(
        plain_five_pool, 4 - len(selected_five), used_ids, papers, rng)
    plain_ten = _pick(
        plain_ten_pool, 6 - len(selected_ten), used_ids, papers, rng)
    if (len(selected_five) + len(plain_five) != 4
            or len(selected_ten) + len(plain_ten) != 6
            or len(selected_b) != 1):
        raise RuntimeError(f"seed {seed}: not enough eligible real questions")

    rng.shuffle(selected_five)
    rng.shuffle(selected_ten)
    rng.shuffle(plain_five)
    rng.shuffle(plain_ten)
    slots = []
    for index, question in enumerate(selected_five + plain_five, start=1):
        slots.append({"slot": f"A{index}", "marks": 5,
                      "question": question})
    for offset, question in enumerate(selected_ten + plain_ten, start=5):
        slots.append({"slot": f"A{offset}", "marks": 10,
                      "question": question})
    slots.append({"slot": "B1", "marks": 20, "question": selected_b[0]})

    payload = []
    for slot in slots:
        question = slot["question"]
        selected_assets = _question_assets(question, assets)
        content = build_content(question, assets, layouts)
        payload.append({
            "slot": slot["slot"],
            "marks": slot["marks"],
            "question_id": question["question_id"],
            "paper_id": question["paper_id"],
            "source_file": question.get("source_file", ""),
            "topic": question.get("topic", ""),
            "diagram": bool(selected_assets),
            "asset_ids": [asset["asset_id"] for asset in selected_assets],
            "figure_refs": question.get("figure_refs", []),
            "content": content,
        })
    return {
        "seed": seed,
        "source": "real_past_paper_bank",
        "diagram_policy": "figure_capture_table_recreate_mixed_text_recreate",
        "slots": payload,
        "summary": {
            "questions": len(payload),
            "total_marks": sum(row["marks"] for row in payload),
            "diagram_questions": sum(1 for row in payload if row["diagram"]),
            "table_questions": sum(
                1 for row in payload
                if any(block["type"] == "table" for block in row["content"])),
            "mixed_questions": sum(
                1 for row in payload
                if any(block["type"] == "mixed" for block in row["content"])),
            "unique_source_papers": len({row["paper_id"] for row in payload}),
        },
    }


# ---------------------------------------------------------------------------
# content blocks
# ---------------------------------------------------------------------------


def _clean_spans(question: dict, boxes: list[tuple[int, list[float]]],
                 labels: list[tuple[int, str]]) -> list[dict]:
    """Question lines outside the selected assets/captions, in source order."""
    spans = question.get("source_spans") or []
    if not spans:
        return []
    keep = []
    prompt_floor: float | None = None
    for span in spans:
        text = " ".join(str(span.get("text", "")).split())
        if not text:
            continue
        page = int(span.get("page", 0))
        sx0, sy0, sx1, sy1 = span.get("bbox", [0, 0, 0, 0])
        is_subpart = bool(SUBPART_START.match(text))
        is_letter = bool(re.match(r"^\(?[a-hA-H]\)", text))
        if any(label and text.startswith(label)
               for asset_page, label in labels if asset_page == page):
            continue
        in_asset = any(
            asset_page == page and _span_in_box(span, box)
            for asset_page, box in boxes)
        if in_asset:
            if is_subpart and is_letter:
                keep.append({
                    "page": page,
                    "bbox": [float(sx0), float(sy0), float(sx1), float(sy1)],
                    "text": text,
                })
                prompt_floor = float(sy1)
                continue
            if prompt_floor is not None and sy0 <= prompt_floor + 18:
                keep.append({
                    "page": page,
                    "bbox": [float(sx0), float(sy0), float(sx1), float(sy1)],
                    "text": text,
                })
                prompt_floor = float(sy1)
                continue
            continue
        keep.append({
            "page": page,
            "bbox": [float(sx0), float(sy0), float(sx1), float(sy1)],
            "text": text,
        })
        if not is_subpart and prompt_floor is not None and sy0 > prompt_floor + 18:
            prompt_floor = None
    return keep


def _group_paragraphs(spans: list[dict]) -> list[dict]:
    spans = sorted(spans, key=lambda span: (
        int(span["page"]), round(float(span["bbox"][1]) / 5),
        float(span["bbox"][0]), float(span["bbox"][1])))
    paragraphs: list[dict] = []
    current: list[dict] = []

    def flush() -> None:
        if not current:
            return
        text = " ".join(span["text"] for span in current).strip()
        if text:
            paragraphs.append({
                "type": "text",
                "page": current[0]["page"],
                "y": current[0]["bbox"][1],
                "text": text,
            })
        current.clear()

    previous = None
    pending_label = False
    for span in spans:
        new_paragraph = False
        if previous is not None:
            if span["page"] != previous["page"]:
                new_paragraph = True
            elif SUBPART_START.match(span["text"]):
                new_paragraph = True
            elif pending_label:
                new_paragraph = False
            else:
                gap = span["bbox"][1] - previous["bbox"][3]
                heights = [previous["bbox"][3] - previous["bbox"][1],
                           span["bbox"][3] - span["bbox"][1]]
                if gap > 1.6 * max(1.0, median(heights)):
                    new_paragraph = True
        if new_paragraph:
            flush()
        current.append(span)
        pending_label = bool(LABEL_ONLY_RE.match(span["text"]))
        previous = span
    flush()
    return paragraphs


def _asset_block(asset: dict, question: dict,
                 layouts: dict[str, dict], *, mixed: bool) -> dict | None:
    page = _layout_page(layouts, asset)
    if asset.get("kind") == "table":
        table = extract_table(asset, page) if page else None
        if table is None:
            return None
        return {
            "type": "table",
            "page": int(asset.get("page", 0)),
            "y": float(_box(asset)[1]),
            "asset_id": asset["asset_id"],
            "table": table,
            "caption": asset.get("caption", ""),
        }
    if mixed:
        lines = _mixed_lines(asset, page)
        if not lines:
            return None
        return {
            "type": "mixed",
            "page": int(asset.get("page", 0)),
            "y": min(float(line["bbox"][1]) for line in lines),
            "asset_id": asset["asset_id"],
            "lines": [line["text"] for line in lines],
            "caption": asset.get("caption", ""),
        }
    box = _figure_box(asset, page, question)
    if box is None:
        return None
    return {
        "type": "figure",
        "page": int(asset.get("page", 0)),
        "y": float(box[1]),
        "asset_id": asset["asset_id"],
        "path": asset["path"],
        "crop_box": box,
        "page_image": asset.get("page_image", ""),
        "page_points": asset.get("page_points", []),
        "width_px": asset.get("width_px", 0),
        "height_px": asset.get("height_px", 0),
        "caption": asset.get("caption", ""),
        "display_width_cm": asset.get("display_width_cm"),
    }


def build_content(question: dict, assets: dict[str, dict],
                  layouts: dict[str, dict]) -> list[dict]:
    selected = _question_assets(question, assets)
    boxes: list[tuple[int, list[float]]] = []
    labels: list[tuple[int, str]] = []
    mixed_ids: set[str] = set()
    for asset in selected:
        page = _layout_page(layouts, asset)
        box = _box(asset)
        labels.append((int(asset.get("page", 0)), str(asset.get("label", ""))))
        if asset.get("kind") == "figure" and _is_mixed_asset(asset, page, question):
            mixed_ids.add(asset["asset_id"])
            lines = _asset_text_lines(asset, page, question, expand=True)
            start = _mixed_start(lines, box[1])
            page_width = float(page.get("width", 600)) if page else 600.0
            box = [0.03 * page_width, start, 0.97 * page_width, box[3]]
        elif asset.get("kind") == "figure":
            presented = _figure_box(asset, page, question)
            if presented is not None:
                box = presented
        elif asset.get("kind") == "table":
            caption = asset.get("caption_bbox")
            top = min(box[1], float(caption[1])) if caption else box[1]
            box = [box[0], top, box[2], box[3]]
        boxes.append((int(asset.get("page", 0)), box))
        caption_box = asset.get("caption_bbox")
        if caption_box:
            boxes.append((int(asset.get("page", 0)),
                          [float(value) for value in caption_box]))
    blocks = _group_paragraphs(_clean_spans(question, boxes, labels))
    for asset in selected:
        block = _asset_block(
            asset, question, layouts,
            mixed=asset["asset_id"] in mixed_ids)
        if block is not None:
            blocks.append(block)
    order = {"text": 0, "figure": 1, "mixed": 1, "table": 1}
    blocks.sort(key=lambda item: (
        int(item.get("page", 0)), float(item.get("y", 0.0)),
        order.get(item["type"], 9)))
    return blocks


LETTER_LABEL_RE = re.compile(r"^([a-h])\)\s*(.*)$", re.I)
ROMAN_LABEL_RE = re.compile(
    r"^(i{1,3}|iv|v|vi|vii)\)\s*(.*)$", re.I)
ROMAN_VALUES = {
    "i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7,
}


def _new_numbering(document, number_format: str) -> int:
    """Append a fresh single-level numbering definition to the document."""
    root = document.part.numbering_part.element
    abstract_ids = [
        int(element.get(qn("w:abstractNumId")))
        for element in root.findall(qn("w:abstractNum"))
    ]
    num_ids = [
        int(element.get(qn("w:numId")))
        for element in root.findall(qn("w:num"))
    ]
    abstract_id = max(abstract_ids, default=0) + 1
    num_id = max(num_ids, default=0) + 1

    abstract = OxmlElement("w:abstractNum")
    abstract.set(qn("w:abstractNumId"), str(abstract_id))
    level_type = OxmlElement("w:multiLevelType")
    level_type.set(qn("w:val"), "hybridMultilevel")
    abstract.append(level_type)
    level = OxmlElement("w:lvl")
    level.set(qn("w:ilvl"), "0")
    start = OxmlElement("w:start")
    start.set(qn("w:val"), "1")
    level.append(start)
    fmt = OxmlElement("w:numFmt")
    fmt.set(qn("w:val"), number_format)
    level.append(fmt)
    text = OxmlElement("w:lvlText")
    text.set(qn("w:val"), "%1)" if number_format == "lowerLetter" else "%1.")
    level.append(text)
    alignment = OxmlElement("w:lvlJc")
    alignment.set(qn("w:val"), "left" if number_format == "lowerLetter"
                  else "right")
    level.append(alignment)
    paragraph_properties = OxmlElement("w:pPr")
    indent = OxmlElement("w:ind")
    indent.set(qn("w:left"), "720" if number_format == "lowerLetter" else "1080")
    indent.set(qn("w:hanging"), "360")
    paragraph_properties.append(indent)
    level.append(paragraph_properties)
    abstract.append(level)

    first_num = root.find(qn("w:num"))
    if first_num is None:
        root.append(abstract)
    else:
        first_num.addprevious(abstract)
    num = OxmlElement("w:num")
    num.set(qn("w:numId"), str(num_id))
    abstract_ref = OxmlElement("w:abstractNumId")
    abstract_ref.set(qn("w:val"), str(abstract_id))
    num.append(abstract_ref)
    root.append(num)
    return num_id


class _QuestionNumbering:
    """Per-question letter/roman list state, restarting each sequence."""

    def __init__(self, document):
        self.document = document
        self.letter_num_id: int | None = None
        self.letter_last: int | None = None
        self.roman_num_id: int | None = None
        self.roman_last: int | None = None

    def letter(self, label: str) -> int:
        value = ord(label.lower()) - ord("a") + 1
        if (self.letter_num_id is None
                or (value == 1 and self.letter_last is not None)
                or (self.letter_last is not None
                    and value != self.letter_last + 1)):
            self.letter_num_id = _new_numbering(self.document, "lowerLetter")
            self.letter_last = None
        self.letter_last = value
        return self.letter_num_id

    def roman(self, label: str) -> int:
        value = ROMAN_VALUES[label.lower()]
        if (self.roman_num_id is None
                or (value == 1 and self.roman_last is not None)
                or (self.roman_last is not None
                    and value != self.roman_last + 1)):
            self.roman_num_id = _new_numbering(self.document, "lowerRoman")
            self.roman_last = None
        self.roman_last = value
        return self.roman_num_id


def _apply_numbering(paragraph, num_id: int) -> None:
    paragraph.style = paragraph.part.document.styles["List Paragraph"]
    num_pr = paragraph._p.get_or_add_pPr().get_or_add_numPr()
    num_pr.get_or_add_ilvl().val = 0
    num_pr.get_or_add_numId().val = num_id


def _add_numbered_text(document, block: dict, num_id: int,
                       text: str) -> None:
    paragraph = document.add_paragraph()
    _apply_numbering(paragraph, num_id)
    paragraph.paragraph_format.line_spacing = 1.5
    paragraph.paragraph_format.space_before = Pt(6)
    paragraph.paragraph_format.space_after = Pt(4)
    run = paragraph.add_run(_safe_text(text))
    run.font.name = "Arial"
    run.font.size = Pt(11)


# ---------------------------------------------------------------------------
# DOCX rendering
# ---------------------------------------------------------------------------


def _set_paragraph_text(paragraph, text: str) -> None:
    runs = paragraph.runs
    if not runs:
        paragraph.add_run(text)
        return
    runs[0].text = text
    for run in runs[1:]:
        run.text = ""


def _clear_after_section_break(document) -> None:
    cut = None
    for index, paragraph in enumerate(document.paragraphs):
        ppr = paragraph._p.pPr
        if ppr is not None and ppr.find(qn("w:sectPr")) is not None:
            cut = index
            break
    if cut is None:
        raise RuntimeError("template has no section break")
    for paragraph in list(document.paragraphs)[cut + 1:]:
        paragraph._element.getparent().remove(paragraph._element)


def _safe_text(text: str) -> str:
    return "".join(
        char for char in str(text)
        if char in "\n\t" or ord(char) >= 32)


def _shade(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def _set_cell_text(cell, text: str, *, bold: bool = False,
                   size: float = 9.5) -> None:
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.line_spacing = 1.0
    paragraph.paragraph_format.space_before = Pt(1)
    paragraph.paragraph_format.space_after = Pt(1)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run(_safe_text(text))
    run.font.name = "Arial"
    run.font.size = Pt(size)
    if bold:
        run.bold = True


def _set_table_borders(table) -> None:
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "8")
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), "000000")
        borders.append(element)
    tbl_pr.append(borders)


def _add_table(document, table: dict, *, caption: str = "") -> None:
    if caption:
        cap = document.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.paragraph_format.line_spacing = 1.0
        cap.paragraph_format.space_before = Pt(4)
        cap.paragraph_format.space_after = Pt(2)
        cap.paragraph_format.keep_with_next = True
        run = cap.add_run(_safe_text(caption))
        run.font.name = "Arial"
        run.font.size = Pt(9)
        run.italic = True
    rows = table.get("rows", [])
    columns = max(1, int(table.get("columns", 1)))
    if not rows:
        return
    word_table = document.add_table(rows=len(rows), cols=columns)
    _set_table_borders(word_table)
    word_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    word_table.autofit = True
    width = Cm(16.2 / columns)
    for column in word_table.columns:
        column.width = width
    for row_index, row in enumerate(rows):
        cells = row.get("cells", [])
        covered: set[int] = set()
        for index in range(columns):
            if index in covered:
                continue
            cell = word_table.cell(row_index, index)
            if index >= len(cells):
                _set_cell_text(cell, "")
                continue
            item = cells[index]
            text = str(item.get("text", ""))
            span = max(1, int(item.get("colspan", 1)))
            if span > 1 and index + span <= columns:
                merged = cell.merge(word_table.cell(
                    row_index, index + span - 1))
                _set_cell_text(merged, text, bold=row_index == 0)
                covered.update(range(index + 1, index + span))
            else:
                _set_cell_text(cell, text, bold=row_index == 0)
    spacer = document.add_paragraph()
    spacer.paragraph_format.space_after = Pt(2)
    spacer.paragraph_format.line_spacing = 1.0


def _crop_figure(block: dict, out_dir: Path) -> Path | None:
    page_image = block.get("page_image")
    crop_box = block.get("crop_box")
    page_points = block.get("page_points") or []
    if not page_image or not crop_box or len(page_points) != 2:
        path = config.PROJECT_ROOT / block["path"]
        return path if path.is_file() else None
    source_path = config.PROJECT_ROOT / page_image
    if not source_path.is_file():
        return None
    with Image.open(source_path) as source:
        image = source.convert("RGB")
        sx = image.width / float(page_points[0])
        sy = image.height / float(page_points[1])
        left = max(0, int(crop_box[0] * sx))
        top = max(0, int(crop_box[1] * sy))
        right = min(image.width, int(crop_box[2] * sx))
        bottom = min(image.height, int(crop_box[3] * sy))
        if right <= left or bottom <= top:
            return None
        crop = image.crop((left, top, right, bottom))
    target = out_dir / "images" / f"{block['asset_id']}.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    crop.save(target, "PNG", dpi=(200, 200))
    return target


def _add_figure(document, block: dict, out_dir: Path) -> None:
    path = _crop_figure(block, out_dir)
    if path is None or not path.is_file():
        return
    with Image.open(path) as image:
        width_px = float(image.width)
        height_px = float(image.height)
    width_cm = float(block.get("display_width_cm") or 16.2)
    if width_px > 0 and height_px > 0:
        max_height_cm = 12.0
        if width_cm * height_px / width_px > max_height_cm:
            width_cm = max_height_cm * width_px / height_px
    picture = document.add_paragraph()
    picture.alignment = WD_ALIGN_PARAGRAPH.CENTER
    picture.paragraph_format.line_spacing = 1.5
    picture.paragraph_format.space_before = Pt(4)
    picture.paragraph_format.space_after = Pt(2)
    picture.paragraph_format.keep_with_next = True
    picture.add_run().add_picture(str(path), width=Cm(width_cm))
    caption = _safe_text(block.get("caption", "")).strip()
    if caption:
        cap = document.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.paragraph_format.line_spacing = 1.0
        cap.paragraph_format.space_before = Pt(1)
        cap.paragraph_format.space_after = Pt(6)
        run = cap.add_run(caption)
        run.font.name = "Arial"
        run.font.size = Pt(9)
        run.italic = True


def _add_mixed(document, block: dict) -> None:
    lines = [line for line in block.get("lines", []) if line.strip()]
    if not lines:
        return
    table = document.add_table(rows=1, cols=1)
    _set_table_borders(table)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.cell(0, 0)
    _shade(cell, "F2F2F2")
    cell.text = ""
    first = True
    for line in lines:
        paragraph = cell.paragraphs[0] if first else cell.add_paragraph()
        first = False
        paragraph.paragraph_format.line_spacing = 1.15
        paragraph.paragraph_format.space_after = Pt(2)
        run = paragraph.add_run(_safe_text(line))
        run.font.name = "Arial"
        run.font.size = Pt(10)
    spacer = document.add_paragraph()
    spacer.paragraph_format.space_after = Pt(2)
    spacer.paragraph_format.line_spacing = 1.0
    caption = _safe_text(block.get("caption", "")).strip()
    if caption:
        cap = document.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.paragraph_format.line_spacing = 1.0
        cap.paragraph_format.space_after = Pt(6)
        run = cap.add_run(caption)
        run.font.name = "Arial"
        run.font.size = Pt(9)
        run.italic = True


def _add_text(document, block: dict, *, first: bool,
              numbering: _QuestionNumbering) -> None:
    text = block.get("text", "")
    letter = LETTER_LABEL_RE.match(text)
    roman = ROMAN_LABEL_RE.match(text)
    if letter:
        _add_numbered_text(
            document, block, numbering.letter(letter.group(1)),
            letter.group(2).strip())
        return
    if roman:
        _add_numbered_text(
            document, block, numbering.roman(roman.group(1)),
            roman.group(2).strip())
        return
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.line_spacing = 1.5
    paragraph.paragraph_format.space_after = Pt(4)
    run = paragraph.add_run(_safe_text(text))
    run.font.name = "Arial"
    run.font.size = Pt(11)


def _add_question(document, slot: dict, out_dir: Path) -> None:
    content = slot.get("content") or []
    large_figure = False
    for block in content:
        if block.get("type") != "figure":
            continue
        width_px = float(block.get("width_px") or 0)
        height_px = float(block.get("height_px") or 0)
        width_cm = float(block.get("display_width_cm") or 16.2)
        if width_px > 0 and height_px > 0:
            height_cm = width_cm * height_px / width_px
            if height_cm > 9.0:
                large_figure = True
                break
    blank = document.add_paragraph()
    blank.paragraph_format.line_spacing = 1.5
    blank.paragraph_format.space_before = Pt(10)
    blank.paragraph_format.space_after = Pt(2)
    heading = document.add_paragraph()
    heading.paragraph_format.line_spacing = 1.5
    heading.paragraph_format.space_before = Pt(10)
    heading.paragraph_format.space_after = Pt(2)
    heading.paragraph_format.keep_with_next = True
    if large_figure:
        heading.paragraph_format.page_break_before = True
    section = document.sections[-1]
    text_width = (section.page_width - section.left_margin
                  - section.right_margin)
    heading.paragraph_format.tab_stops.add_tab_stop(
        text_width, WD_TAB_ALIGNMENT.RIGHT)
    run = heading.add_run(f"QUESTION {slot['slot']}")
    run.bold = True
    heading.add_run("\t")
    run = heading.add_run(f"({slot['marks']} marks)")
    run.bold = True
    if not content:
        content = [{"type": "text", "text": slot.get("text", "")}]
    numbering = _QuestionNumbering(document)
    for index, block in enumerate(content):
        if block["type"] == "text":
            _add_text(document, block, first=index == 0,
                      numbering=numbering)
        elif block["type"] == "figure":
            _add_figure(document, block, out_dir)
        elif block["type"] == "mixed":
            _add_mixed(document, block)
        elif block["type"] == "table":
            _add_table(document, block["table"], caption=block.get("caption", ""))


def build_docx(plan: dict, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TEMPLATE, target)
    document = docx.Document(str(target))
    document.styles["Normal"].font.name = "Arial"
    document.styles["Normal"].font.size = Pt(11)
    cover, body_section = document.sections[0], document.sections[1]
    body_section.start_type = WD_SECTION.NEW_PAGE
    body_section.left_margin = cover.left_margin
    body_section.right_margin = cover.right_margin
    body_section.top_margin = cover.top_margin
    body_section.bottom_margin = cover.bottom_margin
    _clear_after_section_break(document)
    part_a = [slot for slot in plan["slots"] if slot["slot"].startswith("A")]
    part_b = [slot for slot in plan["slots"] if slot["slot"].startswith("B")]
    part_a_heading = document.add_paragraph()
    part_a_heading.paragraph_format.line_spacing = 1.5
    part_a_heading.add_run("PART A (80 MARKS)").bold = True
    note = document.add_paragraph("Answer ALL questions in this part.")
    note.paragraph_format.line_spacing = 1.5
    note.paragraph_format.space_after = Pt(8)
    for slot in part_a:
        _add_question(document, slot, target.parent)
    document.add_page_break()
    part_b_heading = document.add_paragraph()
    part_b_heading.paragraph_format.line_spacing = 1.5
    part_b_heading.add_run("PART B (20 MARKS)").bold = True
    note = document.add_paragraph("Answer the question in this part.")
    note.paragraph_format.line_spacing = 1.5
    note.paragraph_format.space_after = Pt(8)
    for slot in part_b:
        _add_question(document, slot, target.parent)
    document.save(str(target))


def _patch_page_count(document_path: Path, pages: int) -> None:
    document = docx.Document(str(document_path))
    for paragraph in document.paragraphs:
        if paragraph.text.strip().startswith(
                "This examination paper consists"):
            _set_paragraph_text(
                paragraph,
                f"This examination paper consists of {pages} printed pages.")
            document.save(str(document_path))
            return


def _export_seed_pdf(docx_path: Path, pdf_path: Path) -> tuple[int, Path]:
    """Export to the requested PDF, or a sibling when a viewer locks it."""
    temporary = pdf_path.with_name(f"{pdf_path.stem}.tmp{pdf_path.suffix}")
    pages = export_pdf(docx_path, temporary)
    try:
        pdf_path.unlink(missing_ok=True)
        temporary.replace(pdf_path)
        return pages, pdf_path
    except PermissionError:
        fallback = pdf_path.with_name(
            f"{pdf_path.stem}_revised{pdf_path.suffix}")
        fallback.unlink(missing_ok=True)
        temporary.replace(fallback)
        return pages, fallback


def build_seed(seed: int, bank: dict, assets: dict[str, dict],
               used_ids: set[str], layouts: dict[str, dict]) -> dict:
    plan = plan_seed(seed, bank, assets, used_ids, layouts)
    out = OUT_ROOT / f"seed_{seed:02d}"
    out.mkdir(parents=True, exist_ok=True)
    images_dir = out / "images"
    if images_dir.exists():
        shutil.rmtree(images_dir)
    (out / "paper_revised.pdf").unlink(missing_ok=True)
    (out / "plan.json").write_text(
        json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    docx_path = out / "paper.docx"
    pdf_path = out / "paper.pdf"
    build_docx(plan, docx_path)
    pages, actual_pdf = _export_seed_pdf(docx_path, pdf_path)
    _patch_page_count(docx_path, pages)
    pages, actual_pdf = _export_seed_pdf(docx_path, pdf_path)
    plan["summary"]["pages"] = pages
    plan["summary"]["pdf"] = str(actual_pdf)
    (out / "plan.json").write_text(
        json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "seed": seed,
        "path": str(out),
        "pdf": str(actual_pdf),
        "pages": pages,
        "summary": plan["summary"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", default="1-3")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    bank = _load(BANK)
    assets = _asset_index(_load(ASSETS))
    layouts = _layout_index()
    used_ids: set[str] = set()
    parts = args.seeds.split("-")
    seeds = (range(int(parts[0]), int(parts[1]) + 1) if len(parts) == 2
             else [int(value) for value in args.seeds.split(",")])
    results = []
    for seed in seeds:
        results.append(build_seed(seed, bank, assets, used_ids, layouts))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
