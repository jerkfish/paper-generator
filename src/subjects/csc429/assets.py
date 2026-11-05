"""Crop original CSC429 figures and tables from captured page images.

All pages are scans.  Embedded non-full-page images are incomplete 1-bit
masks, so assets are page-image crops, never extracted masks.  Figure
captions are treated as below the figure; table captions as above the table.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from src import config

SUBJECT = "CSC429"
TRACKING = config.TRACKING_DIR / "csc429"
PAGES = TRACKING / "pages"
LAYOUT = TRACKING / "layout"
ASSETS = TRACKING / "assets"
REGISTER = TRACKING / "papers_register.json"

CAPTION_RE = re.compile(
    r"^\s*(Figure|Fig\.?|Table|Rajah|Gambar|Jadual)\s*(\d+)[A-Za-z]?\s*[:.\-–]?",
    re.I,
)
REF_RE = re.compile(r"\b(Figure|Table)\s*(\d+)", re.I)
TEXT_REF_RE = re.compile(
    r"illustrat|show|depict|is based|refer to|given in|below|above", re.I)
FURNITURE_RE = re.compile(
    r"CONF[I!1]DENTIAL|Hak\s*C[i1l]pta|DO\s*NOT\s*TURN|"
    r"^(?:CS|CD)[A-Z0-9/\s]*CSC429$|^This\s+examination\s+paper", re.I)


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-") or "asset"


def _norm_label(kind: str, number: str) -> str:
    kind = kind.lower()
    kind = "Table" if kind in {"table", "jadual"} else "Figure"
    return f"{kind} {int(number)}"


def _kind(label: str) -> str:
    return "table" if label.lower().startswith("table") else "figure"


def _rel(path: Path) -> str:
    try:
        return path.relative_to(config.PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _text(line: dict) -> str:
    return str(line.get("text", "")).strip()


def _bbox(line: dict) -> tuple[float, float, float, float]:
    x0, y0, x1, y1 = line["bbox"]
    return float(x0), float(y0), float(x1), float(y1)


def _inside_content(line: dict, width: float, height: float) -> bool:
    x0, y0, x1, y1 = _bbox(line)
    if y1 < 0.10 * height or y0 > 0.90 * height:
        return False
    text = _text(line)
    if not text or FURNITURE_RE.search(text) or text.isdigit():
        return False
    if x1 < 0.03 * width or x0 > 0.97 * width:
        return False
    return True


def _caption_lines(page: dict) -> list[dict]:
    width, height = float(page["width"]), float(page["height"])
    out = []
    for line in page.get("lines", []):
        if not _inside_content(line, width, height):
            continue
        text = _text(line)
        if len(text) > 140 or TEXT_REF_RE.search(text):
            continue
        if CAPTION_RE.match(text):
            out.append(line)
    return out


def _largest_gap(lines: list[dict], low: float, high: float,
                 *, above: bool) -> tuple[float | None, bool]:
    """Return the band edge after the largest gap and whether one was found."""
    points = []
    for line in lines:
        x0, y0, x1, y1 = _bbox(line)
        if y0 < low or y1 > high:
            continue
        points.append((y0, y1))
    if not points:
        return None, False
    points.sort()
    best = None
    best_gap = 0.0
    cursor = low
    for y0, y1 in points:
        gap = y0 - cursor
        if gap > best_gap:
            best_gap = gap
            best = cursor
        cursor = max(cursor, y1)
    gap = high - cursor
    if gap > best_gap:
        best_gap = gap
        best = cursor
    if best is None or best_gap < 20:
        return None, False
    return best, True


def _crop_image(page: dict, bbox: list[float]) -> Image.Image:
    image_path = config.PROJECT_ROOT / page["image"]
    width, height = page["width"], page["height"]
    page_width, page_height = page["page_points"]
    sx = width / page_width
    sy = height / page_height
    left = max(0, int(bbox[0] * sx))
    top = max(0, int(bbox[1] * sy))
    right = min(width, int(bbox[2] * sx))
    bottom = min(height, int(bbox[3] * sy))
    with Image.open(image_path) as image:
        return image.convert("RGB").crop((left, top, right, bottom))


def _save_crop(image: Image.Image, target: Path) -> tuple[int, int]:
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, "PNG", dpi=(200, 200))
    return image.width, image.height


def _crop_from_page(page: dict, bbox: list[float],
                    target: Path) -> tuple[int, int]:
    return _save_crop(_crop_image(page, bbox), target)


def _ink_band(image: Image.Image, start_row: int, direction: int,
              page_height: float, *, skip_pt: float = 30.0,
              inner_pt: float = 22.0) -> tuple[int, int] | None:
    """Find the nearest ink band above (-1) or below (+1) a row."""
    array = np.asarray(image.convert("L"))
    if array.size == 0:
        return None
    height = array.shape[0]
    scale = height / page_height
    ink = (array < 180).sum(axis=1) > max(2, int(0.002 * array.shape[1]))
    rows = np.flatnonzero(ink)
    if rows.size == 0:
        return None
    skip_px = max(1, int(skip_pt * scale))
    inner_px = max(1, int(inner_pt * scale))
    if direction < 0:
        candidates = rows[rows < start_row]
        if candidates.size == 0:
            return None
        first = int(candidates[-1])
        if start_row - first > skip_px:
            return None
        top = first
        previous = first
        for row in reversed(candidates[:-1].tolist()):
            if previous - row > inner_px:
                break
            top = row
            previous = row
        return top, first
    candidates = rows[rows > start_row]
    if candidates.size == 0:
        return None
    first = int(candidates[0])
    if first - start_row > skip_px:
        return None
    bottom = first
    previous = first
    for row in candidates[1:].tolist():
        if row - previous > inner_px:
            break
        bottom = row
        previous = row
    return first, bottom


def _contact_sheet(paper_id: str, page_manifest: dict,
                   asset_rows: list[dict], target: Path) -> str:
    pages = page_manifest.get("pages", [])
    if not pages:
        return ""
    thumb_width = 360
    margin = 18
    label_height = 26
    columns = 2
    thumbs = []
    for page in pages:
        with Image.open(config.PROJECT_ROOT / page["image"]) as image:
            ratio = thumb_width / image.width
            thumb = image.convert("RGB").resize(
                (thumb_width, max(1, int(image.height * ratio))))
        draw = ImageDraw.Draw(thumb)
        sx = thumb.width / page["page_points"][0]
        sy = thumb.height / page["page_points"][1]
        for asset in asset_rows:
            if int(asset["page"]) != int(page["page"]):
                continue
            x0, y0, x1, y1 = asset["bbox_pdf"]
            draw.rectangle((x0 * sx, y0 * sy, x1 * sx, y1 * sy),
                           outline="red", width=4)
        draw.rectangle((0, thumb.height - label_height,
                        thumb.width, thumb.height), fill="white")
        draw.text((6, thumb.height - label_height + 3),
                  f"Page {page['page']}", fill="black")
        thumbs.append(thumb)
    if not thumbs:
        return ""
    rows = (len(thumbs) + columns - 1) // columns
    cell_height = max(thumb.height for thumb in thumbs) + label_height
    sheet = Image.new(
        "RGB",
        (columns * (thumb_width + margin) + margin,
         rows * (cell_height + margin) + margin),
        "white")
    for index, thumb in enumerate(thumbs):
        x = margin + (index % columns) * (thumb_width + margin)
        y = margin + (index // columns) * (cell_height + margin)
        sheet.paste(thumb, (x, y))
    target.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(target, "PNG")
    return _rel(target)


def _furniture_filtered_lines(page: dict) -> list[dict]:
    width, height = float(page["width"]), float(page["height"])
    return [line for line in page.get("lines", [])
            if _inside_content(line, width, height)]


def _assets_for_page(paper: dict, page: dict, page_meta: dict,
                     paper_dir: Path,
                     used_ids: set[str]) -> tuple[list[dict], list[dict]]:
    width, height = float(page["width"]), float(page["height"])
    content_left = 0.06 * width
    content_right = 0.94 * width
    content_top = 0.10 * height
    content_bottom = 0.90 * height
    lines = _furniture_filtered_lines(page)
    assets = []
    unresolved = []
    for caption in _caption_lines(page):
        text = _text(caption)
        match = CAPTION_RE.match(text)
        if not match:
            continue
        label = _norm_label(match.group(1), match.group(2))
        kind = _kind(label)
        cx0, cy0, cx1, cy1 = _bbox(caption)
        flags = []
        found = False
        method = "page_crop_band"
        with Image.open(config.PROJECT_ROOT / page_meta["image"]) as raw:
            page_image = raw.convert("RGB")
        scale = page_image.height / height
        content_box = None
        caption_box = None
        if kind == "figure":
            band = _ink_band(page_image, int(cy0 * scale) - 1, -1, height)
            if band is not None:
                top_pt = max(content_top, band[0] / scale)
                content_box = [content_left, top_pt,
                               content_right, max(top_pt + 10, cy0 - 4)]
                caption_box = [0.05 * width, cy0 - 4,
                               0.95 * width, cy1 + 8]
                method = "page_crop_ink"
                found = True
            else:
                band_start, found = _largest_gap(
                    [line for line in lines if _bbox(line)[3] < cy0 - 2],
                    content_top, cy0 - 2, above=True)
                if band_start is None:
                    band_start = max(content_top, cy0 - 300)
                    flags.append("gap_not_found")
                content_box = [content_left, band_start + 8,
                               content_right, cy0 - 4]
                caption_box = [0.05 * width, cy0 - 4,
                               0.95 * width, cy1 + 8]
        else:
            band = _ink_band(page_image, int(cy1 * scale) + 1, 1, height)
            if band is not None:
                bottom_pt = min(content_bottom, band[1] / scale)
                content_box = [content_left, max(content_top, cy0 - 4),
                               content_right, bottom_pt]
                caption_box = [0.05 * width, cy0 - 6,
                               0.95 * width, min(content_bottom, cy1 + 6)]
                method = "page_crop_ink"
                found = True
            else:
                band_end, found = _largest_gap(
                    [line for line in lines if _bbox(line)[1] > cy1 + 2],
                    cy1 + 2, content_bottom, above=False)
                if band_end is None:
                    band_end = min(content_bottom, cy1 + 320)
                    flags.append("gap_not_found")
                content_box = [content_left, max(content_top, cy1 + 4),
                               content_right, band_end + 8]
                caption_box = [0.05 * width, cy0 - 6,
                               0.95 * width, cy1 + 6]
        if content_box is None or caption_box is None:
            continue
        band_lines = [
            line for line in lines
            if _bbox(line)[3] >= content_box[1]
            and _bbox(line)[1] <= content_box[3]
        ]
        mark_lines = [
            line for line in band_lines
            if re.search(r"\b\d{1,2}\s*marks?\b", _text(line), re.I)
        ]
        if kind == "figure" and mark_lines:
            mark_bottom = max(_bbox(line)[3] for line in mark_lines)
            if mark_bottom + 6 < content_box[3]:
                content_box[1] = max(content_box[1], mark_bottom + 6)
                flags.append("trimmed_question_marks")
        elif kind == "table" and mark_lines:
            mark_top = min(_bbox(line)[1] for line in mark_lines)
            if mark_top - 6 > content_box[1]:
                content_box[3] = min(content_box[3], mark_top - 6)
                flags.append("trimmed_question_marks")
        right_prose = any(
            len(_text(line)) > 20 and _bbox(line)[0] > 0.45 * width
            for line in band_lines)
        left_prose = any(
            len(_text(line)) > 20 and _bbox(line)[2] < 0.55 * width
            for line in band_lines)
        caption_center = (cx0 + cx1) / 2
        if right_prose and not left_prose:
            content_box[2] = min(content_box[2], 0.50 * width)
            flags.append("prose_column")
        elif left_prose and not right_prose:
            content_box[0] = max(content_box[0], 0.50 * width)
            flags.append("prose_column")
        elif right_prose and left_prose:
            if caption_center < 0.5 * width:
                content_box[2] = min(content_box[2], 0.50 * width)
            else:
                content_box[0] = max(content_box[0], 0.50 * width)
            flags.append("prose_column")
        bbox = [
            min(content_box[0], caption_box[0]),
            min(content_box[1], caption_box[1]),
            max(content_box[2], caption_box[2]),
            max(content_box[3], caption_box[3]),
        ]
        bbox = [max(0.0, min(bbox[0], width)),
                max(0.0, min(bbox[1], height)),
                max(0.0, min(bbox[2], width)),
                max(0.0, min(bbox[3], height))]
        if (content_box[2] - content_box[0] < 80
                or content_box[3] - content_box[1] < 20):
            if kind == "figure":
                content_box = [content_left,
                               max(content_top, cy0 - 220),
                               content_right, max(content_top + 20, cy0 - 4)]
            else:
                content_box = [content_left, cy1 + 4,
                               content_right,
                               min(content_bottom, cy1 + 220)]
            flags.append("small_crop_fallback")
        area_ratio = ((bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                      / (width * height))
        if area_ratio > 0.65:
            flags.append("crop_too_large")
        base_id = f"{paper['paper_id']}-{'T' if kind == 'table' else 'F'}{match.group(2)}"
        asset_id = base_id
        suffix = 2
        while asset_id in used_ids:
            asset_id = f"{base_id}-{suffix}"
            suffix += 1
        used_ids.add(asset_id)
        target = paper_dir / f"{asset_id}.png"
        try:
            content_image = _crop_image(page_meta, content_box)
            caption_image = _crop_image(page_meta, caption_box)
            width_px = max(content_image.width, caption_image.width)
            height_px = content_image.height + 6 + caption_image.height
            composed = Image.new("RGB", (width_px, height_px), "white")
            composed.paste(content_image,
                           ((width_px - content_image.width) // 2, 0))
            composed.paste(caption_image,
                           ((width_px - caption_image.width) // 2,
                            content_image.height + 6))
            crop_width, crop_height = _save_crop(composed, target)
        except Exception as error:
            unresolved.append({
                "paper_id": paper["paper_id"], "label": label,
                "page": page["page"], "reason": f"crop failed: {error}",
                "page_image": page_meta["image"],
            })
            continue
        confidence = "high"
        if flags:
            confidence = "medium"
        if ("crop_too_large" in flags or "gap_not_found" in flags
                or "small_crop_fallback" in flags):
            confidence = "low"
        assets.append({
            "asset_id": asset_id,
            "paper_id": paper["paper_id"],
            "source_file": paper["paper"],
            "kind": kind,
            "label": label,
            "caption": text,
            "page": page["page"],
            "bbox_pdf": [round(value, 2) for value in bbox],
            "content_bbox": [round(value, 2) for value in content_box],
            "caption_bbox": [round(value, 2) for value in caption_box],
            "path": _rel(target),
            "width_px": crop_width,
            "height_px": crop_height,
            "dpi": 200,
            "sha256": _sha256(target),
            "method": method,
            "confidence": confidence,
            "review_flags": flags,
        })
    return assets, unresolved


def build_assets(force: bool = False) -> dict:
    ASSETS.mkdir(parents=True, exist_ok=True)
    page_manifests = {}
    for path in PAGES.glob("*/manifest.json"):
        payload = _load(path)
        page_manifests[payload["paper"]] = payload
    all_assets = []
    all_unresolved = []
    papers = []
    for layout_path in sorted(LAYOUT.glob("*.json")):
        paper = _load(layout_path)
        paper_id = paper["paper_id"]
        paper_dir = ASSETS / paper_id
        paper_dir.mkdir(parents=True, exist_ok=True)
        page_manifest = page_manifests.get(paper["paper"])
        if page_manifest is None:
            continue
        used_ids: set[str] = set()
        paper_assets = []
        paper_unresolved = []
        for index, page in enumerate(paper.get("pages", [])):
            pages_meta = page_manifest.get("pages", [])
            if index >= len(pages_meta):
                break
            page_meta = pages_meta[index]
            assets, unresolved = _assets_for_page(
                paper, page, page_meta, paper_dir, used_ids)
            paper_assets.extend(assets)
            paper_unresolved.extend(unresolved)
        # References without a caption.
        captions = {asset["label"] for asset in paper_assets}
        seen = set()
        for index, page in enumerate(paper.get("pages", [])):
            pages_meta = page_manifest.get("pages", [])
            page_image = (pages_meta[index]["image"]
                          if index < len(pages_meta) else "")
            for line in page.get("lines", []):
                for match in REF_RE.finditer(_text(line)):
                    label = _norm_label(match.group(1), match.group(2))
                    key = (page["page"], label)
                    if label in captions or key in seen:
                        continue
                    seen.add(key)
                    paper_unresolved.append({
                        "paper_id": paper_id, "label": label,
                        "page": page["page"],
                        "reason": "reference without caption",
                        "page_image": page_image,
                    })
        contact = _contact_sheet(
            paper_id, page_manifest, paper_assets,
            paper_dir / "contact_sheet.png")
        per_paper = {
            "schema_version": 1,
            "paper_id": paper_id,
            "paper": paper["paper"],
            "source_file": paper["paper"],
            "source_kind": paper.get("source_kind", ""),
            "assets": paper_assets,
            "unresolved": paper_unresolved,
            "contact_sheet": contact,
        }
        (paper_dir / "manifest.json").write_text(
            json.dumps(per_paper, indent=2), encoding="utf-8")
        papers.append({
            "paper_id": paper_id,
            "paper": paper["paper"],
            "assets": [asset["asset_id"] for asset in paper_assets],
            "contact_sheet": contact,
        })
        all_assets.extend(paper_assets)
        all_unresolved.extend(paper_unresolved)
    all_assets.sort(key=lambda row: (row["paper_id"], row["page"],
                                     row["bbox_pdf"][1], row["bbox_pdf"][0],
                                     row["label"]))
    all_unresolved.sort(key=lambda row: (row["paper_id"], row["page"],
                                         row["label"]))
    counts = {
        "assets": len(all_assets),
        "figures": sum(1 for row in all_assets if row["kind"] == "figure"),
        "tables": sum(1 for row in all_assets if row["kind"] == "table"),
        "high": sum(1 for row in all_assets
                    if row["confidence"] == "high"),
        "medium": sum(1 for row in all_assets
                      if row["confidence"] == "medium"),
        "low": sum(1 for row in all_assets if row["confidence"] == "low"),
        "unresolved": len(all_unresolved),
        "contact_sheets": sum(1 for row in papers if row["contact_sheet"]),
    }
    manifest = {
        "schema_version": 1,
        "subject": SUBJECT,
        "generated_by": "src.subjects.csc429.assets",
        "crop": {"dpi": 200, "format": "png", "mode": "page_image_crop"},
        "assets": all_assets,
        "unresolved": all_unresolved,
        "papers": papers,
        "counts": counts,
    }
    (ASSETS / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build_assets(args.force), indent=2))


if __name__ == "__main__":
    main()
