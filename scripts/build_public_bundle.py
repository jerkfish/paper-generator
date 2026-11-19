"""Build the static public bundle for R2.

The builder reads the private Library caches, creates PUBLIC_BUILD copies of
every paper and scheme, renders the public pages and writes the public
manifests.  It never copies private files directly:

- papers keep the original local-build cover and are re-exported;
- subjects whose capability says ``rebuild_scheme`` get public schemes with
  verbatim slide quotes omitted;
- subjects whose capability says ``copy_cached`` reuse their cached scheme;
- only public-safe subject fields and Library metadata are written.

The list of subjects, their routes and their document strategy all come from
the registry.  A generated ``subjects.json`` is written for the Worker.

Run it without PUBLIC_BUILD=1 (the builder applies the public rules itself):

    uv run python -m scripts.build_public_bundle --out outputs/public_bundle
"""
from __future__ import annotations

import argparse
import json
import re
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
from src.app.jobs import (library_item, library_version_columns,
                          topic_legend)
from src.assemble.build_docx_paper import export_pdf
from src.assemble.generic_build import build_scheme
from src.subjects.plugins import (
    generator_labels as subject_generator_labels,
    require_plugin,
)
from src.subjects.registry import (
    Subject,
    default_subject_code,
    get_subject,
    load_subjects,
)

APP_DIR = ROOT / "src" / "app"
TEMPLATES = APP_DIR / "templates"
STATIC = APP_DIR / "static"
SCHEME_MARKER = "[verbatim slide quote omitted in public build]"


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


def _generator_labels(subject: Subject) -> list[str]:
    return subject_generator_labels(subject)


def _public_item(item: dict, subject: Subject) -> dict:
    """Drop document versions the subject contract does not publish yet."""
    if not item.get("versions"):
        return item
    allowed = subject.public_document_versions
    versions = [version for version in item.get("versions") or []
                if str(version["version"]) in allowed]
    if not versions:
        versions = list(item.get("versions") or [])[:1]
    downloads = {}
    for version in versions:
        downloads.update(version["downloads"])
    out = dict(item)
    out["versions"] = versions
    out["version_map"] = {str(version["version"]): version
                          for version in versions}
    out["downloads"] = downloads
    return out


