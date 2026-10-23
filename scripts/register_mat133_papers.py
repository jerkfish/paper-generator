"""Read MAT133 paper covers and propose/perform subject-month-year renames.

Text-layer PDFs are read directly. Scanned covers are OCR'd with the Windows
WinRT engine. The register is written to data/tracking/mat133/papers_register.json
before any file is renamed; pass --apply to rename.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import pymupdf

from src.ingest.ocr import MONTHS, decode_offset_text, normalize_month, ocr_pdf

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "data" / "papers" / "MAT133"
OUT = ROOT / "data" / "tracking" / "mat133" / "papers_register.json"
MONTH_ALIASES = {
    "JAN": "JANUARY", "FEB": "FEBRUARY", "MAR": "MARCH", "APR": "APRIL",
    "MAY": "MAY", "JUN": "JUNE", "JUL": "JULY", "AUG": "AUGUST",
    "SEP": "SEPTEMBER", "SEPT": "SEPTEMBER", "OCT": "OCTOBER",
    "NOV": "NOVEMBER", "DEC": "DECEMBER", "FEBRUARI": "FEBRUARY",
}


def cover_text(path: Path) -> tuple[str, str]:
    doc = pymupdf.open(str(path))
    try:
        raw = doc[0].get_text()
    finally:
        doc.close()
    text = decode_offset_text(raw)
    if len(text.strip()) >= 50:
        return text, "text"
    return ocr_pdf(path, pages=[0]), "ocr"


def parse_metadata(text: str) -> dict:
    norm = " ".join(text.split()).replace("FEBRUARI", "FEBRUARY")
    # Prefer the CS/<MONTH> <YEAR>/<CODE> reference line.
    ref = re.search(
        r"CS\s*[/|]\s*([A-Z]{3,9})\s*[ ]?(20\d{2})\s*[/|]\s*(MAT\s*1\d\d(?:\s*/\s*1\d\d)?)",
        norm, re.I)
    month = year = code = None
    if ref:
        month = MONTH_ALIASES.get(ref.group(1).upper(), normalize_month(ref.group(1)))
        year = int(ref.group(2))
        code = re.sub(r"\s+", "", ref.group(3).upper())
    if not month or not year:
        m = re.search(r"\b(" + "|".join(MONTHS) + r")\s+(20\d{2})\b", norm, re.I)
        if m:
            month, year = normalize_month(m.group(1)), int(m.group(2))
    if not year:
        m = re.search(r"\b(20\d{2})\b", norm)
        if m:
            year = int(m.group(1))
    if not code:
        m = re.search(r"\bMAT\s*1\d\d(?:\s*/\s*1\d\d)?\b", norm, re.I)
        if m:
            code = re.sub(r"\s+", "", m.group(0).upper())
    return {"course_code": code, "month": month, "year": year,
            "reference_line": ref.group(0) if ref else None}


def build() -> list[dict]:
    rows = []
    cache_path = OUT.parent / "cover_text.json"
    cache = {}
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            cache = {}
    for path in sorted(PAPERS.iterdir()):
        if path.suffix.lower() != ".pdf":
            continue
        try:
            digest = hashlib.md5(path.read_bytes()).hexdigest()
            if digest in cache:
                text, source = cache[digest]["text"], cache[digest]["source"]
            else:
                text, source = cover_text(path)
                cache[digest] = {"text": text, "source": source}
        except Exception as error:
            rows.append({"source": path.name, "error": str(error)})
            continue
        meta = parse_metadata(text)
        rows.append({
            "source": path.name,
            "source_kind": source,
            "course_code": meta["course_code"],
            "month": meta["month"],
            "year": meta["year"],
            "reference_line": meta["reference_line"],
            "md5": digest,
            "pages": len(pymupdf.open(str(path))),
            "preview": " ".join(text.split())[:300],
        })
    cache_path.write_text(json.dumps(cache, indent=2, ensure_ascii=False),
                          encoding="utf-8")
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    rows = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    for row in rows:
        print(row)
    if not args.apply:
        print(f"wrote {OUT}; no files renamed (pass --apply)")
        return
    used: set[str] = set()
    for row in rows:
        if row.get("error") or not row.get("month") or not row.get("year"):
            print("SKIP", row.get("source"), row.get("error") or "missing month/year")
            continue
        base = f"MAT133 {row['month']} {row['year']}"
        name = base + ".pdf"
        n = 2
        while name.lower() in used or (PAPERS / name).exists():
            name = f"{base} ({n}).pdf"
            n += 1
        used.add(name.lower())
        src = PAPERS / row["source"]
        dst = PAPERS / name
        if src != dst:
            src.rename(dst)
            print(f"RENAME {src.name} -> {name}")


if __name__ == "__main__":
    main()
