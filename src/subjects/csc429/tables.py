"""Reconstruct CSC429 tables from the layout layer for native Word tables.

The only input is the page layout that Stage 1 already captured.  Text is
copied verbatim from the source lines; this module never invents a cell.  It
clusters line boxes into rows and columns and keeps multi-column header cells
as ``colspan`` records so the builder can merge them in Word.
"""
from __future__ import annotations

import re
from statistics import median
from typing import Any

CAPTION_RE = re.compile(
    r"^\s*(?:Figure|Fig\.?|Table|Rajah|Gambar|Jadual)\s*\d+", re.I)

HEADER_WORDS = re.compile(
    r"\b(?:tag|line|address|mode|value|zero-address|one-address|"
    r"two-address|three-address|machine|instruction|binary|block)\b", re.I)


def _bbox(line: dict[str, Any]) -> tuple[float, float, float, float]:
    x0, y0, x1, y1 = line["bbox"]
    return float(x0), float(y0), float(x1), float(y1)


def _inside(line: dict[str, Any], box: list[float]) -> bool:
    x0, y0, x1, y1 = _bbox(line)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return (box[0] - 2 <= cx <= box[2] + 2
            and box[1] - 2 <= cy <= box[3] + 2)


def _rows(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in sorted(lines, key=lambda item: (_bbox(item)[1], _bbox(item)[0])):
        _x0, y0, _x1, y1 = _bbox(line)
        cy = (y0 + y1) / 2
        for row in rows:
            if abs(cy - row["cy"]) <= 5.0:
                row["lines"].append(line)
                row["cy"] = (row["cy"] * (len(row["lines"]) - 1) + cy) / len(
                    row["lines"])
                break
        else:
            rows.append({"cy": cy, "lines": [line]})
    rows.sort(key=lambda row: row["cy"])
    return rows


def _column_centres(lines: list[dict[str, Any]], left: float,
                    right: float) -> list[float]:
    starts = sorted(_bbox(line)[0] for line in lines)
    if not starts:
        return []
    clusters: list[list[float]] = []
    for value in starts:
        if clusters and value - clusters[-1][-1] <= 24.0:
            clusters[-1].append(value)
        else:
            clusters.append([value])
    centres = [sum(cluster) / len(cluster) for cluster in clusters]
    centres = [value for value in centres if left - 5 <= value <= right + 5]
    return centres if len(centres) > 1 else []


def _assign_columns(line: dict[str, Any], centres: list[float],
                    *, header_row: bool) -> tuple[int, int]:
    """Return ``(first_column, colspan)`` for a line."""
    x0, _y0, x1, _y1 = _bbox(line)
    covered = [index for index, centre in enumerate(centres)
               if x0 - 5 <= centre <= x1 + 5]
    if not covered:
        nearest = min(
            range(len(centres)),
            key=lambda index: abs((x0 + x1) / 2 - centres[index]))
        return nearest, 1
    if header_row and len(covered) > 1:
        return covered[0], covered[-1] - covered[0] + 1
    centre = (x0 + x1) / 2
    nearest = min(range(len(centres)),
                  key=lambda index: abs(centre - centres[index]))
    return nearest, 1


def _normalise(text: str) -> str:
    return " ".join(str(text).split())


def extract_table(asset: dict[str, Any], page: dict[str, Any]) -> dict[str, Any] | None:
    """Return a native-table description or ``None`` when it is unusable.

    The result is deliberately conservative: a table needs at least two rows
    and two columns, and at least 45% of its cells must contain text.
    """
    box = asset.get("content_bbox") or asset.get("bbox_pdf")
    if not box:
        return None
    label = str(asset.get("label", ""))
    lines = []
    for line in page.get("lines", []):
        if not _inside(line, box):
            continue
        text = _normalise(line.get("text", ""))
        if not text or CAPTION_RE.match(text):
            continue
        if label and text.lower().startswith(label.lower()):
            continue
        lines.append(line)
    if len(lines) < 4:
        return None

    row_groups = _rows(lines)
    centres = _column_centres(lines, float(box[0]), float(box[2]))
    if len(row_groups) < 2 or len(centres) < 2:
        return None

    widths = [b - a for a, b in zip(centres, centres[1:])]
    median_width = median(widths) if widths else 1.0

    table_rows: list[dict[str, Any]] = []
    non_empty = 0
    total_cells = 0
    for row_index, row in enumerate(row_groups):
        header_row = row_index <= 1
        cells: list[dict[str, Any]] = [
            {"text": "", "colspan": 1} for _ in centres
        ]
        columns_seen: set[int] = set()
        for line in sorted(row["lines"], key=lambda item: _bbox(item)[0]):
            text = _normalise(line.get("text", ""))
            if not text:
                continue
            x0, _y0, x1, _y1 = _bbox(line)
            width = x1 - x0
            is_header = header_row or bool(HEADER_WORDS.search(text))
            first, span = _assign_columns(line, centres, header_row=is_header)
            if is_header and span == 1 and width > 1.8 * median_width:
                # A wide header may still cover adjacent sub-columns whose
                # starts were not sampled often enough to form a cluster.
                covered = [index for index, centre in enumerate(centres)
                           if x0 - 5 <= centre <= x1 + 5]
                if covered:
                    first = covered[0]
                    span = covered[-1] - covered[0] + 1
            if first in columns_seen:
                # A second line in the same column is a continuation.
                cell = cells[first]
                cell["text"] = _normalise(f"{cell['text']} {text}")
                continue
            columns_seen.add(first)
            cells[first]["text"] = text
            cells[first]["colspan"] = max(1, span)
            if span > 1:
                for index in range(first + 1, min(len(cells), first + span)):
                    columns_seen.add(index)
                    cells[index]["text"] = ""
        if any(cell["text"] for cell in cells):
            table_rows.append({"cells": cells})
            non_empty += sum(1 for cell in cells if cell["text"])
            total_cells += len(cells)

    if len(table_rows) < 2 or total_cells == 0:
        return None
    if non_empty / total_cells < 0.45:
        return None
    return {
        "columns": len(centres),
        "rows": table_rows,
        "non_empty_ratio": round(non_empty / total_cells, 3),
        "source": "layout",
    }


def table_question_assets(question: dict[str, Any], assets: dict[str, dict]) -> list[str]:
    """Return table asset IDs attached to a question."""
    return [
        asset_id for asset_id in question.get("asset_ids", [])
        if assets.get(asset_id, {}).get("kind") == "table"
    ]


def figure_question_assets(question: dict[str, Any], assets: dict[str, dict]) -> list[str]:
    """Return figure asset IDs attached to a question."""
    return [
        asset_id for asset_id in question.get("asset_ids", [])
        if assets.get(asset_id, {}).get("kind") == "figure"
    ]