def _copy_complete(item: dict, papers: Path, schemes: Path,
                   force: bool) -> bool:
    names = item["downloads"]
    targets = {}
    for version in item.get("versions") or []:
        for canonical, vkind in (version.get("kinds") or {}).items():
            folder = schemes if canonical.startswith("scheme") else papers
            targets[vkind] = folder / names[vkind]
    if not targets:
        targets = {
            "paper_docx": papers / names["paper_docx"],
            "paper_pdf": papers / names["paper_pdf"],
            "scheme_docx": schemes / names["scheme_docx"],
            "scheme_pdf": schemes / names["scheme_pdf"],
        }
    if not force and all(path.exists() for path in targets.values()):
        return True
    for vkind, target in targets.items():
        canonical = vkind
        match = re.fullmatch(r"(paper|scheme)_v\d+_(docx|pdf)", vkind)
        if match:
            canonical = f"{match.group(1)}_{match.group(2)}"
        source = ""
        for version in item.get("versions") or []:
            if (version.get("kinds") or {}).get(canonical) == vkind:
                source = str((version.get("files") or {}).get(canonical, ""))
                break
        if not source:
            source = str((item.get("files") or {}).get(canonical, ""))
        source_path = Path(source)
        if not source_path.exists():
            raise SystemExit(
                f"missing private {vkind} for {item['subject']} seed "
                f"{item['seed']}: {source_path}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target)
    return False


def _build_rebuilt_documents(out: Path, seeds: list[int], force: bool,
                             subject: Subject) -> dict:
    """Copy the paper and rebuild a quote-free public scheme."""
    papers = out / "library" / subject.code / "papers"
    schemes = out / "library" / subject.code / "schemes"
    papers.mkdir(parents=True, exist_ok=True)
    schemes.mkdir(parents=True, exist_ok=True)
    require_marker = subject.public_scheme_requires_quote_marker
    plan_inputs = require_plugin(subject, "plan_inputs")
    built = 0
    skipped = 0
    for seed in seeds:
        item = library_item(seed, subject)
        if item is None:
            raise SystemExit(
                f"no cached Library item for {subject.code} seed {seed}")
        inputs = plan_inputs(seed)
        plan = Path(inputs["plan"])
        theory = Path(inputs["theory"])
        if not plan.exists() or not theory.exists():
            raise SystemExit(
                f"missing planner/theory JSON for {subject.code} seed {seed}")
        names = item["downloads"]
        paper_docx = papers / names["paper_docx"]
        paper_pdf = papers / names["paper_pdf"]
        scheme_docx = schemes / names["scheme_docx"]
        scheme_pdf = schemes / names["scheme_pdf"]
        if (not force and paper_docx.exists() and paper_pdf.exists()
                and scheme_docx.exists() and scheme_pdf.exists()):
            print(f"{subject.code} seed {seed:02d}: cached bundle files, "
                  f"skipped", flush=True)
            skipped += 1
            continue

        source_docx = Path(item["files"]["paper_docx"])
        if not source_docx.exists():
            raise SystemExit(
                f"missing private paper DOCX for {subject.code} seed {seed}: "
                f"{source_docx}")
        print(f"{subject.code} seed {seed:02d}: public paper "
              f"(original cover)", flush=True)
        shutil.copy2(source_docx, paper_docx)
        export_pdf(paper_docx, paper_pdf)

        print(f"{subject.code} seed {seed:02d}: public scheme", flush=True)
        build_scheme(source_docx, plan, theory, scheme_docx, scheme_pdf,
                     public=True)
        problems = (_check_scheme(scheme_docx, require_marker=require_marker)
                    + _check_scheme(scheme_pdf,
                                    require_marker=require_marker))
        if problems:
            raise SystemExit(f"seed {seed}: " + "; ".join(problems))
        built += 1
    return {"strategy": "rebuild_scheme", "built": built, "skipped": skipped,
            "papers": len(list(papers.glob("*.docx"))),
            "schemes": len(list(schemes.glob("*.docx")))}


def _build_copied_documents(out: Path, seeds: list[int], force: bool,
                            subject: Subject) -> dict:
    """Copy the cached paper and scheme, checking the marker if configured."""
    papers = out / "library" / subject.code / "papers"
    schemes = out / "library" / subject.code / "schemes"
    papers.mkdir(parents=True, exist_ok=True)
    schemes.mkdir(parents=True, exist_ok=True)
    require_marker = subject.public_scheme_requires_quote_marker
    built = 0
    skipped = 0
    for seed in seeds:
        item = library_item(seed, subject)
        if item is None:
            raise SystemExit(
                f"no cached {subject.code} Library item for seed {seed}; run "
                f"prebuild_library first")
        print(f"{subject.code} seed {seed:02d}: public paper and scheme",
              flush=True)
        if _copy_complete(item, papers, schemes, force):
            print(f"{subject.code} seed {seed:02d}: cached bundle files, "
                  f"skipped", flush=True)
            skipped += 1
            continue
        names = item["downloads"]
        problems = []
        for version in item.get("versions") or []:
            kinds = version.get("kinds") or {}
            for canonical in ("scheme_docx", "scheme_pdf"):
                vkind = kinds.get(canonical)
                if vkind and names.get(vkind):
                    problems.extend(_check_scheme(
                        schemes / names[vkind], require_marker=require_marker))
        if problems:
            raise SystemExit(f"seed {seed}: " + "; ".join(problems))
        built += 1
    return {"strategy": "copy_cached", "built": built, "skipped": skipped,
            "papers": len(list(papers.glob("*.docx"))),
            "schemes": len(list(schemes.glob("*.docx")))}


def build_documents(out: Path, seeds: list[int], force: bool = False,
                    subject: str | Subject | None = None) -> dict:
    record = subject if isinstance(subject, Subject) else None
    if record is None:
        record = get_subject(subject or default_subject_code())
    strategy = str(record.capabilities.get("public_documents",
                                           "copy_cached"))
    if strategy == "rebuild_scheme":
        return _build_rebuilt_documents(out, seeds, force, record)
    if strategy == "copy_cached":
        return _build_copied_documents(out, seeds, force, record)
    raise SystemExit(
        f"subject {record.code}: unknown public_documents strategy {strategy!r}")


def _urls(item: dict, out_dir: Path | None = None,
          subject: str | None = None) -> dict:
    code = str(subject or default_subject_code())
    urls = {}
    for kind, name in item["downloads"].items():
        folder = "schemes" if kind.startswith("scheme") else "papers"
        url = f"/library/{code}/{folder}/{quote(name, safe='')}"
        if out_dir is not None:
            path = out_dir / "library" / code / folder / name
            if path.exists():
                url += f"?v={int(path.stat().st_mtime)}"
        urls[kind] = url
    return urls


def _public_subjects(local_only: bool = False) -> list[Subject]:
    """Subjects the public bundle may expose.

    ``coming_soon`` stubs are always public metadata.  An ``available``
    subject is exposed only after its publication permission is recorded.
    ``local_only`` builds a local verification bundle without changing the
    publication permission; it never uploads or deploys.
    """
    public: list[Subject] = []
    for subject in load_subjects().values():
        allowed = bool(
            (subject.permissions or {}).get("publication", {}).get("allowed"))
        if not subject.available or allowed or (
                local_only and subject.available):
            public.append(subject)
    return public


def _bundle_count(out: Path, code: str, built: int) -> int:
    """Count papers already present in the bundle for a partial rebuild.

    A ``--subject`` build only carries items for the selected subjects.  Read
    the existing manifest so the homepage does not show zero for subjects
    whose pages and documents are still in the bundle.
    """
    if built:
        return built
    manifest = out / "library" / code / "manifest.json"
    if not manifest.is_file():
        return 0
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        return max(0, int(data.get("count") or 0))
    except (OSError, TypeError, ValueError):
        return 0


def _render_pages(out: Path, subject_items: dict[str, list[dict]],
                  local_only: bool = False) -> dict:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    subjects = _public_subjects(local_only)
    counts = {
        s.code: _bundle_count(out, s.code, len(subject_items.get(s.code, [])))
        for s in subjects
    }
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
            deterministic=subject.deterministic,
            needs_llm=subject.needs_llm)
        pages[f"{subject.route}/library/index.html"] = render(
            "library.html", subject=subject, items=items, total=len(items),
            q="", computed="any", topic="any", placeholders="any",
            topics=topics, computed_options=computed_options,
            item_urls=item_urls,
            version_columns=library_version_columns(items),
            topic_legend=topic_legend(subject))
        pages[f"{subject.route}/generate/index.html"] = render(
            "generate.html", subject=subject,
            deterministic=subject.deterministic,
            needs_llm=subject.needs_llm)
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


