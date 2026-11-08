"""Normalize MinerU output into reviewable paper/question/asset records.

MinerU is the parser of record; the legacy 300 dpi page render is only used
when a referenced figure/table has no MinerU asset.
"""
from __future__ import annotations

import html
import json
import re
from collections import Counter
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw, ImageFont

QUESTION_RE = re.compile(r"\bQUESTION\s+([0-9OIl]{1,3})\b", re.I)
MARKS_RE = re.compile(r"\(?\s*([0-9OIl]{1,2})\s*marks?\s*\)?", re.I)
SUBPART_RE = re.compile(r"^\(?([a-h]|[ivx]{1,4})\)\s*", re.I | re.M)
REF_RE = re.compile(r"\b(Figure|Table)\s*(\d+)\b", re.I)
CAPTION_RE = re.compile(r"\b(Figure|Table)\s*(\d+)\b", re.I)


def _load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _save(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def _find_content_list(root: Path) -> Path | None:
    for path in root.rglob("*content_list*.json"):
        if path.is_file():
            return path
    return None


def _norm(text: str) -> str:
    return " ".join(str(text or "").split())


def _number(raw: str) -> int | None:
    value = (raw.upper().replace("O", "0").replace("I", "1")
             .replace("L", "1"))
    return int(value) if value.isdigit() else None


def _caption_text(block: dict) -> str:
    for key in ("image_caption", "table_caption", "caption", "text"):
        value = block.get(key)
        if isinstance(value, list):
            value = " ".join(str(item) for item in value)
        if value:
            return _norm(value)
    return ""


def _bbox(block: dict) -> list[float] | None:
    value = block.get("bbox") or block.get("box")
    if isinstance(value, (list, tuple)) and len(value) == 4:
        try:
            return [float(item) for item in value]
        except (TypeError, ValueError):
            return None
    return None


def _page_size(pdf_path: Path, page_idx: int) -> tuple[float, float]:
    with pymupdf.open(str(pdf_path)) as pdf:
        if 0 <= page_idx < len(pdf):
            page = pdf[page_idx]
            return page.rect.width, page.rect.height
    return 595.0, 842.0


def _px_bbox(bbox: list[float] | None, page_size: tuple[float, float],
             image_size: tuple[int, int]) -> tuple[int, int, int, int]:
    if not bbox:
        return 0, 0, image_size[0], image_size[1]
    x0, y0, x1, y1 = bbox
    if max(x0, y0, x1, y1) <= 1000:
        x0 = x0 / 1000 * page_size[0]
        x1 = x1 / 1000 * page_size[0]
        y0 = y0 / 1000 * page_size[1]
        y1 = y1 / 1000 * page_size[1]
    image_width, image_height = image_size
    sx = image_width / page_size[0]
    sy = image_height / page_size[1]
    return (max(0, int(x0 * sx)), max(0, int(y0 * sy)),
            min(image_width, int(x1 * sx)),
            min(image_height, int(y1 * sy)))


def _image_path(block: dict, root: Path) -> Path | None:
    value = block.get("img_path") or block.get("image_path")
    if not value:
        return None
    candidate = root / str(value)
    if candidate.is_file():
        return candidate
    matches = list(root.rglob(Path(str(value)).name))
    return matches[0] if matches else None


def _render_page(pdf_path: Path, page_idx: int, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    with pymupdf.open(str(pdf_path)) as pdf:
        page = pdf[page_idx]
        pix = page.get_pixmap(dpi=300, colorspace=pymupdf.csRGB,
                              alpha=False)
        out.write_bytes(pix.tobytes("png"))
    return out


def _font(size: int):
    for name in ("arial.ttf", "Arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _asset_preview(block: dict, root: Path, size=(360, 240)) -> Image.Image:
    path = _image_path(block, root)
    if path:
        with Image.open(path) as image:
            image = image.convert("RGB")
            image.thumbnail(size)
            return image.copy()
    image = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(image)
    text = _caption_text(block) or block.get("table_body") or "MinerU table"
    text = re.sub(r"<[^>]+>", " ", str(text))
    draw.multiline_text((8, 8), text[:500], fill="black",
                        font=_font(12), spacing=3)
    return image


def _contact_sheet(paper_id: str, pdf_path: Path, page_cache: Path,
                   cache_dir: Path, assets: list[dict], model: str,
                   target: Path) -> str:
    rows = []
    for asset in assets:
        page_idx = int(asset.get("page_idx", 0))
        page_path = page_cache / f"page_{page_idx + 1:03d}.png"
        if not page_path.exists():
            _render_page(pdf_path, page_idx, page_path)
        with Image.open(page_path) as page:
            page = page.convert("RGB")
            box = _px_bbox(asset.get("bbox"), (page.width, page.height),
                           (page.width, page.height))
            original = page.crop(box)
            original.thumbnail((360, 240))
            original = original.copy()
        preview = _asset_preview(asset["_block"], cache_dir, (360, 240))
        recreation = Image.new("RGB", (360, 240), "white")
        ImageDraw.Draw(recreation).text(
            (8, 8), "No recreation", fill="black", font=_font(14))
        height = max(original.height, preview.height, recreation.height) + 30
        sheet = Image.new("RGB", (1120, height), "white")
        x = 0
        for image, label in ((original, "Original page crop"),
                             (preview, "MinerU image/table"),
                             (recreation, "Recreation")):
            sheet.paste(image, (x, 24))
            ImageDraw.Draw(sheet).text((x, 5), label, fill="black",
                                       font=_font(13))
            x += 370
        rows.append(sheet)
    if not rows:
        rows.append(Image.new("RGB", (1120, 260), "white"))
    height = sum(row.height for row in rows)
    contact = Image.new("RGB", (1120, height), "white")
    y = 0
    for row in rows:
        contact.paste(row, (0, y))
        y += row.height
    target.parent.mkdir(parents=True, exist_ok=True)
    contact.save(target, "PNG")
    return str(target)


def _question_page(questions: list[dict], page_idx: int, y: float) -> int | None:
    candidates = [index for index, question
                  in enumerate(questions)
                  if int(question.get("page_idx", 0)) == page_idx
                  and float(question.get("y", 0)) <= y + 20]
    if candidates:
        return candidates[-1]
    same_page = [index for index, question in enumerate(questions)
                 if int(question.get("page_idx", 0)) == page_idx]
    return same_page[-1] if same_page else None


def normalize(*, paper_id: str, pdf_path: Path, cache_dir: Path,
              model: str, out_dir: Path) -> dict:
    content_path = _find_content_list(cache_dir)
    if content_path is None:
        raise RuntimeError(f"MinerU content_list.json missing in {cache_dir}")
    blocks = _load(content_path, [])
    if not isinstance(blocks, list):
        blocks = []
    page_cache = out_dir / "pages"
    page_cache.mkdir(parents=True, exist_ok=True)
    text_blocks = []
    asset_blocks = []
    equations = 0
    for index, block in enumerate(blocks):
        if not isinstance(block, dict):
            continue
        block = dict(block)
        block["_block_id"] = f"B{index + 1:04d}"
        kind = str(block.get("type", "")).lower()
        if kind == "text":
            text_blocks.append(block)
        elif kind in {"image", "table"}:
            asset_blocks.append(block)
        elif kind == "equation":
            equations += 1
    text_blocks.sort(key=lambda block: (
        int(block.get("page_idx", 0)), (_bbox(block) or [0, 0, 0, 0])[1]))
    questions = []
    current = None
    for block in text_blocks:
        text = _norm(block.get("text", ""))
        match = QUESTION_RE.search(text)
        bbox = _bbox(block) or [0, 0, 0, 0]
        if match:
            number = _number(match.group(1))
            if number is not None:
                current = {
                    "question_id": f"{paper_id}-Q{number}",
                    "number": number,
                    "page_idx": int(block.get("page_idx", 0)),
                    "y": bbox[1],
                    "bbox": bbox,
                    "blocks": [block["_block_id"]],
                    "text": text,
                    "subparts": [],
                    "refs": [],
                }
                questions.append(current)
                text = text[match.end():].strip()
        if current is None:
            continue
        if block["_block_id"] not in current["blocks"]:
            current["blocks"].append(block["_block_id"])
        if text:
            current["text"] = (current["text"] + "\n" + text).strip()
        marks = MARKS_RE.search(text or current["text"])
        if marks and not current.get("marks"):
            current["marks"] = _number(marks.group(1))
        for ref in REF_RE.findall(text):
            label = f"{ref[0].title()} {int(ref[1])}"
            if label not in current["refs"]:
                current["refs"].append(label)
    for question in questions:
        subparts = []
        for match in SUBPART_RE.finditer(question["text"]):
            subparts.append({"label": match.group(1).lower(),
                             "text": question["text"][match.end():].strip()})
        question["subparts"] = subparts
        question["refs"] = sorted(set(question["refs"]),
                                  key=lambda value: (
                                      value.split()[0], int(value.split()[1])))
    assets = []
    for block in asset_blocks:
        kind = str(block.get("type", "")).lower()
        bbox = _bbox(block) or [0, 0, 0, 0]
        caption = _caption_text(block)
        label_match = CAPTION_RE.search(caption)
        label = (f"{label_match.group(1).title()} {label_match.group(2)}"
                 if label_match else "")
        page_idx = int(block.get("page_idx", 0))
        target = _question_page(questions, page_idx, bbox[1])
        if label:
            for index, question in enumerate(questions):
                if label in question["refs"]:
                    target = index
                    break
        asset = {
            "asset_id": f"MU-{block['_block_id']}",
            "question_index": target,
            "page_idx": page_idx,
            "bbox": bbox,
            "kind": "table" if kind == "table" else "image",
            "label": label,
            "caption": caption,
            "img_path": str(_image_path(block, cache_dir) or ""),
            "table_html": block.get("table_body") or block.get("html") or "",
            "provenance": {"parser": "mineru", "model": model,
                           "block_id": block["_block_id"],
                           "page_idx": page_idx},
            "_block": block,
        }
        if target is not None:
            questions[target].setdefault("assets", []).append(asset["asset_id"])
        assets.append(asset)
    # Fallback for referenced labels with no MinerU asset.
    fallback = []
    for index, question in enumerate(questions):
        attached = {asset["label"] for asset in assets
                    if asset.get("question_index") == index
                    or asset["asset_id"] in (question.get("assets") or [])}
        for ref in question["refs"]:
            if ref in attached:
                continue
            page_idx = int(question.get("page_idx", 0))
            page_path = page_cache / f"page_{page_idx + 1:03d}.png"
            if not page_path.exists():
                _render_page(pdf_path, page_idx, page_path)
            fallback.append({
                "asset_id": f"FB-{question['question_id']}-{ref.replace(' ', '')}",
                "question_id": question["question_id"],
                "label": ref,
                "page_idx": page_idx,
                "path": str(page_path),
                "treatment": "page_crop_fallback",
                "reason": "referenced label had no MinerU image/table block",
            })
            question.setdefault("fallback_assets", []).append(fallback[-1]["asset_id"])
    contact = _contact_sheet(paper_id, pdf_path, page_cache, cache_dir,
                             assets, model, out_dir / "contact_sheet.png")
    referenced = sum(len(question["refs"]) for question in questions)
    resolved = sum(1 for question in questions for ref in question["refs"]
                   if any(asset["label"] == ref for asset in assets))
    result = {
        "schema_version": 1,
        "paper_id": paper_id,
        "model": model,
        "content_list": str(content_path),
        "counts": {
            "pages": max((int(block.get("page_idx", 0)) for block in blocks),
                         default=-1) + 1,
            "questions": len(questions),
            "figures": sum(1 for asset in assets if asset["kind"] == "image"),
            "tables": sum(1 for asset in assets if asset["kind"] == "table"),
            "equations": equations,
            "assets": len(assets),
            "referenced_figures_tables": referenced,
            "resolved_references": resolved,
            "fallback_assets": len(fallback),
        },
        "questions": questions,
        "assets": [{key: value for key, value in asset.items()
                    if key != "_block"} for asset in assets],
        "fallback": fallback,
        "contact_sheet": contact,
        "provenance": {"parser": "mineru", "model": model,
                       "content_list": str(content_path)},
    }
    _save(out_dir / "normalized.json", result)
    return result
