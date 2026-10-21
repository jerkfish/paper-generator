"""Download names and Content-Disposition headers.

Every download uses the same public name regardless of where the file was
built (fresh job, Library, or a shared gallery paper):

    {SUBJECT} Seed {SEED} {YEAR}.docx/.pdf
    {SUBJECT} Seed {SEED} {YEAR} - Marking Scheme.docx/.pdf

Practice mode adds `` (practice N)`` before the extension.  ``YEAR`` is the
UTC year of generation.  The header carries an ASCII fallback plus the
RFC 5987 ``filename*`` form.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from urllib.parse import quote

VALID_EXTENSIONS = {"docx", "pdf"}


def utc_year(timestamp: float | None = None) -> int:
    if timestamp is None:
        return datetime.now(timezone.utc).year
    return datetime.fromtimestamp(float(timestamp), timezone.utc).year


def download_filename(subject: str, seed: int, year: int, ext: str,
                      scheme: bool = False,
                      practice_marks: int | None = None) -> str:
    """Build the user-facing filename (without any folder)."""
    subject = str(subject).strip().upper()
    if not re.fullmatch(r"[A-Z0-9]+", subject):
        raise ValueError("subject code must be letters and digits")
    seed = int(seed)
    if seed < 1:
        raise ValueError("seed must be a positive integer")
    year = int(year)
    if not 1000 <= year <= 9999:
        raise ValueError("year must be a four-digit UTC year")
    ext = str(ext).lower().lstrip(".")
    if ext not in VALID_EXTENSIONS:
        raise ValueError(f"extension must be one of {sorted(VALID_EXTENSIONS)}")
    base = f"{subject} Seed {seed:02d} {year}"
    if scheme:
        base += " - Marking Scheme"
    if practice_marks is not None:
        marks = int(practice_marks)
        if marks < 0:
            raise ValueError("practice computed marks cannot be negative")
        base += f" (practice {marks})"
    return f"{base}.{ext}"


def _ascii_fallback(name: str) -> str:
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    text = text.replace("\r", " ").replace("\n", " ")
    text = text.replace("\\", "_").replace('"', "'")
    return text or "download"


def content_disposition(name: str) -> str:
    """RFC 6266 header with both ``filename`` and ``filename*``."""
    ascii_name = _ascii_fallback(name)
    return (f'attachment; filename="{ascii_name}"; '
            f"filename*=UTF-8''{quote(name, safe='')}")


def url_path(name: str) -> str:
    """Percent-encode a path segment so spaces and parentheses are safe."""
    return quote(name, safe="")
