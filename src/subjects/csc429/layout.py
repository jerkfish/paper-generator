"""Build a page/line layout layer for CSC429 source papers.

Text-layer pages use PyMuPDF coordinates directly; scanned pages use the
Windows OCR engine's line/word boxes mapped back to PDF points.  The layout
layer is what lets later stages locate question boundaries and figure
captions without guessing.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pymupdf

from src import config
from src.ingest.ocr import win_ocr_layout

SUBJECT = "CSC429"
TRACKING = config.TRACKING_DIR / "csc429"
PAPERS = config.subject_papers_dir(SUBJECT)
REGISTER = TRACKING / "papers_register.json"
PAGES = TRACKING / "pages"
LAYOUT = TRACKING / "layout"
CAPTION_RE = re.compile(r"\b(?:Figure|Table|Rajah|Diagram)\s*\d+", re.I)


def _text_layout(page: pymupdf.Page) -> list[dict]:
    lines = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            text = "".join(span.get("text", "") for span in line["spans"])
            text = text.strip()
            if not text:
                continue
            x0, y0, x1, y1 = line["bbox"]
            lines.append({
                "text": text,
                "bbox": [round(x0, 2), round(y0, 2),
                         round(x1, 2), round(y1, 2)],
            })
    return lines



MARK_LINE_RE = re.compile(
    r"^[\[(]?\s*['\"`]?\s*[0-9OIlSs]{1,2}\s*marks?\s*[\])]?\s*$", re.I)
DANGLING_RE = re.compile(
    r"\b(in|of|to|for|with|by|from|at|on)\s*$", re.I)


def _repair_truncated_lines(lines: list[dict], page: dict,
                            width_pt: float, height_pt: float) -> list[dict]:
    """Recover a wrapped continuation that the full-page OCR missed.

    A line ending in a connector word followed by a marks block is usually
    split across two visual lines.  A high-resolution crop of that small band
    recovers the missing tail (for example ``9(a).`` in CSC429-2014-06 Q9).
    """
    from PIL import Image

    marks = [
        line for line in lines
        if MARK_LINE_RE.match(line["text"].strip())
    ]
    if not marks:
        return lines
    image_path = config.PROJECT_ROOT / page["image"]
    if not image_path.is_file():
        return lines
    image = Image.open(image_path)
    sx = image.width / width_pt
    sy = image.height / height_pt
    additions: list[dict] = []
    for line in lines:
        text = " ".join(line["text"].split())
        if len(text.split()) < 8 or not DANGLING_RE.search(text):
            continue
        x0, y0, x1, y1 = [float(value) for value in line["bbox"]]
        if x1 < 0.80 * width_pt:
            continue
        candidates = [
            mark for mark in marks
            if y1 + 8 < float(mark["bbox"][1]) < y1 + 45
        ]
        if not candidates:
            continue
        mark = min(candidates, key=lambda item: float(item["bbox"][1]))
        bottom = min(height_pt, float(mark["bbox"][1]) + 10.0)
        recovered_values: list[tuple[str, dict]] = []
        for offset, right_fraction in (
                (8.0, 0.94), (4.8, 0.94), (12.0, 0.94),
                (4.8, 0.79), (8.0, 0.70), (6.0, 0.90)):
            top = max(0.0, y1 - offset)
            left = 0.10 * width_pt
            right = right_fraction * width_pt
            if bottom <= top:
                continue
            crop = image.crop((
                max(0, int(left * sx)), max(0, int(top * sy)),
                min(image.width, int(right * sx)),
                min(image.height, int(bottom * sy)),
            ))
            if crop.width < 20 or crop.height < 8:
                continue
            factor = min(
                6, max(1, int(4000 / max(1, crop.width, crop.height))))
            crop = crop.resize((crop.width * factor, crop.height * factor))
            import tempfile
            from src.ingest.ocr import win_ocr_layout
            try:
                with tempfile.TemporaryDirectory(prefix="csc429_tail_") as tmp:
                    target = Path(tmp) / "tail.png"
                    crop.save(target)
                    payload = win_ocr_layout(target)
            except Exception:
                continue
            for recovered in payload.get("lines", []):
                value = str(recovered.get("text", "")).strip()
                value = re.sub(r"[_*]+", "", value)
                value = re.sub(
                    r"\(?\s*[0-9OIlSs]{1,2}\s*marks?\s*\)?", "", value,
                    flags=re.I).strip()
                if value and not MARK_LINE_RE.match(value):
                    recovered_values.append((value, recovered))
            if recovered_values:
                break
        scale_x = (right - left) / crop.width
        scale_y = (bottom - top) / crop.height
        existing = {item["text"].strip() for item in lines + additions}
        for value, recovered in recovered_values:
            if value in existing:
                continue
            words = recovered.get("words") or []
            if not words:
                continue
            rx0 = left + min(word["x"] for word in words) * scale_x
            ry0 = top + min(word["y"] for word in words) * scale_y
            rx1 = left + max(
                word["x"] + word["w"] for word in words) * scale_x
            ry1 = top + max(
                word["y"] + word["h"] for word in words) * scale_y
            if (len(value) >= 20 and rx1 < 0.82 * width_pt):
                continue
            alpha = sum(1 for char in value if char.isalpha())
            if len(value) <= 12:
                if not re.search(r"[.,;:)]$", value):
                    continue
            elif alpha < 0.55 * len(value) or len(value.split()) < 2:
                continue
            additions.append({
                "text": value,
                "bbox": [round(rx0, 2), round(ry0, 2),
                         round(rx1, 2), round(ry1, 2)],
                "recovered": True,
            })
    return lines + additions


def _ocr_layout(page: dict) -> list[dict]:
    image_path = config.PROJECT_ROOT / page["image"]
    payload = win_ocr_layout(image_path)
    width = page["width"]
    height = page["height"]
    page_width, page_height = page["page_points"]
    sx = page_width / width
    sy = page_height / height
    lines = []
    for line in payload.get("lines", []):
        words = line.get("words") or []
        if not words:
            continue
        x0 = min(word["x"] for word in words)
        y0 = min(word["y"] for word in words)
        x1 = max(word["x"] + word["w"] for word in words)
        y1 = max(word["y"] + word["h"] for word in words)
        lines.append({
            "text": str(line.get("text", "")).strip(),
            "bbox": [round(x0 * sx, 2), round(y0 * sy, 2),
                     round(x1 * sx, 2), round(y1 * sy, 2)],
        })
    return [line for line in lines if line["text"]]


def build_layout(force: bool = False) -> dict:
    LAYOUT.mkdir(parents=True, exist_ok=True)
    records = json.loads(REGISTER.read_text(encoding="utf-8"))
    unique = [row for row in records if not row.get("duplicate_of")]
    page_manifests = {}
    for path in PAGES.glob("*/manifest.json"):
        manifest = json.loads(path.read_text(encoding="utf-8"))
        page_manifests[manifest["paper"]] = manifest
    papers = []
    for record in unique:
        source = record["source"]
        page_manifest = page_manifests[source]
        paper_id = page_manifest["paper_id"]
        target = LAYOUT / f"{paper_id}.json"
        if target.exists() and not force:
            papers.append(json.loads(target.read_text(encoding="utf-8")))
            continue
        source_kind = record.get("source_kind", "")
        document = pymupdf.open(str(PAPERS / source))
        pages = []
        try:
            for index, page in enumerate(document):
                if source_kind == "text":
                    lines = _text_layout(page)
                else:
                    lines = _ocr_layout(page_manifest["pages"][index])
                    lines = _repair_truncated_lines(
                        lines, page_manifest["pages"][index],
                        page.rect.width, page.rect.height)
                captions = [
                    line for line in lines if CAPTION_RE.search(line["text"])]
                pages.append({
                    "page": index + 1,
                    "width": round(page.rect.width, 2),
                    "height": round(page.rect.height, 2),
                    "lines": lines,
                    "captions": captions,
                })
        finally:
            document.close()
        payload = {
            "paper": source,
            "paper_id": paper_id,
            "source_kind": source_kind,
            "pages": pages,
            "caption_lines": sum(len(page["captions"]) for page in pages),
        }
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        papers.append(payload)

    summary = {
        "subject": SUBJECT,
        "papers": len(papers),
        "pages": sum(len(paper["pages"]) for paper in papers),
        "lines": sum(len(page["lines"])
                     for paper in papers for page in paper["pages"]),
        "caption_lines": sum(paper["caption_lines"] for paper in papers),
        "recovered_lines": sum(
            1 for paper in papers for page in paper["pages"]
            for line in page["lines"] if line.get("recovered")),
        "layout_files": [
            str((LAYOUT / f"{paper['paper_id']}.json")
                .relative_to(config.PROJECT_ROOT))
            for paper in papers
        ],
    }
    (TRACKING / "layout_manifest.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build_layout(args.force), indent=2))


if __name__ == "__main__":
    main()
