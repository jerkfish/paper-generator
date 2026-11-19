"""V1 MinerU dossier for the MAT133 playbook-v2 migration.

Every unique working copy under ``data/papers/MAT133`` is extracted.  The full
MinerU ZIP is kept under ``data/tracking/mat133/v2/mineru/<paper_id>/`` and
normalised to a review dossier.  Failures are recorded per paper and do not
abort the run.

Run:
    uv run python -m src.subjects.mat133.extract --papers MAT133-2026-FEB
    uv run python -m src.subjects.mat133.extract
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from src import config
from src.bank.extraction import extract_paper
from src.subjects.mat133.papers import SUBJECT

TRACKING = config.TRACKING_DIR / "mat133" / "v2"
REGISTER = TRACKING / "papers_register.json"
STATUS = TRACKING / "extraction_status.json"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _save(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def unique_papers() -> list[dict]:
    register = _load(REGISTER, {})
    return list(register.get("unique_papers") or [])


def run(paper_ids: list[str] | None = None, *, model: str = "vlm",
        force: bool = False) -> dict:
    papers = unique_papers()
    if not papers:
        raise SystemExit(
            f"{REGISTER} is missing; run src.subjects.mat133.papers first")
    wanted = {code.upper() for code in paper_ids or []}
    status = _load(STATUS, {"subject": SUBJECT, "model": model,
                            "papers": {}})
    status["model"] = model
    for row in papers:
        paper_id = row["paper_id"]
        if wanted and paper_id.upper() not in wanted:
            continue
        entry = status["papers"].get(paper_id) or {}
        if entry.get("status") == "done" and entry.get("model") == model \
                and not force:
            print(f"{paper_id}: cached dossier", flush=True)
            continue
        started = time.time()
        try:
            source = Path(row["file"])
            if not source.is_absolute():
                source = config.PAPERS_ROOT / SUBJECT / row["file"]
            result = extract_paper(
                subject_code=SUBJECT,
                paper_path=source,
                paper_id=paper_id,
                page_count=int(row["pages"]),
                tracking=TRACKING,
                model=model,
            )
            manifest = result.get("manifest") or {}
            normalized = result.get("normalized") or {}
            entry = {
                "status": "done",
                "paper_id": paper_id,
                "file": row["file"],
                "pages": int(row["pages"]),
                "model": model,
                "batch_id": manifest.get("batch_id", ""),
                "cache_dir": result.get("cache_dir", ""),
                "zip": manifest.get("zip", ""),
                "normalized": normalized.get("counts", {}),
                "contact_sheet": normalized.get("contact_sheet", ""),
                "duration_seconds": round(time.time() - started, 2),
                "cost_usd": 0.0,
                "finished_at": _now(),
            }
            print(f"{paper_id}: {normalized.get('counts', {})}", flush=True)
        except Exception as error:  # keep the batch going paper by paper
            entry = {
                "status": "failed",
                "paper_id": paper_id,
                "file": row["file"],
                "pages": int(row["pages"]),
                "model": model,
                "error": f"{type(error).__name__}: {error}",
                "duration_seconds": round(time.time() - started, 2),
                "cost_usd": 0.0,
                "finished_at": _now(),
            }
            print(f"{paper_id}: FAILED {entry['error']}", flush=True)
        status["papers"][paper_id] = entry
        _save(STATUS, status)
    done = [row for row in status["papers"].values()
            if row.get("status") == "done"]
    failed = [row for row in status["papers"].values()
              if row.get("status") == "failed"]
    summary = {
        "subject": SUBJECT,
        "model": model,
        "papers_total": len(papers),
        "done": len(done),
        "failed": len(failed),
        "documents_uploaded": len(done) + len(failed),
        "daily_limit": 5000,
        "cost_usd": 0.0,
    }
    status["summary"] = summary
    _save(STATUS, status)
    return summary


def write_reports() -> list[Path]:
    """Write one V1 dossier report per extracted paper."""
    status = _load(STATUS, {})
    written = []
    for paper_id, entry in sorted((status.get("papers") or {}).items()):
        if entry.get("status") != "done":
            continue
        cache = Path(entry.get("cache_dir") or "")
        normalized_path = cache / "review" / "normalized.json"
        if not normalized_path.is_file():
            continue
        dossier = json.loads(normalized_path.read_text(encoding="utf-8"))
        counts = dossier.get("counts") or {}
        lines = [
            f"# {paper_id} — MinerU extraction dossier",
            "",
            f"- Model: **{entry.get('model')}**",
            f"- Source: `{entry.get('file')}` ({entry.get('pages')} pages)",
            f"- Batch id: `{entry.get('batch_id')}`",
            f"- Full ZIP: `{entry.get('zip')}`",
            f"- Content list: `{dossier.get('content_list')}`",
            f"- Normalised: `{normalized_path}`",
            f"- Contact sheet: `{dossier.get('contact_sheet')}`",
            "",
            "## Counts",
            "",
        ]
        for key in ("pages", "questions", "figures", "tables", "equations",
                    "assets", "referenced_figures_tables",
                    "resolved_references", "fallback_assets"):
            lines.append(f"- {key.replace('_', ' ')}: {counts.get(key, 0)}")
        lines += ["", "## References and fallbacks", ""]
        unresolved = []
        for question in dossier.get("questions") or []:
            if question.get("refs"):
                lines.append(
                    f"- `{question['question_id']}` page "
                    f"{int(question.get('page_idx', 0)) + 1}: "
                    + ", ".join(question["refs"]))
            if question.get("fallback_assets"):
                unresolved.extend(question["fallback_assets"])
        if not unresolved:
            lines.append("- No fallback assets.")
        for item in dossier.get("fallback") or []:
            lines.append(
                f"- Fallback `{item.get('asset_id')}` page "
                f"{int(item.get('page_idx', 0)) + 1}: {item.get('reason')} "
                f"(`{item.get('path')}`)")
        lines += ["", "## Questions", ""]
        for question in dossier.get("questions") or []:
            lines.append(
                f"- `{question['question_id']}` — page "
                f"{int(question.get('page_idx', 0)) + 1} — "
                f"{len(question.get('blocks') or [])} blocks")
        report = cache / "review" / "EXTRACTION_REPORT.md"
        report.write_text("\n".join(lines) + "\n", encoding="utf-8")
        written.append(report)
    return written


def summary() -> dict:
    status = _load(STATUS, {})
    rows = list((status.get("papers") or {}).values())
    done = [row for row in rows if row.get("status") == "done"]
    failed = [row for row in rows if row.get("status") == "failed"]
    counts = {
        "papers_total": len(unique_papers()),
        "done": len(done),
        "failed": len(failed),
        "pages": sum(int(row.get("pages") or 0) for row in done),
        "questions": sum(int((row.get("normalized") or {}).get(
            "questions") or 0) for row in done),
        "assets": sum(int((row.get("normalized") or {}).get("assets") or 0)
                      for row in done),
        "references": sum(int((row.get("normalized") or {}).get(
            "referenced_figures_tables") or 0) for row in done),
        "resolved_references": sum(int((row.get("normalized") or {}).get(
            "resolved_references") or 0) for row in done),
        "fallback_assets": sum(int((row.get("normalized") or {}).get(
            "fallback_assets") or 0) for row in done),
        "cost_usd": 0.0,
    }
    return {
        "schema_version": 2,
        "subject": SUBJECT,
        "model": status.get("model", ""),
        "counts": counts,
        "failed": [{"paper_id": row.get("paper_id"),
                    "error": row.get("error", "")} for row in failed],
    }


def parser_provenance() -> list[dict]:
    status = _load(STATUS, {})
    rows = []
    for paper_id, entry in sorted((status.get("papers") or {}).items()):
        if entry.get("status") != "done":
            continue
        cache = Path(entry.get("cache_dir") or "")
        rows.append({
            "paper_id": paper_id,
            "parser": "mineru",
            "model": entry.get("model", ""),
            "pages": int(entry.get("pages") or 0),
            "task_id": entry.get("batch_id", ""),
            "cache_path": str(cache),
            "report": str(cache / "review" / "EXTRACTION_REPORT.md"),
        })
    return rows


def write_summary() -> dict:
    data = summary()
    lines = [
        "# MAT133 V1 — MinerU extraction summary",
        "",
        f"Model: **{data['model'] or 'unknown'}**",
        f"Papers: {data['counts']['done']} done, "
        f"{data['counts']['failed']} failed, "
        f"{data['counts']['papers_total']} total",
        f"Pages: {data['counts']['pages']}",
        f"Questions found: {data['counts']['questions']}",
        f"Assets: {data['counts']['assets']} "
        f"({data['counts']['fallback_assets']} page-crop fallbacks)",
        f"References: {data['counts']['references']} "
        f"({data['counts']['resolved_references']} resolved)",
        "Cost: $0.00 (MinerU free tier)",
        "",
        "## Failed papers",
        "",
    ]
    if data["failed"]:
        for row in data["failed"]:
            lines.append(f"- `{row['paper_id']}`: {row['error']}")
    else:
        lines.append("None.")
    lines += [
        "",
        "## Provenance",
        "",
        "- Parser: MinerU (`vlm`) for every unique working copy.",
        "- Full ZIP, content list, page renders and contact sheets are kept "
        "under `data/tracking/mat133/v2/mineru/`.",
        "- Missing printed marks are cross-checked at V2 against the approved "
        "v1 question log and the same paper's legacy OCR; the bank records "
        "`source: v1_question_log` or `source: legacy_ocr` and flags any "
        "conflict.",
        "- The original PDFs under `data/papers/MAT133` were not modified.",
        "",
    ]
    target = TRACKING / "V1_REPORT.md"
    target.write_text("\n".join(lines), encoding="utf-8")
    data["report"] = str(target)
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--papers", nargs="*", default=None)
    parser.add_argument("--model", default="vlm")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--reports-only", action="store_true")
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args()
    if args.summary_only:
        print(json.dumps(write_summary(), indent=2, ensure_ascii=False))
        return
    if args.reports_only:
        print(json.dumps([str(path) for path in write_reports()], indent=2))
        print(json.dumps(write_summary(), indent=2, ensure_ascii=False))
        return
    print(json.dumps(run(args.papers, model=args.model, force=args.force),
                     indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
