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