def _write_manifests(out: Path, subject_items: dict[str, list[dict]],
                     local_only: bool = False) -> dict:
    subjects = _public_subjects(local_only)
    subject_dir = out / "subjects"
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
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
            files = {}
            versions = item.get("versions") or []
            for version in versions:
                for canonical, vkind in (version.get("kinds") or {}).items():
                    folder = ("schemes" if canonical.startswith("scheme")
                              else "papers")
                    files[vkind] = (
                        f"library/{code}/{folder}/"
                        f"{item['downloads'][vkind]}")
            if not versions:
                for canonical in ("paper_docx", "paper_pdf",
                                  "scheme_docx", "scheme_pdf"):
                    folder = ("schemes" if canonical.startswith("scheme")
                              else "papers")
                    files[canonical] = (
                        f"library/{code}/{folder}/"
                        f"{item['downloads'][canonical]}")
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
                "documents": [
                    {
                        "version": version["version"],
                        "label": version["label"],
                        "files": {
                            vkind: (
                                f"library/{code}/"
                                + ("schemes" if canonical.startswith("scheme")
                                   else "papers")
                                + f"/{item['downloads'][vkind]}")
                            for canonical, vkind in (
                                version.get("kinds") or {}).items()
                        },
                    }
                    for version in item.get("versions") or []
                ],
                "files": files,
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
        "generated": generated,
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

    # One generated file drives Worker routing and gallery share validation.
    worker_index = {
        "generated": generated,
        "subjects": [
            {
                "code": s.code,
                "title": s.title,
                "status": s.status,
                "route": s.route,
                "available": s.available,
                "type": s.subject_type,
                "papers": len(subject_items.get(s.code, [])),
                "library_manifest": (
                    f"/library/{s.code}/manifest.json"
                    if subject_items.get(s.code) else None),
                "routes": ({
                    "home": f"/{s.route}",
                    "library": f"/{s.route}/library",
                    "generate": f"/{s.route}/generate",
                } if subject_items.get(s.code) else None),
            }
            for s in subjects
        ],
    }
    (out / "subjects.json").write_text(
        json.dumps(worker_index, indent=2) + "\n", encoding="utf-8")
    return {"subjects": len(subjects), "papers": total_papers}


