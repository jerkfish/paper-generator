"""P2: recreate/compare tables and lock original crops for pictures/figures.

No picture, figure or diagram is ever redrawn.  Tables are the only asset kind
that may become a native Word table, and only when a second OCR pass agrees
with the extracted cell text.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src import config
from src.ingest.ocr import win_ocr
from src.subjects.csc429 import pure_config

TRACKING = config.TRACKING_DIR / "csc429"
BANK = TRACKING / "bank"
ASSETS = BANK / "assets"
COMPARE = BANK / "compare"
REPORT = BANK / "compare_report.json"


def _load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _save(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def _norm(text: str) -> str:
    return " ".join(str(text or "").split())


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", str(text).lower())


def _table_text(table: dict) -> list[str]:
    cells = []
    for row in table.get("rows") or []:
        for cell in row.get("cells") or []:
            value = _norm(cell.get("text", ""))
            if value:
                cells.append(value)
    return cells


def _table_text_flat(table: dict) -> str:
    return " | ".join(_table_text(table))


def _table_score(table: dict, ocr_text: str) -> tuple[float, dict]:
    cells = _table_text(table)
    ocr_norm = _norm(ocr_text).lower()
    ocr_tokens = Counter(_tokens(ocr_text))
    if not cells:
        return 0.0, {"cells": 0, "covered": 0, "token_overlap": 0.0,
                     "sequence": 0.0}
    covered = 0
    for cell in cells:
        value = cell.lower()
        if len(_tokens(value)) <= 1:
            if value and value in ocr_norm:
                covered += 1
            continue
        if value in ocr_norm:
            covered += 1
            continue
        cell_tokens = Counter(_tokens(value))
        overlap = sum(min(count, ocr_tokens[token])
                      for token, count in cell_tokens.items())
        if overlap / max(1, sum(cell_tokens.values())) >= 0.75:
            covered += 1
    coverage = covered / len(cells)
    native_tokens = _tokens(_table_text_flat(table))
    ocr_list = _tokens(ocr_text)
    sequence = SequenceMatcher(
        None, " ".join(native_tokens), " ".join(ocr_list)).ratio()
    return max(coverage, sequence), {
        "cells": len(cells),
        "covered": covered,
        "coverage": round(coverage, 4),
        "sequence": round(sequence, 4),
        "token_overlap": round(
            sum((Counter(native_tokens) & ocr_tokens).values())
            / max(1, len(native_tokens)), 4),
    }


def _font(size: int):
    for name in ("arial.ttf", "Arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _render_table(table: dict, width: int = 900) -> Image.Image:
    rows = []
    columns = int(table.get("columns") or 0)
    for row in table.get("rows") or []:
        cells = []
        for cell in row.get("cells") or []:
            cells.append(str(cell.get("text", "")))
        rows.append(cells)
    columns = max(columns, max((len(row) for row in rows), default=1))
    if not rows:
        rows = [[""] * columns]
    line_height = 22
    margin = 12
    cell_padding = 6
    col_width = max(80, (width - 2 * margin) // max(1, columns))
    width = col_width * columns + 2 * margin
    height = margin * 2 + line_height * len(rows)
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font = _font(14)
    for r_index, row in enumerate(rows):
        y0 = margin + r_index * line_height
        draw.line((margin, y0, width - margin, y0), fill="black", width=1)
        for c_index in range(columns):
            x0 = margin + c_index * col_width
            if c_index:
                draw.line((x0, y0, x0, y0 + line_height), fill="black", width=1)
            text = row[c_index] if c_index < len(row) else ""
            draw.text((x0 + cell_padding, y0 + cell_padding - 2),
                      text[:60], fill="black", font=font)
    draw.line((margin, margin + len(rows) * line_height,
               width - margin, margin + len(rows) * line_height),
              fill="black", width=1)
    return image


def _side_by_side(original: Path, table: dict | None, target: Path,
                  title: str) -> str:
    with Image.open(original) as source:
        left = source.convert("RGB")
    if table:
        right = _render_table(table)
    else:
        right = Image.new("RGB", (600, 300), "white")
        ImageDraw.Draw(right).text(
            (20, 20), "No native recreation", fill="black", font=_font(18))
    height = max(left.height, right.height, 260)
    def fit(image):
        if image.height == height:
            return image
        ratio = height / max(1, image.height)
        return image.resize((max(1, int(image.width * ratio)), height))
    left, right = fit(left), fit(right)
    gap = 20
    sheet = Image.new("RGB", (left.width + right.width + gap * 3,
                              height + 40), "white")
    sheet.paste(left, (gap, 30))
    sheet.paste(right, (left.width + gap * 2, 30))
    draw = ImageDraw.Draw(sheet)
    draw.text((gap, 8), f"Original crop — {title}", fill="black",
              font=_font(16))
    draw.text((left.width + gap * 2, 8), "Native/recreated preview",
              fill="black", font=_font(16))
    target.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(target, "PNG")
    return str(target.relative_to(config.PROJECT_ROOT).as_posix())


def _compare_asset(asset: dict, config_data: dict) -> dict:
    kind = str(asset.get("kind", ""))
    if kind != "table":
        asset["treatment"] = "crop"
        asset["compare"] = {
            "status": "not_applicable",
            "method": "original_only",
            "reason": "pictures/figures/diagrams/formulas are never redrawn",
        }
        return asset
    native = asset.get("native_table")
    crop = config.PROJECT_ROOT / asset["path"]
    if not native:
        compare_path = COMPARE / f"{asset['id']}_compare.png"
        _side_by_side(crop, None, compare_path, asset.get("label", ""))
        asset["treatment"] = "crop"
        asset["compare"] = {
            "status": "rejected",
            "method": "no_native_table",
            "reason": "table extractor did not produce a usable cell grid",
            "side_by_side": (
                compare_path.relative_to(config.PROJECT_ROOT).as_posix()),
        }
        return asset
    try:
        ocr_text = win_ocr(crop)
    except Exception as error:
        ocr_text = ""
        compare_path = COMPARE / f"{asset['id']}_compare.png"
        _side_by_side(crop, native, compare_path, asset.get("label", ""))
        asset["compare"] = {
            "status": "rejected",
            "method": "ocr_error",
            "reason": str(error),
            "side_by_side": (
                compare_path.relative_to(config.PROJECT_ROOT).as_posix()),
        }
        asset["treatment"] = "crop"
        return asset
    score, detail = _table_score(native, ocr_text)
    threshold = float(config_data.get("table_fuzzy_threshold", 0.92))
    accepted = score >= threshold and detail["cells"] >= 4
    asset["treatment"] = "native_table" if accepted else "crop"
    compare_path = COMPARE / f"{asset['id']}_compare.png"
    _side_by_side(crop, native, compare_path, asset.get("label", ""))
    asset["compare"] = {
        "status": "accepted" if accepted else "rejected",
        "method": "ocr_cell_fuzzy_match",
        "score": round(score, 4),
        "threshold": threshold,
        "detail": detail,
        "ocr_text": ocr_text[:4000],
        "native_text": _table_text_flat(native)[:4000],
        "side_by_side": (
            compare_path.relative_to(config.PROJECT_ROOT).as_posix()),
    }
    return asset


def build() -> dict:
    config_data = pure_config.ensure()
    assets = []
    for path in sorted(ASSETS.glob("*.json")):
        asset = _load(path, {})
        if not asset or asset.get("verdict") not in (None, "", "pending"):
            assets.append(asset)
            continue
        asset = _compare_asset(asset, config_data)
        _save(path, asset)
        assets.append(asset)
    accepted = sum(1 for row in assets
                   if row.get("compare", {}).get("status") == "accepted")
    rejected = sum(1 for row in assets
                   if row.get("compare", {}).get("status") == "rejected")
    original = sum(1 for row in assets
                   if row.get("compare", {}).get("status") == "not_applicable")
    report = {
        "schema_version": 1,
        "subject": "CSC429",
        "stage": "P2",
        "assets": len(assets),
        "native_table_accepted": accepted,
        "table_crop_fallback": rejected,
        "original_only": original,
        "thresholds": {
            "table_fuzzy_threshold": config_data.get(
                "table_fuzzy_threshold"),
            "diagram_recreate_max_nodes": config_data.get(
                "diagram_recreate_max_nodes"),
            "diagram_recreate_max_edges": config_data.get(
                "diagram_recreate_max_edges"),
        },
        "cost_usd": 0.0,
    }
    _save(REPORT, report)
    _save(BANK / "assets_index.json", {
        "schema_version": 1,
        "count": len(assets),
        "assets": [
            {key: asset.get(key) for key in (
                "id", "question_ids", "source_paper", "page", "label",
                "kind", "treatment", "sha256", "path", "verdict")}
            for asset in sorted(assets, key=lambda row: row.get("id", ""))
        ],
    })
    return report


def main() -> None:
    print(json.dumps(build(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
