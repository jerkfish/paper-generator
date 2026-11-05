"""Shared stage-1 paper preprocessing.

Every subject uses the same working-copy rules:

- only ``data/papers/<CODE>/`` may be touched; originals are never modified;
- the cover is read from the PDF text layer, or OCR'd when no text exists;
- duplicates are detected by SHA-256 and reported, never silently deleted;
- the register is written before any rename;
- ``--apply-rename`` is opt-in and uses ``<CODE> <MONTH> <YEAR>.pdf``.

Run:

    uv run python -m src.subjects.preprocess --subject CSC402 --register --corpus
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import pymupdf

from src import config
from src.ingest.ocr import MONTHS, decode_offset_text, normalize_month, ocr_pdf

MONTH_ALIASES = {
    "JAN": "JANUARY", "FEB": "FEBRUARY", "FEBRUARI": "FEBRUARY",
    "MAR": "MARCH", "APR": "APRIL", "JUN": "JUNE", "JUL": "JULY",
    "AUG": "AUGUST", "SEP": "SEPTEMBER", "SEPT": "SEPTEMBER",
    "OCT": "OCTOBER", "NOV": "NOVEMBER", "DEC": "DECEMBER",
}
MONTH_PATTERN = "|".join(sorted(
    set(MONTHS) | set(MONTH_ALIASES), key=len, reverse=True))


def require_working_copies(path: Path) -> Path:
    """Refuse to operate outside ``data/papers``."""
    path = Path(path).resolve()
    root = Path(config.PAPERS_ROOT).resolve()
    if path != root and root not in path.parents:
        raise SystemExit(
            f"refusing to modify {path}: stage 1 only works on working copies "
            f"under {root}; originals are read-only")
    return path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cover_text(path: Path, ocr: bool = True) -> tuple[str, str]:
    doc = pymupdf.open(str(path))
    try:
        raw = doc[0].get_text()
    finally:
        doc.close()
    text = decode_offset_text(raw)
    if len(text.strip()) >= 50:
        return text, "text"
    if not ocr:
        return text, "none"
    return ocr_pdf(path, pages=[0]), "ocr"


def _code_pattern(code: str) -> re.Pattern | None:
    match = re.fullmatch(r"([A-Z]+)(\d+)", code.upper())
    if not match:
        return None
    return re.compile(
        rf"\b{re.escape(match.group(1))}\s*{re.escape(match.group(2))}\b",
        re.I)


def parse_cover(text: str, subject: str) -> dict:
    norm = " ".join((text or "").split())
    norm = re.sub(r"\bFEBRUARI\b", "FEBRUARY", norm, flags=re.I)
    code = subject.upper()
    found_code = bool(
        re.search(rf"\b{re.escape(code)}\b", norm, re.I))
    if not found_code:
        pattern = _code_pattern(code)
        found_code = bool(pattern and pattern.search(norm))
    month = None
    year = None
    reference = None
    # Common UTM cover forms: CS/JUNE 2024/CSC402 or CSC402 JUNE 2024.
    ref = re.search(
        rf"(?:CS\s*[/|]\s*)?({MONTH_PATTERN})\s*[ ]?(20\d{{2}})",
        norm, re.I)
    if ref:
        month = MONTH_ALIASES.get(ref.group(1).upper(),
                                  normalize_month(ref.group(1)))
        if month not in MONTHS:
            month = None
        year = int(ref.group(2))
        reference = ref.group(0)
    if year is None:
        match = re.search(r"\b(20\d{2})\b", norm)
        year = int(match.group(1)) if match else None
    confidence = "high" if found_code and month and year else (
        "medium" if month and year else "low")
    return {
        "course_code_found": found_code,
        "code": code if found_code else "",
        "month": month,
        "year": year,
        "confidence": confidence,
        "reference_line": reference,
    }


def extract_text(path: Path, ocr: bool = True) -> tuple[str, str]:
    doc = pymupdf.open(str(path))
    try:
        parts = [decode_offset_text(page.get_text()) for page in doc]
        joined = "\n".join(parts)
        page_count = len(doc)
    finally:
        doc.close()
    if len(joined.strip()) >= 100:
        return joined, "text"
    if not ocr:
        return joined, "none"
    return ocr_pdf(path, pages=list(range(page_count))), "ocr"


def scan_papers(papers_dir: Path, subject: str,
                ocr: bool = True) -> tuple[list[dict], dict]:
    papers_dir = require_working_copies(papers_dir)
    files = sorted(path for path in papers_dir.glob("*.pdf")
                   if path.is_file())
    rows = []
    by_hash: dict[str, dict] = {}
    for path in files:
        try:
            digest = sha256_file(path)
            text, source = cover_text(path, ocr=ocr)
            parsed = parse_cover(text, subject)
            doc = pymupdf.open(str(path))
            try:
                pages = len(doc)
            finally:
                doc.close()
        except Exception as error:
            rows.append({"source": path.name, "error": str(error)})
            continue
        row = {
            "source": path.name,
            "sha256": digest,
            "pages": pages,
            "source_kind": source,
            "course_code_found": parsed["course_code_found"],
            "month": parsed["month"],
            "year": parsed["year"],
            "confidence": parsed["confidence"],
            "reference_line": parsed["reference_line"],
            "cover_text": text[:4000],
            "preview": " ".join(text.split())[:300],
            "duplicate_of": "",
        }
        canonical = by_hash.get(digest)
        if canonical is not None:
            row["duplicate_of"] = canonical["source"]
        else:
            by_hash[digest] = row
        rows.append(row)
    return rows, {"unique_hashes": len(by_hash), "total": len(rows)}


def _unique_target(rows: list[dict], row: dict, used: set[str]) -> str:
    month = row.get("month")
    year = row.get("year")
    subject = row.get("_subject", "")
    if not month or not year:
        return row["source"]
    base = f"{subject} {month} {year}"
    name = f"{base}.pdf"
    number = 2
    while name.lower() in used:
        name = f"{base} ({number}).pdf"
        number += 1
    used.add(name.lower())
    return name


def apply_renames(rows: list[dict], papers_dir: Path, subject: str,
                  apply: bool) -> list[dict]:
    """Return rows with canonical names; rename only when ``apply`` is true."""
    papers_dir = require_working_copies(papers_dir)
    used: set[str] = set()
    mapping: dict[str, str] = {}
    for row in rows:
        if row.get("error"):
            continue
        row["_subject"] = subject.upper()
        old_source = row["source"]
        target = _unique_target(rows, row, used)
        row["proposed_name"] = target
        if apply:
            mapping[old_source] = target
            if target != old_source:
                source = papers_dir / old_source
                destination = papers_dir / target
                if not destination.exists() or source == destination:
                    source.rename(destination)
            row["source"] = target
        else:
            mapping[old_source] = old_source
            row["source"] = old_source
    for row in rows:
        if row.get("duplicate_of"):
            row["duplicate_of"] = mapping.get(row["duplicate_of"],
                                              row["duplicate_of"])
    for row in rows:
        row.pop("_subject", None)
    return rows


def write_corpus(rows: list[dict], papers_dir: Path,
                 tracking_dir: Path, ocr: bool = True) -> list[dict]:
    papers_dir = require_working_copies(papers_dir)
    text_dir = tracking_dir / "paper_text"
    text_dir.mkdir(parents=True, exist_ok=True)
    index = []
    canonical_text: dict[str, str] = {}
    # Extract unique papers first so a duplicate that sorts before its
    # canonical file still reuses the canonical text.
    for row in rows:
        if row.get("error") or row.get("duplicate_of"):
            continue
        source = papers_dir / row["source"]
        text, kind = (extract_text(source, ocr=ocr) if source.exists()
                      else ("", "missing"))
        canonical_text[row["source"]] = text
        target = text_dir / (Path(row["source"]).stem + ".txt")
        target.write_text(text, encoding="utf-8")
        index.append({"paper": row["source"], "chars": len(text),
                      "source": kind, "text_file": str(target)})
    for row in rows:
        if row.get("error") or not row.get("duplicate_of"):
            continue
        text = canonical_text.get(row["duplicate_of"], "")
        target = text_dir / (Path(row["source"]).stem + ".txt")
        target.write_text(text, encoding="utf-8")
        index.append({"paper": row["source"], "chars": len(text),
                      "source": "duplicate", "text_file": str(target)})
    (text_dir / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    return index


def register(subject: str, papers_dir: Path | None = None,
             tracking_dir: Path | None = None, apply_rename: bool = False,
             corpus: bool = False, ocr: bool = True,
             assets: bool = False) -> dict:
    code = subject.upper()
    papers_dir = require_working_copies(
        papers_dir or config.subject_papers_dir(code))
    tracking_dir = Path(tracking_dir or
                        config.TRACKING_DIR / code.lower())
    tracking_dir.mkdir(parents=True, exist_ok=True)
    rows, scan = scan_papers(papers_dir, code, ocr=ocr)
    rows = apply_renames(rows, papers_dir, code, apply=apply_rename)
    unique = [row for row in rows if not row.get("duplicate_of")]
    summary = {
        "subject": code,
        "papers_dir": str(papers_dir),
        "total": scan["total"],
        "unique": len(unique),
        "duplicates": scan["total"] - len(unique),
        "duplicate_groups": [
            {"canonical": row["source"],
             "duplicates": [other["source"] for other in rows
                            if other.get("duplicate_of") == row["source"]]}
            for row in unique
            if any(other.get("duplicate_of") == row["source"]
                   for other in rows)
        ],
        "month_year_found": sum(1 for row in unique
                                if row.get("month") and row.get("year")),
        "low_confidence": [row["source"] for row in unique
                           if row.get("confidence") != "high"],
        "renamed": bool(apply_rename),
        "ocr": bool(ocr),
    }
    (tracking_dir / "papers_register.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    (tracking_dir / "papers_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    covers = {row.get("sha256", row["source"]): {
        "text": row.get("cover_text", row.get("preview", "")),
        "source": row.get("source_kind", ""),
    } for row in rows if not row.get("error")}
    (tracking_dir / "cover_text.json").write_text(
        json.dumps(covers, indent=2, ensure_ascii=False), encoding="utf-8")
    if corpus:
        summary["corpus"] = write_corpus(rows, papers_dir, tracking_dir,
                                         ocr=ocr)
        (tracking_dir / "papers_summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False),
            encoding="utf-8")
    if assets:
        from src.subjects import plugins
        from src.subjects.registry import get_subject

        record = get_subject(code)
        capture = plugins.plugin_for(record, "stage1_assets")
        if capture is None:
            raise SystemExit(
                f"{code}: no stage1_assets plugin in subject.json")
        summary["assets"] = capture(
            subject=code, papers_dir=papers_dir,
            tracking_dir=tracking_dir, rows=rows, summary=summary, ocr=ocr)
        (tracking_dir / "papers_summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False),
            encoding="utf-8")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject", required=True)
    ap.add_argument("--papers", default="")
    ap.add_argument("--tracking", default="")
    ap.add_argument("--register", action="store_true",
                    help="write papers_register.json and summary")
    ap.add_argument("--corpus", action="store_true",
                    help="write paper_text/*.txt and index.json")
    ap.add_argument("--apply-rename", action="store_true",
                    help="rename working copies by cover; off by default")
    ap.add_argument("--no-ocr", action="store_true")
    ap.add_argument("--assets", action="store_true",
                    help="run the subject's stage1_assets plugin after register")
    args = ap.parse_args()
    if args.assets:
        args.register = True
    papers = Path(args.papers) if args.papers else None
    tracking = Path(args.tracking) if args.tracking else None
    if not args.register and not args.corpus:
        rows, scan = scan_papers(
            papers or config.subject_papers_dir(args.subject),
            args.subject, ocr=not args.no_ocr)
        print(json.dumps({"scan": scan, "papers": rows}, indent=2))
        return
    summary = register(args.subject, papers_dir=papers,
                       tracking_dir=tracking,
                       apply_rename=args.apply_rename,
                       corpus=args.corpus, ocr=not args.no_ocr,
                       assets=args.assets)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