def _bundle_subject(rel: str) -> str:
    parts = rel.split("/")
    if len(parts) >= 2 and parts[0] == "library":
        return parts[1].upper()
    return ""


def validate(out: Path) -> list[str]:
    problems = []
    subjects = {s.code: s for s in load_subjects().values()}
    forbidden = ["data/", "outputs/", "src/", "tests/", "design/", ".env",
                 "wrangler"] + [f"{code}/" for code in subjects]
    private_markers = ["data/reference"] + [
        Path(s.template_path).name for s in subjects.values()
        if s.template_path
    ]
    for path in out.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(out).as_posix()
        if any(rel.startswith(prefix) for prefix in forbidden):
            problems.append(f"forbidden path in bundle: {rel}")
        if path.suffix.lower() in {".docx", ".pdf"}:
            if "Marking Scheme" in path.name:
                subject = subjects.get(_bundle_subject(rel))
                requires = bool(
                    subject and subject.public_scheme_requires_quote_marker)
                problems.extend(_check_scheme(path, require_marker=requires))
        elif path.suffix.lower() in {".html", ".json", ".css", ".js", ".txt"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            if any(marker in text for marker in private_markers):
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
          pages_only: bool = False, subjects: list[str] | None = None,
          local_only: bool = False) -> dict:
    out = out.resolve()
    if config.PUBLIC_BUILD:
        raise SystemExit("run the builder without PUBLIC_BUILD=1")
    out.mkdir(parents=True, exist_ok=True)
    available = {s.code for s in _public_subjects(local_only) if s.available}
    codes = [code.upper() for code in (subjects or sorted(available))]
    unknown = [code for code in codes if code not in available]
    if unknown:
        raise SystemExit(
            f"subject not available for publication: {', '.join(unknown)}")
    subject_items: dict[str, list[dict]] = {}
    for code in codes:
        items = [library_item(seed, code) for seed in seeds]
        missing = [seed for seed, item in zip(seeds, items) if item is None]
        if missing:
            raise SystemExit(
                f"missing {code} Library cache for seeds: {missing}")
        record = get_subject(code)
        subject_items[code] = [_public_item(item, record)
                               for item in items if item is not None]
    doc_info = {}
    if not pages_only:
        for code in codes:
            doc_info[code] = build_documents(out, seeds, force=force,
                                             subject=code)
            print(f"{code} documents: {doc_info[code]}", flush=True)
    page_info = _render_pages(out, subject_items, local_only=local_only)
    print(f"pages: {page_info}", flush=True)
    manifest_info = _write_manifests(out, subject_items, local_only=local_only)
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
    ap.add_argument("--local-only", action="store_true",
                    help="build a local verification bundle without changing "
                         "publication permission; never uploads or deploys")
    args = ap.parse_args()
    print(build(Path(args.out), _seeds(args.seeds), force=args.force,
                pages_only=args.pages_only, subjects=args.subject,
                local_only=args.local_only))


if __name__ == "__main__":
    main()
