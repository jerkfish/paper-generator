"""Capture every CSC429 source page and its embedded-image metadata.

Stage 1 evidence: each unique paper is rendered at 200 dpi and its embedded
raster image boxes are recorded.  This is a provenance layer; question-level
figure crops are built on top of it later.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pymupdf
from PIL import Image

from src import config

SUBJECT = "CSC429"
TRACKING = config.TRACKING_DIR / "csc429"
PAPERS = config.subject_papers_dir(SUBJECT)
REGISTER = TRACKING / "papers_register.json"
PAGES_DIR = TRACKING / "pages"
MANIFEST = TRACKING / "pages_manifest.json"
MONTHS = {
    "JANUARY": 1, "FEBRUARY": 2, "MARCH": 3, "APRIL": 4, "MAY": 5,
    "JUNE": 6, "JULY": 7, "AUGUST": 8, "SEPTEMBER": 9, "OCTOBER": 10,
    "NOVEMBER": 11, "DECEMBER": 12,
}


def _slug(source: str) -> str:
    stem = Path(source).stem
    value = re.sub(r"[^A-Za-z0-9]+", "_", stem).strip("_")
    return value or "paper"


def _paper_id(record: dict, used: set[str]) -> str:
    year = record.get("year")
    month = MONTHS.get(str(record.get("month", "")).upper())
    base = (f"CSC429-{int(year)}-{month:02d}"
            if year and month else f"CSC429-{_slug(record['source'])}")
    value = base
    suffix = 2
    while value in used:
        value = f"{base}-v{suffix}"
        suffix += 1
    used.add(value)
    return value


def _unique_records() -> list[dict]:
    records = json.loads(REGISTER.read_text(encoding="utf-8"))
    return [row for row in records if not row.get("duplicate_of")]


def capture_pages(dpi: int = 200, force: bool = False) -> dict:
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    papers = []
    used_ids: set[str] = set()
    for record in _unique_records():
        source = record["source"]
        doc_path = PAPERS / source
        paper_id = _paper_id(record, used_ids)
        out_dir = PAGES_DIR / paper_id
        manifest_path = out_dir / "manifest.json"
        if manifest_path.exists() and not force:
            papers.append(json.loads(manifest_path.read_text(encoding="utf-8")))
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        document = pymupdf.open(str(doc_path))
        pages = []
        try:
            for index, page in enumerate(document):
                pix = page.get_pixmap(
                    dpi=dpi, colorspace=pymupdf.csRGB, alpha=False)
                target = out_dir / f"page_{index + 1:03d}.jpg"
                image = Image.frombytes(
                    "RGB", (pix.width, pix.height), pix.samples)
                image.save(target, "JPEG", quality=90, dpi=(dpi, dpi))
                embedded = []
                for item in page.get_images(full=True):
                    xref = item[0]
                    embedded.append({
                        "xref": xref,
                        "width": item[2],
                        "height": item[3],
                        "bbox": [
                            [round(rect.x0, 2), round(rect.y0, 2),
                             round(rect.x1, 2), round(rect.y1, 2)]
                            for rect in page.get_image_rects(xref)
                        ],
                    })
                pages.append({
                    "page": index + 1,
                    "image": str(target.relative_to(config.PROJECT_ROOT)),
                    "width": pix.width,
                    "height": pix.height,
                    "page_points": [round(page.rect.width, 2),
                                    round(page.rect.height, 2)],
                    "embedded_images": embedded,
                    "drawings": len(page.get_drawings()),
                })
        finally:
            document.close()
        record = {
            "paper": source,
            "paper_id": paper_id,
            "month": record.get("month", ""),
            "year": record.get("year"),
            "source_kind": record.get("source_kind", ""),
            "dpi": dpi,
            "page_count": len(pages),
            "pages": pages,
        }
        manifest_path.write_text(
            json.dumps(record, indent=2), encoding="utf-8")
        papers.append(record)

    payload = {
        "subject": SUBJECT,
        "dpi": dpi,
        "papers": len(papers),
        "pages": sum(row["page_count"] for row in papers),
        "paper_manifests": [
            str((PAGES_DIR / row["paper_id"] / "manifest.json")
                .relative_to(config.PROJECT_ROOT))
            for row in papers
        ],
    }
    MANIFEST.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dpi", type=int, default=200)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    print(json.dumps(capture_pages(args.dpi, args.force), indent=2))


if __name__ == "__main__":
    main()
