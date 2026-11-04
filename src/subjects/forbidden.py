"""Shared forbidden-token scan for subject deliverables.

Catches private paths, another subject's code, secret markers and any
subject-specific tokens declared in ``capabilities.forbidden_tokens``.  It is
used at every lifecycle gate before a document is cached or published.
"""
from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

import docx
import pymupdf

from src import config
from src.subjects.registry import SubjectNotFound, get_subject, load_subjects

GENERIC_TOKENS = (
    "data/reference",
    "data/papers",
    "outputs/web_cache",
    "outputs/web_runs",
    ".env",
    "wrangler.toml",
    "BEGIN PRIVATE KEY",
    "C:\\Users\\",
)


def forbidden_tokens(subject: str,
                     root: Path | None = None) -> list[str]:
    code = subject.upper()
    tokens = list(GENERIC_TOKENS)
    try:
        subjects = load_subjects(root)
    except Exception:
        subjects = {}
    for other in subjects:
        if other != code:
            tokens.append(other)
    try:
        record = get_subject(code, root)
        tokens.extend(str(token) for token in
                      record.capabilities.get("forbidden_tokens") or [])
    except SubjectNotFound:
        pass
    return sorted(set(tokens))


def _docx_text(path: Path) -> str:
    document = docx.Document(str(path))
    parts = [p.text for p in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                parts.append(cell.text)
    for section in document.sections:
        for part in (section.header, section.footer,
                     section.first_page_header, section.first_page_footer):
            try:
                parts.extend(p.text for p in part.paragraphs)
            except Exception:
                continue
    return "\n".join(parts)


def scan_path(path: Path, tokens: list[str]) -> list[dict]:
    path = Path(path)
    if not path.is_file():
        return [{"path": str(path), "error": "missing"}]
    suffix = path.suffix.lower()
    try:
        if suffix == ".docx":
            text = _docx_text(path)
        elif suffix == ".pdf":
            with pymupdf.open(str(path)) as pdf:
                text = "\n".join(page.get_text() for page in pdf)
        elif suffix in {".txt", ".md", ".json", ".html", ".css", ".js"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
        else:
            return [{"path": str(path), "error": "unsupported file type"}]
    except Exception as error:
        return [{"path": str(path), "error": str(error)}]
    hits = []
    for token in tokens:
        if token and token in text:
            hits.append({"path": str(path), "token": token})
    return hits


def scan(paths: list[Path], subject: str,
         root: Path | None = None) -> dict:
    tokens = forbidden_tokens(subject, root)
    hits = []
    for path in paths:
        hits.extend(scan_path(path, tokens))
    return {"subject": subject.upper(), "tokens": tokens,
            "files": [str(path) for path in paths], "hits": hits}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject", required=True)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--root", default=str(config.PROJECT_ROOT),
                    help=argparse.SUPPRESS)
    args = ap.parse_args()
    result = scan([Path(path) for path in args.paths], args.subject,
                  Path(args.root).resolve())
    print(json.dumps(result, indent=2))
    if result["hits"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
