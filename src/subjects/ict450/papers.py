"""V1 paper register for the ICT450 pilot.

Hashes and page counts are derived from the working copies.  A month/year is
taken from the PDF text layer when the cover has one; scanned covers fall back
to the v1 OCR hint and are marked provisional until MinerU confirms them.

Run:
    uv run python -m src.subjects.ict450.papers
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pymupdf

from src import config

SUBJECT = "ICT450"
MONTHS = {
    "JAN": "JAN", "JANUARY": "JAN", "FEB": "FEB", "FEBRUARY": "FEB",
    "MAR": "MAR", "MARCH": "MAR", "APR": "APR", "APRIL": "APR",
    "MAY": "MAY", "JUN": "JUN", "JUNE": "JUN", "JUL": "JUL",
    "JULY": "JUL", "AUG": "AUG", "AUGUST": "AUG", "SEP": "SEP",
    "SEPT": "SEP", "SEPTEMBER": "SEP", "OCT": "OCT", "OCTOBER": "OCT",
    "NOV": "NOV", "NOVEMBER": "NOV", "DEC": "DEC", "DECEMBER": "DEC",
}
MONTH_YEAR_RE = re.compile(
    r"\b(" + "|".join(sorted(MONTHS, key=len, reverse=True)) +
    r")\.?\s+((?:19|20)\d{2})\b", re.I)

# v1 OCR hints for covers without a text layer.  Provisional only; MinerU
# extraction must confirm each month before Gate A.
V1_HINTS = {
    "ICT450 (1).pdf": "2023-FEB",
    "ICT450 (2).pdf": "2023-JUL",
    "ICT450 (3).pdf": "2024-JAN",
    "ICT450 (4).pdf": "2024-JUL",
    "ICT450 (5).pdf": "2025-FEB",
    "ICT450 (6).pdf": "2025-JUL",
    "ICT450 (7).pdf": "2026-FEB",
    "ICT450.pdf": "2022-FEB",
    "ICT450_ITS432 (1).PDF": "2018-JUN",
    "ICT450_ITS432 (2).PDF": "2018-DEC",
    "ICT450_ITS432 (3).PDF": "2019-DEC",
    "ICT450_ITS432.PDF": "2018-JUN",
    "ITS432_ICT450.PDF": "2019-JUN",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cover_month(text: str) -> str:
    match = MONTH_YEAR_RE.search(text or "")
    if not match:
        return ""
    month = MONTHS[match.group(1).upper().rstrip(".")]
    return f"{match.group(2)}-{month}"


def _paper_id(month_year: str, sha256: str) -> str:
    if month_year:
        return f"{SUBJECT}-{month_year}"
    return f"{SUBJECT}-UNKNOWN-{sha256[:8]}"


def register(papers_dir: Path, tracking: Path) -> dict:
    papers = sorted(Path(papers_dir).glob("*.pdf"))
    papers += sorted(Path(papers_dir).glob("*.PDF"))
    rows: list[dict] = []
    for path in sorted(set(papers)):
        sha256 = sha256_file(path)
        with pymupdf.open(str(path)) as pdf:
            pages = len(pdf)
            first = " ".join(pdf[0].get_text().split()) if pages else ""
        month_year = cover_month(first)
        source = "pdf_text" if month_year else "provisional_v1_ocr"
        if not month_year:
            month_year = V1_HINTS.get(path.name, "")
        rows.append({
            "file": path.name,
            "path": str(path),
            "sha256": sha256,
            "pages": pages,
            "month_year": month_year,
            "month_source": source,
            "paper_id": _paper_id(month_year, sha256),
            "cover_text": first[:1000],
        })
    by_hash: dict[str, list[dict]] = {}
    for row in rows:
        by_hash.setdefault(row["sha256"], []).append(row)
    duplicate_groups = []
    for sha256, members in by_hash.items():
        if len(members) < 2:
            continue
        canonical = members[0]
        duplicate_groups.append({
            "sha256": sha256,
            "canonical": canonical["file"],
            "duplicates": [row["file"] for row in members[1:]],
        })
    for row in rows:
        group = next((group for group in duplicate_groups
                      if group["sha256"] == row["sha256"]), None)
        row["duplicate_group"] = group["canonical"] if group else ""
        row["is_duplicate"] = bool(group and group["canonical"] != row["file"])
    summary = {
        "subject": SUBJECT,
        "papers_dir": str(papers_dir),
        "total": len(rows),
        "unique": len(by_hash),
        "duplicates": len(rows) - len(by_hash),
        "duplicate_groups": duplicate_groups,
        "month_provisional": [row["file"] for row in rows
                              if row["month_source"] != "pdf_text"],
    }
    payload = {
        "schema_version": 2,
        "subject": SUBJECT,
        "generated_on": "2026-11-11",
        "originals_note": "working copies under data/papers/ICT450; read-only",
        "papers": rows,
        "unique_papers": [
            {
                "paper_id": members[0]["paper_id"],
                "file": members[0]["file"],
                "sha256": sha256,
                "pages": members[0]["pages"],
                "month_year": members[0]["month_year"],
                "month_source": members[0]["month_source"],
            }
            for sha256, members in sorted(by_hash.items(),
                                          key=lambda item: item[1][0]["file"])
        ],
    }
    tracking = Path(tracking)
    tracking.mkdir(parents=True, exist_ok=True)
    (tracking / "papers_register.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    (tracking / "papers_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    return summary


def main() -> None:
    tracking = config.TRACKING_DIR / "ict450" / "v2"
    summary = register(config.PAPERS_ROOT / SUBJECT, tracking)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
