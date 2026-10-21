"""List/check the public Cloudflare bundle candidates.

Phase 1 scope: declare the subject-aware allowlist, expand existing static
files, and fail on forbidden paths. The document entries are produced later by
the PUBLIC_BUILD bundle builder.
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

# public destination -> source file
STATIC_FILES = {
    "index.html": "design/mockups/index.html",
    "subject-csc662.html": "design/mockups/subject-csc662.html",
    "library.html": "design/mockups/library.html",
    "generate.html": "design/mockups/generate.html",
    "gallery.html": "design/mockups/gallery.html",
    "paused.html": "design/mockups/paused.html",
    "assets/style.css": "design/mockups/style.css",
    "assets/htmx.min.js": "src/app/static/htmx.min.js",
}
DYNAMIC_TAIL = [
    ("library/manifest.json", "subject index generated from the registry"),
    ("static/gallery-shell.html", "generated gallery shell; ids resolved at runtime"),
]
FORBIDDEN_PREFIXES = (
    "data/", "CSC662/", "outputs/", "tests/", "src/", "private/",
    ".env", "wrangler", "design/",
)


def _public_filename(subject: str, seed: int, year: int, scheme: bool,
                     ext: str) -> str:
    suffix = " - Marking Scheme" if scheme else ""
    return f"{subject} Seed {seed:02d} {year}{suffix}.{ext}"


def build_manifest() -> list[dict]:
    year = datetime.now(timezone.utc).year
    entries: list[dict] = []
    for public, source in STATIC_FILES.items():
        p = ROOT / source
        entries.append({
            "path": public, "source": source,
            "status": "present" if p.exists() else "missing",
        })
    subjects = load_subjects()
    for code, subject in subjects.items():
        entries.append({
            "path": f"subjects/{code}/subject.json",
            "source": ("generated from registry; public-safe fields only"
                       if subject.available else
                       "generated from registry coming_soon stub"),
            "status": "planned",
        })
        if not subject.available:
            continue
        entries.append({
            "path": f"library/{code}/manifest.json",
            "source": "generated from public Library metadata",
            "status": "planned",
        })
        # 20 seeds x paper/scheme x docx/pdf, generated at bundle time.
        for seed in range(1, 21):
            for scheme in (False, True):
                for ext in ("docx", "pdf"):
                    name = _public_filename(code, seed, year, scheme, ext)
                    folder = "schemes" if scheme else "papers"
                    source = ("PUBLIC_BUILD output; quote-free scheme"
                              if scheme else "PUBLIC_BUILD output")
                    entries.append({
                        "path": f"library/{code}/{folder}/{name}",
                        "source": source,
                        "status": "generated",
                    })
    for public, note in DYNAMIC_TAIL:
        entries.append({"path": public, "source": note, "status": "planned"})
    return entries


def errors(entries: list[dict]) -> list[str]:
    out = []
    for e in entries:
        path = e["path"]
        if any(path.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
            out.append(f"forbidden public path: {path}")
        if e["status"] == "missing":
            out.append(f"missing source for {path}: {e['source']}")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true",
                    help="write cloudflare/public_bundle_manifest.txt")
    args = ap.parse_args()
    entries = build_manifest()
    errs = errors(entries)
    for e in entries:
        e["url"] = quote(e["path"], safe="/")
        print(f"{e['status']:10} {e['path']}  <- {e['source']}")
    print(f"\n{len(entries)} entries; {len(errs)} forbidden/missing")
    if args.write:
        out = ROOT / "cloudflare" / "public_bundle_manifest.txt"
        out.parent.mkdir(exist_ok=True)
        out.write_text("\n".join(
            f"{e['status']:10} {e['path']}  <- {e['source']}"
            for e in entries) + "\n", encoding="utf-8")
        (ROOT / "cloudflare" / "public_bundle_manifest.json").write_text(
            json.dumps(entries, indent=2), encoding="utf-8")
        print(f"wrote {out}")
    if errs:
        for err in errs:
            print("ERROR:", err, file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
