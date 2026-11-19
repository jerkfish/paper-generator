"""V0/V1 paper register for the MAT133 playbook-v2 migration.

The register is rebuilt from the working copies under ``data/papers/MAT133``.
The supplied originals are never modified.  Duplicate files are byte-identical
copies; only the canonical file is extracted.

Run:
    uv run python -m src.subjects.mat133.papers
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pymupdf

from src import config

SUBJECT = "MAT133"
MONTHS = {
    "JANUARY": "JAN", "FEBRUARY": "FEB", "MARCH": "MAR", "APRIL": "APR",
    "MAY": "MAY", "JUNE": "JUN", "JULY": "JUL", "AUGUST": "AUG",
    "SEPTEMBER": "SEP", "OCTOBER": "OCT", "NOVEMBER": "NOV", "DECEMBER": "DEC",
}
NAME_RE = re.compile(
    r"^MAT133\s+([A-Z]+)\s+((?:19|20)\d{2})(?:\s+\((\d+)\))?\.pdf$", re.I)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_name(path: Path) -> dict:
    match = NAME_RE.match(path.name)
    if not match:
        return {"month": "", "year": 0, "month_short": "",
                "paper_id": f"{SUBJECT}-UNKNOWN-{sha256_file(path)[:8]}"}
    month = match.group(1).upper()
    year = int(match.group(2))
    short = MONTHS.get(month, month[:3])
    return {
        "month": month,
        "year": year,
        "month_short": short,
        "paper_id": f"{SUBJECT}-{year}-{short}",
    }


def _cover_text(path: Path) -> str:
    with pymupdf.open(str(path)) as pdf:
        if not len(pdf):
            return ""
        return " ".join(pdf[0].get_text().split())[:1500]


def register(papers_dir: Path, tracking: Path) -> dict:
    papers_dir = Path(papers_dir)
    files = sorted(path for path in papers_dir.glob("*.pdf")
                   if path.is_file())
    rows: list[dict] = []
    for path in files:
        parsed = parse_name(path)
        with pymupdf.open(str(path)) as pdf:
            pages = len(pdf)
        rows.append({
            "file": path.name,
            "path": str(path),
            "sha256": sha256_file(path),
            "pages": pages,
            **parsed,
            "cover_text": _cover_text(path),
        })
    by_hash: dict[str, list[dict]] = {}
    for row in rows:
        by_hash.setdefault(row["sha256"], []).append(row)
    duplicate_groups = []
    for sha256, members in by_hash.items():
        if len(members) < 2:
            continue
        ordered = sorted(
            members, key=lambda row: ("(" in row["file"], row["file"]))
        canonical = ordered[0]
        duplicate_groups.append({
            "sha256": sha256,
            "canonical": canonical["file"],
            "duplicates": [row["file"] for row in ordered[1:]],
        })
    for row in rows:
        group = next((group for group in duplicate_groups
                      if group["sha256"] == row["sha256"]), None)
        row["duplicate_group"] = group["canonical"] if group else ""
        row["is_duplicate"] = bool(group and group["canonical"] != row["file"])
    unique = []
    for sha256, members in sorted(
            by_hash.items(),
            key=lambda pair: sorted(
                pair[1], key=lambda row: ("(" in row["file"],
                                          row["file"]))[0]["file"]):
        row = sorted(
            members, key=lambda row: ("(" in row["file"], row["file"]))[0]
        unique.append({
            "paper_id": row["paper_id"],
            "file": row["file"],
            "sha256": sha256,
            "pages": row["pages"],
            "month": row["month"],
            "year": row["year"],
            "month_short": row["month_short"],
        })
    summary = {
        "subject": SUBJECT,
        "papers_dir": str(papers_dir),
        "total": len(rows),
        "unique": len(unique),
        "duplicates": len(rows) - len(unique),
        "pages_total": sum(row["pages"] for row in rows),
        "pages_unique": sum(row["pages"] for row in unique),
        "duplicate_groups": duplicate_groups,
        "unknown_names": [row["file"] for row in rows
                          if not row["month"]],
    }
    payload = {
        "schema_version": 2,
        "subject": SUBJECT,
        "generated_on": "2026-11-14",
        "originals_note": (
            "Working copies under data/papers/MAT133; supplied originals "
            "remain read-only."),
        "papers": rows,
        "unique_papers": unique,
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
    tracking = config.TRACKING_DIR / "mat133" / "v2"
    summary = register(config.PAPERS_ROOT / SUBJECT, tracking)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
