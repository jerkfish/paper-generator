"""Run the MinerU pilot on three representative CSC413 papers.

Pilot only: three papers, both model versions, no Library changes, no publish.
"""
from __future__ import annotations

import json
import os
import time
from collections import Counter
from pathlib import Path

import pymupdf

from src import config
from src.subjects.parsers import mineru_client, mineru_normalize
from src.subjects.registry import get_subject

CODE = "CSC413"
TRACKING = config.TRACKING_DIR / "csc413"
MINERU_ROOT = TRACKING / "mineru"
REPORT = MINERU_ROOT / "pilot_report.json"
REPORT_MD = MINERU_ROOT / "PILOT_REPORT.md"
PILOT_MODELS = ("pipeline", "vlm")


def _load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _save(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def _papers() -> list[dict]:
    register = _load(TRACKING / "papers_register.json", [])
    rows = []
    for row in register:
        if row.get("error") or row.get("duplicate_of"):
            continue
        path = config.PAPERS_ROOT / CODE / str(row.get("source", ""))
        if not path.is_file():
            continue
        with pymupdf.open(str(path)) as pdf:
            pages = len(pdf)
            images = sum(len(page.get_images(full=True)) for page in pdf)
        rows.append({
            "paper_id": f"CSC413-{row.get('year')}-{str(row.get('month'))[:3]}",
            "source": row.get("source"),
            "path": path,
            "pages": pages,
            "images": images,
            "source_kind": row.get("source_kind", ""),
        })
    return rows


def _select(rows: list[dict]) -> list[dict]:
    text = next((row for row in rows if row["source_kind"] == "text"), None)
    scanned = next((row for row in rows if row["source_kind"] == "ocr"), None)
    by_images = sorted(rows, key=lambda row: (-row["images"], row["source"]))
    selected = []
    for row in (text, scanned, by_images[0] if by_images else None):
        if row and row not in selected:
            selected.append(row)
    for row in by_images:
        if len(selected) >= 3:
            break
        if row not in selected:
            selected.append(row)
    return selected[:3]


def _permission() -> tuple[bool, dict, list[dict]]:
    subject = get_subject(CODE)
    cloud = (subject.permissions or {}).get("cloud_processing") or {}
    allowed = bool(cloud.get("allowed"))
    papers = _load(TRACKING / "papers_register.json", [])
    excluded = [] if allowed else [
        {"source": row.get("source"), "reason": "cloud_processing not allowed"}
        for row in papers if not row.get("error") and not row.get("duplicate_of")
    ]
    return allowed, cloud, excluded


def _stats(result: dict) -> dict:
    return result.get("counts", {})


def run() -> dict:
    allowed, cloud, excluded = _permission()
    rows = _papers()
    selected = _select(rows)
    total_pages = sum(row["pages"] for row in selected) * len(PILOT_MODELS)
    configured = mineru_client.load_config()
    if not allowed:
        report = {
            "schema_version": 1,
            "subject": CODE,
            "status": "blocked_permission",
            "cloud_processing": cloud,
            "excluded_files": excluded,
            "paper_count": len(rows),
            "cost_usd": 0.0,
        }
        _save(REPORT, report)
        return report
    if total_pages > configured.page_budget:
        report = {
            "schema_version": 1,
            "subject": CODE,
            "status": "blocked_page_budget",
            "page_budget": configured.page_budget,
            "pages_requested": total_pages,
            "selected": [row["paper_id"] for row in selected],
            "cost_usd": 0.0,
        }
        _save(REPORT, report)
        return report
    if not configured.api_key:
        report = {
            "schema_version": 1,
            "subject": CODE,
            "status": "blocked_api_key",
            "required_variable": "MINERU_API_KEY",
            "selected": [row["paper_id"] for row in selected],
            "cost_usd": 0.0,
        }
        _save(REPORT, report)
        return report
    results = []
    started = time.time()
    config_data = mineru_client.MineruConfig(
        api_key=configured.api_key,
        page_budget=configured.page_budget,
        request_timeout=int(os.environ.get("MINERU_REQUEST_TIMEOUT_SECONDS",
                                          "300")),
        options=mineru_client.MineruOptions(
            model_version="pipeline",
            language=os.environ.get("MINERU_LANGUAGE", "en").strip() or "en",
            timeout_seconds=int(os.environ.get("MINERU_TIMEOUT_SECONDS",
                                              "900")),
            poll_interval=float(os.environ.get("MINERU_POLL_INTERVAL", "3")),
            retries=int(os.environ.get("MINERU_RETRIES", "3")),
            concurrency=int(os.environ.get("MINERU_CONCURRENCY", "2")),
        ),
    )
    with mineru_client.MineruClient(config_data) as client:
        for paper in selected:
            for model in PILOT_MODELS:
                options = mineru_client.MineruOptions(
                    model_version=model,
                    language=config_data.options.language,
                    timeout_seconds=config_data.options.timeout_seconds,
                    poll_interval=config_data.options.poll_interval,
                    retries=config_data.options.retries,
                    concurrency=config_data.options.concurrency,
                )
                print(f"{paper['paper_id']} {model}: start", flush=True)
                entry = {
                    "paper_id": paper["paper_id"],
                    "source": paper["source"],
                    "source_kind": paper["source_kind"],
                    "pages": paper["pages"],
                    "pdf_images": paper["images"],
                    "model": model,
                    "cached": False,
                    "error": "",
                }
                try:
                    manifest = client.parse(
                        code=CODE,
                        paper_path=paper["path"],
                        paper_id=paper["paper_id"],
                        page_count=paper["pages"],
                        options=options,
                        tracking=TRACKING,
                    )
                    entry["cached"] = bool(manifest.get("cached"))
                    entry["batch_id"] = manifest.get("batch_id", "")
                    entry["duration_seconds"] = manifest.get(
                        "duration_seconds", 0)
                    cache_dir = Path(manifest["zip"]).parent
                    normalized = mineru_normalize.normalize(
                        paper_id=paper["paper_id"],
                        pdf_path=paper["path"],
                        cache_dir=cache_dir,
                        model=model,
                        out_dir=cache_dir / "review",
                    )
                    entry["counts"] = _stats(normalized)
                    entry["contact_sheet"] = normalized["contact_sheet"]
                    print(f"{paper['paper_id']} {model}: "
                          f"{entry['counts']}", flush=True)
                except mineru_client.MineruAuthError as error:
                    entry["error"] = f"AUTH: {error}"
                except mineru_client.MineruQuotaError as error:
                    entry["error"] = f"QUOTA: {error}"
                except mineru_client.MineruTimeout as error:
                    entry["error"] = f"TIMEOUT: {error}"
                except Exception as error:
                    entry["error"] = f"{type(error).__name__}: {error}"
                if entry.get("error"):
                    print(f"{paper['paper_id']} {model}: {entry['error']}",
                          flush=True)
                results.append(entry)
    tally = Counter()
    for row in results:
        if row.get("counts"):
            for key in ("figures", "tables", "equations", "fallback_assets",
                        "resolved_references", "referenced_figures_tables"):
                tally[key] += int(row["counts"].get(key, 0))
    report = {
        "schema_version": 1,
        "subject": CODE,
        "status": "complete" if not any(row["error"] for row in results)
        else "complete_with_errors",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "permission": cloud,
        "excluded_files": excluded,
        "page_budget": configured.page_budget,
        "pages_requested": total_pages,
        "models": list(PILOT_MODELS),
        "selected_papers": [row["paper_id"] for row in selected],
        "results": results,
        "totals": dict(tally),
        "duration_seconds": round(time.time() - started, 2),
        "cost_usd": 0.0,
        "cost_note": "MinerU v4 does not expose a per-task price here; pages submitted are recorded.",
        "contact_sheets": [row.get("contact_sheet") for row in results
                           if row.get("contact_sheet")],
    }
    _save(REPORT, report)
    lines = [
        "# MinerU pilot — CSC413",
        "",
        f"Status: **{report['status']}**",
        "",
        f"- Selected papers: {', '.join(report['selected_papers'])}",
        f"- Models: {', '.join(PILOT_MODELS)}",
        f"- Page budget: {configured.page_budget}; pages requested: {total_pages}",
        f"- Cost: $0.00 recorded; pages submitted: {total_pages}",
        "",
        "| Paper | Kind | Pages | Model | Figures | Tables | Equations | Refs | Resolved | Fallback | Cache |",
        "|---|---|---:|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in results:
        c = row.get("counts", {})
        lines.append(
            f"| {row['paper_id']} | {row['source_kind']} | {row['pages']} | "
            f"{row['model']} | {c.get('figures',0)} | {c.get('tables',0)} | "
            f"{c.get('equations',0)} | {c.get('referenced_figures_tables',0)} | "
            f"{c.get('resolved_references',0)} | {c.get('fallback_assets',0)} | "
            f"{'hit' if row['cached'] else 'miss'} |")
        if row.get("error"):
            lines.append(f"| | | | | | | | | | | **{row['error']}** |")
    lines += ["", "Contact sheets:", ""]
    lines += [f"- `{path}`" for path in report["contact_sheets"]]
    lines += ["", "No remaining papers were processed. The default model is for the owner to choose.", ""]
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    return report


def main() -> None:
    print(json.dumps(run(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
