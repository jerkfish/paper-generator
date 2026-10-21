"""Extract full text for every MAT133 paper, OCRing scanned pages."""
from __future__ import annotations

import json
from pathlib import Path

import pymupdf

from src.ingest.ocr import decode_offset_text, ocr_pdf

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "data" / "papers" / "MAT133"
OUT = ROOT / "data" / "tracking" / "mat133" / "paper_text"


def extract(path: Path) -> tuple[str, str]:
    doc = pymupdf.open(str(path))
    try:
        parts = []
        for page in doc:
            text = decode_offset_text(page.get_text())
            parts.append(text)
        joined = "\n".join(parts)
        if len(joined.strip()) >= 100:
            return joined, "text"
        pages = list(range(len(doc)))
    finally:
        doc.close()
    return ocr_pdf(path, pages=pages), "ocr"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    index = []
    for path in sorted(PAPERS.glob("*.pdf")):
        target = OUT / (path.stem + ".txt")
        if target.exists() and target.stat().st_size > 200:
            text = target.read_text(encoding="utf-8")
            source = "cache"
        else:
            text, source = extract(path)
            target.write_text(text, encoding="utf-8")
        index.append({"paper": path.name, "chars": len(text),
                      "source": source, "text_file": str(target)})
        print(f"{path.name}: {len(text)} chars ({source})", flush=True)
    (OUT / "index.json").write_text(json.dumps(index, indent=2),
                                    encoding="utf-8")
    print(f"wrote {len(index)} texts")


if __name__ == "__main__":
    main()
