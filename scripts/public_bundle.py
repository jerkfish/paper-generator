"""List/check the public Cloudflare bundle.

The allowlist is explicit; nothing is copied by excluding from a larger tree.
Pages are rendered from the app templates by
``scripts/build_public_bundle.py`` and the documents are PUBLIC_BUILD copies.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.subjects.registry import load_subjects

BUNDLE_DIR = ROOT / "outputs" / "public_bundle"
STATIC_PATHS = (
    "index.html",
    "csc662/index.html",
    "csc662/library/index.html",
    "csc662/generate/index.html",
    "gallery/index.html",
    "paused/index.html",
    "static/gallery-shell.html",
    "assets/style.css",
    "assets/htmx.min.js",
    "assets/library.js",
    "assets/gallery.js",
)
FORBIDDEN_PREFIXES = (
    "data/", "CSC662/", "outputs/", "tests/", "src/", "private/",
    ".env", "wrangler", "design/",
)


def _public_filename(subject: str, seed: int, year: int, scheme: bool,
                     ext: str) -> str:
    suffix = " - Marking Scheme" if scheme else ""
    return f"{subject} Seed {seed:02d} {year}{suffix}.{ext}"


def _status(relative: str, default: str = "generated") -> str:
    return "present" if (BUNDLE_DIR / relative).is_file() else default


def build_manifest() -> list[dict]:
    year = datetime.now(timezone.utc).year
    entries: list[dict] = []
    for path in STATIC_PATHS:
        entries.append({
            "path": path,
            "source": ("generated from app templates"
                       if path.endswith(".html")
                       else "copied from src/app/static"),
            "status": _status(path),
        })
    subjects = load_subjects()
    for code, subject in subjects.items():
        rel = f"subjects/{code}/subject.json"
        entries.append({
            "path": rel,
            "source": ("generated from registry; public-safe fields only"
                       if subject.available else
                       "generated from registry coming_soon stub"),
            "status": _status(rel),
        })
        if not subject.available:
            continue
        for name in ("library/manifest.json",
                     f"library/{code}/manifest.json"):
            entries.append({
                "path": name,
                "source": "generated from public Library metadata",
                "status": _status(name),
            })
        for seed in range(1, 21):
            for scheme in (False, True):
                for ext in ("docx", "pdf"):
                    name = _public_filename(code, seed, year, scheme, ext)
                    folder = "schemes" if scheme else "papers"
                    rel = f"library/{code}/{folder}/{name}"
                    entries.append({
                        "path": rel,
                        "source": ("PUBLIC_BUILD output; quote-free scheme"
                                   if scheme else "PUBLIC_BUILD output"),
                        "status": _status(rel),
                    })
    return entries


def errors(entries: list[dict]) -> list[str]:
    out = []
    for entry in entries:
        path = entry["path"]
        if any(path.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
            out.append(f"forbidden public path: {path}")
        if entry["status"] == "missing":
            out.append(f"missing source for {path}: {entry['source']}")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true",
                    help="write cloudflare/public_bundle_manifest.txt")
    args = ap.parse_args()
    entries = build_manifest()
    for entry in entries:
        entry["url"] = quote(entry["path"], safe="/")
        print(f"{entry['status']:10} {entry['path']}  <- {entry['source']}")
    problems = errors(entries)
    print(f"\n{len(entries)} entries; {len(problems)} forbidden/missing")
    if args.write:
        out = ROOT / "cloudflare" / "public_bundle_manifest.txt"
        out.parent.mkdir(exist_ok=True)
        out.write_text("\n".join(
            f"{e['status']:10} {e['path']}  <- {e['source']}"
            for e in entries) + "\n", encoding="utf-8")
        (ROOT / "cloudflare" / "public_bundle_manifest.json").write_text(
            json.dumps(entries, indent=2), encoding="utf-8")
        print(f"wrote {out}")
    if problems:
        for problem in problems:
            print("ERROR:", problem, file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
