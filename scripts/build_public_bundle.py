"""Build the static public bundle for R2.

The builder reads the private Library caches, creates PUBLIC_BUILD copies of
every paper and scheme, renders the public pages and writes the public
manifests.  It never copies private files directly:

- papers keep the original local-build cover and are re-exported;
- CSC662 schemes are rebuilt with verbatim slide quotes omitted;
- MAT133 schemes are deterministic and contain no lecture quotes;
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
from src.app.filenames import utc_year
from src.app.jobs import DEFAULT_SUBJECT, library_item, topic_legend
from src.assemble.build_docx_paper import export_pdf
from src.assemble.generic_build import build_scheme
from src.mat133.planner import GENERATOR_LABELS as MAT133_GENERATOR_LABELS
from src.planner.planner import TYPE_LABEL
from src.subjects.registry import get_subject, load_subjects

APP_DIR = ROOT / "src" / "app"
TEMPLATES = APP_DIR / "templates"
STATIC = APP_DIR / "static"
SUBJECT = DEFAULT_SUBJECT  # backward-compatible default for helpers/tests
MAT133 = "MAT133"
SCHEME_MARKER = "[verbatim slide quote omitted in public build]"
# Only the lecture-deck-based subject needs the public quote-omission marker.
MARKER_SUBJECTS = {DEFAULT_SUBJECT}


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


def _check_scheme(path: Path, *, require_marker: bool = True) -> list[str]:
    problems: list[str] = []
    text = _docx_text(path) if path.suffix.lower() == ".docx" else _pdf_text(path)
    if require_marker:
        normalised = " ".join(text.split())
        if SCHEME_MARKER not in normalised:
            problems.append(f"quote omission marker missing in {path.name}")
    return problems


def _generator_labels(subject) -> list[str]:
    labels = []
    for generator_id in subject.enabled_computed_generators:
        label = (TYPE_LABEL.get(generator_id)
                 or MAT133_GENERATOR_LABELS.get(generator_id))
        labels.append(label or generator_id)
    return labels


def _copy_complete(item: dict, papers: Path, schemes: Path,
                   force: bool) -> bool:
    names = item["downloads"]
    targets = {
        "paper_docx": papers / names["paper_docx"],
        "paper_pdf": papers / names["paper_pdf"],
        "scheme_docx": schemes / names["scheme_docx"],
        "scheme_pdf": schemes / names["scheme_pdf"],
    }
    if not force and all(path.exists() for path in targets.values()):
        return True
    for kind, target in targets.items():
        source = Path(str((item.get("files") or {}).get(kind, "")))
        if not source.exists():
            raise SystemExit(
                f"missing private {kind} for {item['subject']} seed "
                f"{item['seed']}: {source}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return False


def _build_csc662_documents(out: Path, seeds: list[int],
                           force: bool) -> dict:
    subject = SUBJECT
    papers = out / "library" / subject / "papers"
    schemes = out / "library" / subject / "schemes"
    papers.mkdir(parents=True, exist_ok=True)
    schemes.mkdir(parents=True, exist_ok=True)
    plan_dir = config.OUTPUTS_DIR / "eval_final_deepseek"
    built = 0
    skipped = 0
    for seed in seeds:
        item = library_item(seed, subject)
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
            print(f"{subject} seed {seed:02d}: cached bundle files, skipped",
                  flush=True)
            skipped += 1
            continue

        source_docx = Path(item["files"]["paper_docx"])
        if not source_docx.exists():
            raise SystemExit(f"missing private paper DOCX for seed {seed}: "
                             f"{source_docx}")
        print(f"{subject} seed {seed:02d}: public paper (original cover)",
              flush=True)
        shutil.copy2(source_docx, paper_docx)
        export_pdf(paper_docx, paper_pdf)

        print(f"{subject} seed {seed:02d}: public scheme", flush=True)
        build_scheme(source_docx, plan, theory, scheme_docx, scheme_pdf,
                     public=True)
        problems = (_check_scheme(scheme_docx, require_marker=True)
                    + _check_scheme(scheme_pdf, require_marker=True))
        if problems:
            raise SystemExit(f"seed {seed}: " + "; ".join(problems))
        built += 1
    return {"built": built, "skipped": skipped,
            "papers": len(list(papers.glob("*.docx"))),
            "schemes": len(list(schemes.glob("*.docx")))}


def _build_mat133_documents(out: Path, seeds: list[int],
                            force: bool) -> dict:
    papers = out / "library" / MAT133 / "papers"
    schemes = out / "library" / MAT133 / "schemes"
    papers.mkdir(parents=True, exist_ok=True)
    schemes.mkdir(parents=True, exist_ok=True)
    built = 0
    skipped = 0
    for seed in seeds:
        item = library_item(seed, MAT133)
        if item is None:
            raise SystemExit(
                f"no cached MAT133 Library item for seed {seed}; run "
                f"prebuild_library first")
        print(f"{MAT133} seed {seed:02d}: public paper and scheme",
              flush=True)
        if _copy_complete(item, papers, schemes, force):
            print(f"{MAT133} seed {seed:02d}: cached bundle files, skipped",
                  flush=True)
            skipped += 1
            continue
        names = item["downloads"]
        problems = (
            _check_scheme(schemes / names["scheme_docx"],
                          require_marker=False)
            + _check_scheme(schemes / names["scheme_pdf"],
                            require_marker=False))
        if problems:
            raise SystemExit(f"seed {seed}: " + "; ".join(problems))
        built += 1
    return {"built": built, "skipped": skipped,
            "papers": len(list(papers.glob("*.docx"))),
            "schemes": len(list(schemes.glob("*.docx")))}


def build_documents(out: Path, seeds: list[int], force: bool = False,
                    subject: str = SUBJECT) -> dict:
    if subject.upper() == MAT133:
        return _build_mat133_documents(out, seeds, force)
    return _build_csc662_documents(out, seeds, force)


def _urls(item: dict, out_dir: Path | None = None,
          subject: str = SUBJECT) -> dict:
    urls = {}
    for kind, name in item["downloads"].items():
        folder = "schemes" if kind.startswith("scheme") else "papers"
        url = f"/library/{subject}/{folder}/{quote(name, safe='')}"
        if out_dir is not None:
            path = out_dir / "library" / subject / folder / name
            if path.exists():
                url += f"?v={int(path.stat().st_mtime)}"
        urls[kind] = url
    return urls


def _render_pages(out: Path, subject_items: dict[str, list[dict]]) -> dict:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    subjects = list(load_subjects().values())
    counts = {s.code: len(subject_items.get(s.code, [])) for s in subjects}
    try:
        asset_version = int(max(
            p.stat().st_mtime for p in STATIC.iterdir() if p.is_file()))
    except (OSError, ValueError):
        asset_version = 0
    base = {
        "site_name": config.SITE_NAME,
        "subjects": subjects,
        "public": True,
        "static_bundle": True,
        "library_disabled": False,
        "generate_disabled": True,
        "gallery_enabled": True,
        "asset_base": "/assets",
        "asset_version": asset_version,
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

    pages = {"index.html": render("index.html", counts=counts)}
    for code, items in subject_items.items():
        subject = get_subject(code)
        item_urls = {str(item["seed"]): _urls(item, out, code)
                     for item in items}
        topics = sorted({name for item in items
                         for name, marks in item["topic_marks"].items()
                         if int(marks) > 0})
        computed_options = sorted({
            int(item.get("marks_value", item["computed_display"]) or 0)
            for item in items})
        pages[f"{subject.route}/index.html"] = render(
            "subject.html", subject=subject, paper_count=len(items),
            registry_display=f"subjects/{code}/subject.json",
            generator_labels=_generator_labels(subject),
            deterministic=code == MAT133)
        pages[f"{subject.route}/library/index.html"] = render(
            "library.html", subject=subject, items=items, total=len(items),
            q="", computed="any", topic="any", placeholders="any",
            topics=topics, computed_options=computed_options,
            item_urls=item_urls, topic_legend=topic_legend(code))
        pages[f"{subject.route}/generate/index.html"] = render(
            "generate.html", subject=subject, deterministic=code == MAT133)
    pages["gallery/index.html"] = render("gallery.html", items=[])
    pages["paused/index.html"] = render("paused.html")
    for rel, html in pages.items():
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8")
    (out / "static").mkdir(parents=True, exist_ok=True)
    shutil.copy2(out / "gallery/index.html", out / "static/gallery-shell.html")
    assets = out / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    for name in ("style.css", "htmx.min.js", "library.js", "gallery.js"):
        shutil.copy2(STATIC / name, assets / name)
    return {"pages": len(pages) + 1, "assets": 4}


def _write_manifests(out: Path, subject_items: dict[str, list[dict]]) -> dict:
    subjects = list(load_subjects().values())
    subject_dir = out / "subjects"
    for item in subjects:
        data = item.public_dict()
        items = subject_items.get(item.code, [])
        data["paper_count"] = len(items)
        data["has_practice_mode"] = item.has_practice_mode
        data["has_placeholders"] = item.has_placeholders
        if items:
            data["library_manifest"] = f"/library/{item.code}/manifest.json"
            data["routes"] = {
                "home": f"/{item.route}",
                "library": f"/{item.route}/library",
                "generate": f"/{item.route}/generate",
            }
        path = subject_dir / item.code / "subject.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    total_papers = 0
    for code, items in subject_items.items():
        subject = get_subject(code)
        papers = []
        for item in items:
            urls = _urls(item, out, code)
            papers.append({
                "seed": item["seed"],
                "mode": item["mode"],
                "computed_marks": item["computed_display"],
                "total_marks": item.get("total_marks"),
                "marks_value": item.get("marks_value",
                                        item["computed_display"]),
                "has_practice_mode": item.get("has_practice_mode", True),
                "has_placeholders": item.get("has_placeholders", True),
                "year": item["year"],
                "accepted": item["accepted"],
                "placeholders": item["placeholders"],
                "topic_marks": item["topic_marks"],
                "topic_mix": item["topic_mix"],
                "files": {
                    "paper_docx": f"library/{code}/papers/{item['downloads']['paper_docx']}",
                    "paper_pdf": f"library/{code}/papers/{item['downloads']['paper_pdf']}",
                    "scheme_docx": f"library/{code}/schemes/{item['downloads']['scheme_docx']}",
                    "scheme_pdf": f"library/{code}/schemes/{item['downloads']['scheme_pdf']}",
                },
                "urls": urls,
            })
        lib = {
            "subject": code,
            "title": subject.title,
            "year": utc_year(),
            "has_practice_mode": subject.has_practice_mode,
            "has_placeholders": subject.has_placeholders,
            "count": len(papers),
            "papers": papers,
        }
        lib_path = out / "library" / code / "manifest.json"
        lib_path.parent.mkdir(parents=True, exist_ok=True)
        lib_path.write_text(json.dumps(lib, indent=2) + "\n",
                            encoding="utf-8")
        total_papers += len(papers)
    index = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "subjects": [
            {"code": s.code, "title": s.title, "status": s.status,
             "papers": len(subject_items.get(s.code, [])),
             "manifest": (f"/library/{s.code}/manifest.json"
                          if subject_items.get(s.code) else None)}
            for s in subjects
        ],
    }
    (out / "library").mkdir(parents=True, exist_ok=True)
    (out / "library" / "manifest.json").write_text(
        json.dumps(index, indent=2) + "\n", encoding="utf-8")
    return {"subjects": len(subjects), "papers": total_papers}


def _bundle_subject(rel: str) -> str:
    parts = rel.split("/")
    if len(parts) >= 2 and parts[0] == "library":
        return parts[1].upper()
    return ""


def validate(out: Path) -> list[str]:
    problems = []
    forbidden = ("data/", "CSC662/", "MAT133/", "outputs/", "src/", "tests/",
                 "design/", ".env", "wrangler")
    for path in out.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(out).as_posix()
        if any(rel.startswith(prefix) for prefix in forbidden):
            problems.append(f"forbidden path in bundle: {rel}")
        if path.suffix.lower() in {".docx", ".pdf"}:
            if "Marking Scheme" in path.name:
                requires = _bundle_subject(rel) in MARKER_SUBJECTS
                problems.extend(_check_scheme(path, require_marker=requires))
        elif path.suffix.lower() in {".html", ".json", ".css", ".js", ".txt"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "data/reference" in text or "CSC662 FEBRUARY 2026-raw" in text:
                problems.append(f"private path in {rel}")
    for manifest_path in sorted((out / "library").glob("*/manifest.json")):
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            problems.append(f"unreadable manifest {manifest_path.name}: {exc}")
            continue
        for paper in data.get("papers", []):
            for kind, rel in (paper.get("files") or {}).items():
                if not (out / rel).is_file():
                    problems.append(
                        f"manifest {manifest_path.parent.name} references "
                        f"missing {kind}: {rel}")
    return problems


def _seeds(value: str) -> list[int]:
    if "-" in value:
        a, b = value.split("-")
        return list(range(int(a), int(b) + 1))
    return [int(x) for x in value.split(",") if x.strip()]


def build(out: Path, seeds: list[int], force: bool = False,
          pages_only: bool = False, subjects: list[str] | None = None) -> dict:
    out = out.resolve()
    if config.PUBLIC_BUILD:
        raise SystemExit("run the builder without PUBLIC_BUILD=1")
    out.mkdir(parents=True, exist_ok=True)
    available = {s.code for s in load_subjects().values() if s.available}
    codes = [code.upper() for code in (subjects or sorted(available))]
    unknown = [code for code in codes if code not in available]
    if unknown:
        raise SystemExit(f"subject not available: {', '.join(unknown)}")
    subject_items: dict[str, list[dict]] = {}
    for code in codes:
        items = [library_item(seed, code) for seed in seeds]
        missing = [seed for seed, item in zip(seeds, items) if item is None]
        if missing:
            raise SystemExit(
                f"missing {code} Library cache for seeds: {missing}")
        subject_items[code] = [item for item in items if item is not None]
    doc_info = {}
    if not pages_only:
        for code in codes:
            doc_info[code] = build_documents(out, seeds, force=force,
                                             subject=code)
            print(f"{code} documents: {doc_info[code]}", flush=True)
    page_info = _render_pages(out, subject_items)
    print(f"pages: {page_info}", flush=True)
    manifest_info = _write_manifests(out, subject_items)
    print(f"manifests: {manifest_info}", flush=True)
    problems = validate(out)
    if problems:
        for problem in problems:
            print("BUNDLE ERROR:", problem, file=sys.stderr)
        raise SystemExit(1)
    return {"out": str(out), "documents": doc_info,
            "pages": page_info, "manifests": manifest_info}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "outputs" / "public_bundle"))
    ap.add_argument("--seeds", default="1-20")
    ap.add_argument("--subject", action="append",
                    help="subject code; repeat for more than one. "
                         "Default: every available subject")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--pages-only", action="store_true")
    args = ap.parse_args()
    print(build(Path(args.out), _seeds(args.seeds), force=args.force,
                pages_only=args.pages_only, subjects=args.subject))


if __name__ == "__main__":
    main()
