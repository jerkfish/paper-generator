"""Build the static public bundle for R2.

The builder reads the private Library cache, creates PUBLIC_BUILD copies of
every paper and scheme, renders the public pages and writes the public
manifests.  It never copies private files directly:

- papers are re-branded and re-exported;
- schemes are rebuilt with verbatim slide quotes omitted;
- only public-safe subject fields and Library metadata are written.

Run it without PUBLIC_BUILD=1 (the builder applies the public rules itself):

    uv run python -m scripts.build_public_bundle --out outputs/public_bundle
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import docx
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import config
from src.app.filenames import (download_filename, utc_year)
from src.app.jobs import DEFAULT_SUBJECT, library_item
from src.assemble.build_docx_paper import export_pdf
from src.assemble.generic_build import build_scheme, publicise
from src.planner.planner import TYPE_LABEL
from src.subjects.registry import get_subject, load_subjects

APP_DIR = ROOT / "src" / "app"
TEMPLATES = APP_DIR / "templates"
STATIC = APP_DIR / "static"
SUBJECT = DEFAULT_SUBJECT
SCHEME_MARKER = "[verbatim slide quote omitted in public build]"
PRIVATE_BRAND = "UNIVERSITI TEKNOLOGI MARA"


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


def _pdf_text(path: Path) -> str:
    import pymupdf
    with pymupdf.open(str(path)) as pdf:
        return "\n".join(page.get_text() for page in pdf)


def _check_public_file(path: Path) -> list[str]:
    text = _docx_text(path) if path.suffix.lower() == ".docx" else _pdf_text(path)
    problems = []
    if PRIVATE_BRAND.lower() in text.lower():
        problems.append(f"private branding in {path.name}")
    if "CS/MOCK" in text or "2026/CSC662" in text:
        problems.append(f"private reference code in {path.name}")
    return problems


def _check_scheme(path: Path) -> list[str]:
    problems = _check_public_file(path)
    text = _docx_text(path) if path.suffix.lower() == ".docx" else _pdf_text(path)
    normalised = " ".join(text.split())
    if SCHEME_MARKER not in normalised:
        problems.append(f"quote omission marker missing in {path.name}")
    return problems


def build_documents(out: Path, seeds: list[int], force: bool = False) -> dict:
    papers = out / "library" / SUBJECT / "papers"
    schemes = out / "library" / SUBJECT / "schemes"
    papers.mkdir(parents=True, exist_ok=True)
    schemes.mkdir(parents=True, exist_ok=True)
    plan_dir = config.OUTPUTS_DIR / "eval_final_deepseek"
    built = 0
    skipped = 0
    for seed in seeds:
        item = library_item(seed, SUBJECT)
        if item is None:
            raise SystemExit(f"no cached Library item for seed {seed}")
        plan = plan_dir / f"seed_{seed:02d}_planner.json"
        theory = plan_dir / f"seed_{seed:02d}_theory.json"
        if not plan.exists() or not theory.exists():
            raise SystemExit(f"missing planner/theory JSON for seed {seed}")
        names = item["downloads"]
        paper_docx = papers / names["paper_docx"]
        paper_pdf = papers / names["paper_pdf"]
        scheme_docx = schemes / names["scheme_docx"]
        scheme_pdf = schemes / names["scheme_pdf"]
        if (not force and paper_docx.exists() and paper_pdf.exists()
                and scheme_docx.exists() and scheme_pdf.exists()):
            print(f"seed {seed:02d}: cached bundle files, skipped", flush=True)
            skipped += 1
            continue

        source_docx = Path(item["files"]["paper_docx"])
        if not source_docx.exists():
            raise SystemExit(f"missing private paper DOCX for seed {seed}: "
                             f"{source_docx}")
        print(f"seed {seed:02d}: public paper", flush=True)
        shutil.copy2(source_docx, paper_docx)
        publicise(paper_docx)
        export_pdf(paper_docx, paper_pdf)
        problems = _check_public_file(paper_docx) + _check_public_file(paper_pdf)
        if problems:
            raise SystemExit(f"seed {seed}: " + "; ".join(problems))

        print(f"seed {seed:02d}: public scheme", flush=True)
        build_scheme(source_docx, plan, theory, scheme_docx, scheme_pdf,
                     public=True)
        problems = _check_scheme(scheme_docx) + _check_scheme(scheme_pdf)
        if problems:
            raise SystemExit(f"seed {seed}: " + "; ".join(problems))
        built += 1
    return {"built": built, "skipped": skipped,
            "papers": len(list(papers.glob("*.docx"))),
            "schemes": len(list(schemes.glob("*.docx")))}


def _urls(item: dict) -> dict:
    out = {}
    for kind, name in item["downloads"].items():
        folder = "schemes" if kind.startswith("scheme") else "papers"
        out[kind] = f"/library/{SUBJECT}/{folder}/{quote(name, safe='')}"
    return out


def _render_pages(out: Path, items: list[dict]) -> dict:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    subjects = list(load_subjects().values())
    subject = get_subject(SUBJECT)
    counts = {s.code: 0 for s in subjects}
    counts[SUBJECT] = len(items)
    item_urls = {str(item["seed"]): _urls(item) for item in items}
    topics = sorted({name for item in items
                     for name, marks in item["topic_marks"].items()
                     if int(marks) > 0})
    computed_options = sorted({int(item["computed_display"]) for item in items})
    base = {
        "site_name": config.SITE_NAME,
        "subjects": subjects,
        "public": True,
        "static_bundle": True,
        "library_disabled": False,
        "generate_disabled": True,
        "asset_base": "/assets",
        "contact_email": config.CONTACT_EMAIL,
        "repo_url": config.REPO_URL,
        "cost_cap": config.WEB_COST_CAP_USD,
        "model": config.MOCKGEN_MODEL,
        "has_key": False,
    }

    def render(template: str, **extra) -> str:
        context = dict(base)
        context.update(extra)
        return env.get_template(template).render(**context)

    pages = {
        "index.html": render(
            "index.html", counts=counts),
        f"{subject.route}/index.html": render(
            "subject.html", subject=subject, paper_count=len(items),
            registry_display=f"subjects/{SUBJECT}/subject.json",
            generator_labels=[TYPE_LABEL.get(g, g)
                              for g in subject.enabled_computed_generators]),
        f"{subject.route}/library/index.html": render(
            "library.html", subject=subject, items=items, total=len(items),
            q="", computed="any", topic="any", placeholders="any",
            topics=topics, computed_options=computed_options,
            item_urls=item_urls),
        f"{subject.route}/generate/index.html": render(
            "generate.html", subject=subject),
        "gallery/index.html": render("gallery.html", items=[]),
        "paused/index.html": render("paused.html"),
    }
    for rel, html in pages.items():
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8")
    (out / "static").mkdir(parents=True, exist_ok=True)
    shutil.copy2(out / "gallery/index.html", out / "static/gallery-shell.html")
    assets = out / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    for name in ("style.css", "htmx.min.js", "library.js"):
        shutil.copy2(STATIC / name, assets / name)
    return {"pages": len(pages) + 1, "assets": 3}


def _write_manifests(out: Path, items: list[dict]) -> dict:
    subject = get_subject(SUBJECT)
    subjects = list(load_subjects().values())
    subject_dir = out / "subjects"
    for item in subjects:
        data = item.public_dict()
        data["paper_count"] = len(items) if item.code == SUBJECT else 0
        if item.code == SUBJECT:
            data["library_manifest"] = f"/library/{SUBJECT}/manifest.json"
            data["routes"] = {
                "home": f"/{item.route}",
                "library": f"/{item.route}/library",
                "generate": f"/{item.route}/generate",
            }
        path = subject_dir / item.code / "subject.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    papers = []
    for item in items:
        urls = _urls(item)
        papers.append({
            "seed": item["seed"],
            "mode": item["mode"],
            "computed_marks": item["computed_display"],
            "year": item["year"],
            "accepted": item["accepted"],
            "placeholders": item["placeholders"],
            "topic_marks": item["topic_marks"],
            "topic_mix": item["topic_mix"],
            "files": {
                "paper_docx": f"library/{SUBJECT}/papers/{item['downloads']['paper_docx']}",
                "paper_pdf": f"library/{SUBJECT}/papers/{item['downloads']['paper_pdf']}",
                "scheme_docx": f"library/{SUBJECT}/schemes/{item['downloads']['scheme_docx']}",
                "scheme_pdf": f"library/{SUBJECT}/schemes/{item['downloads']['scheme_pdf']}",
            },
            "urls": urls,
        })
    lib = {
        "subject": SUBJECT,
        "title": subject.title,
        "year": utc_year(),
        "count": len(papers),
        "papers": papers,
    }
    lib_path = out / "library" / SUBJECT / "manifest.json"
    lib_path.parent.mkdir(parents=True, exist_ok=True)
    lib_path.write_text(json.dumps(lib, indent=2) + "\n", encoding="utf-8")
    index = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "subjects": [
            {"code": s.code, "title": s.title, "status": s.status,
             "papers": len(papers) if s.code == SUBJECT else 0,
             "manifest": (f"/library/{s.code}/manifest.json"
                          if s.code == SUBJECT else None)}
            for s in subjects
        ],
    }
    (out / "library").mkdir(parents=True, exist_ok=True)
    (out / "library" / "manifest.json").write_text(
        json.dumps(index, indent=2) + "\n", encoding="utf-8")
    return {"subjects": len(subjects), "papers": len(papers)}


def build(out: Path, seeds: list[int], force: bool = False,
          pages_only: bool = False) -> dict:
    out = out.resolve()
    if config.PUBLIC_BUILD:
        raise SystemExit("run the builder without PUBLIC_BUILD=1")
    out.mkdir(parents=True, exist_ok=True)
    items = [library_item(seed, SUBJECT) for seed in seeds]
    missing = [seed for seed, item in zip(seeds, items) if item is None]
    if missing:
        raise SystemExit(f"missing Library cache for seeds: {missing}")
    items = [item for item in items if item is not None]
    page_info = _render_pages(out, items)
    print(f"pages: {page_info}", flush=True)
    manifest_info = _write_manifests(out, items)
    print(f"manifests: {manifest_info}", flush=True)
    doc_info = {"built": 0, "skipped": 0}
    if not pages_only:
        doc_info = build_documents(out, seeds, force=force)
        print(f"documents: {doc_info}", flush=True)
    problems = validate(out)
    if problems:
        for problem in problems:
            print("BUNDLE ERROR:", problem, file=sys.stderr)
        raise SystemExit(1)
    return {"out": str(out), "documents": doc_info,
            "pages": page_info, "manifests": manifest_info}


def validate(out: Path) -> list[str]:
    problems = []
    forbidden = ("data/", "CSC662/", "outputs/", "src/", "tests/",
                 "design/", ".env", "wrangler")
    for path in out.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(out).as_posix()
        if any(rel.startswith(prefix) for prefix in forbidden):
            problems.append(f"forbidden path in bundle: {rel}")
        if path.suffix.lower() in {".docx", ".pdf"}:
            problems.extend(_check_public_file(path))
            if "Marking Scheme" in path.name:
                problems.extend(_check_scheme(path))
        elif path.suffix.lower() in {".html", ".json", ".css", ".js", ".txt"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            if PRIVATE_BRAND.lower() in text.lower():
                problems.append(f"private branding in {rel}")
            if "data/reference" in text or "CSC662 FEBRUARY 2026-raw" in text:
                problems.append(f"private path in {rel}")
    return problems


def _seeds(value: str) -> list[int]:
    if "-" in value:
        a, b = value.split("-")
        return list(range(int(a), int(b) + 1))
    return [int(x) for x in value.split(",") if x.strip()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "outputs" / "public_bundle"))
    ap.add_argument("--seeds", default="1-20")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--pages-only", action="store_true")
    args = ap.parse_args()
    print(build(Path(args.out), _seeds(args.seeds), force=args.force,
                pages_only=args.pages_only))


if __name__ == "__main__":
    main()
