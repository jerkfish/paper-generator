"""Stage 1 report for CSC429.

Aggregates register, page capture, layout, asset and question-bank artifacts
into one auditable report.  It does not parse PDFs itself and makes no LLM
calls.
"""
from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from pathlib import Path

from src import config

SUBJECT = "CSC429"
TRACKING = config.TRACKING_DIR / "csc429"


def _load(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _rel(path: Path) -> str:
    try:
        return path.relative_to(config.PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def build_report() -> dict:
    register = json.loads(
        (TRACKING / "papers_register.json").read_text(encoding="utf-8"))
    summary = _load(TRACKING / "papers_summary.json")
    pages = _load(TRACKING / "pages_manifest.json")
    layout = _load(TRACKING / "layout_manifest.json")
    assets = _load(TRACKING / "assets" / "manifest.json")
    bank = _load(TRACKING / "question_bank_draft.json")

    unique = [row for row in register if not row.get("duplicate_of")]
    duplicates = [row for row in register if row.get("duplicate_of")]
    asset_rows = assets.get("assets", [])
    kinds = Counter(str(row.get("kind", "other")) for row in asset_rows)
    confidence = Counter(str(row.get("confidence", "unknown"))
                         for row in asset_rows)
    unresolved = assets.get("unresolved", [])
    questions = bank.get("questions", [])
    by_part = Counter(str(row.get("part", "?")) for row in questions)
    with_marks = sum(1 for row in questions
                     if isinstance(row.get("marks"), int)
                     and row["marks"] > 0)
    with_assets = sum(1 for row in questions if row.get("asset_ids"))
    unsure = list(bank.get("unsure", []))
    report = {
        "schema_version": 1,
        "subject": SUBJECT,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cost_usd": 0.0,
        "llm_calls": 0,
        "inputs": {
            "papers": len(register),
            "unique": len(unique),
            "duplicates": len(duplicates),
            "duplicate_groups": summary.get("duplicate_groups", []),
            "source_texts": dict(sorted(Counter(
                row.get("source_kind", "") for row in unique).items())),
        },
        "pages": {
            "unique_pages": pages.get("pages", 0),
            "rendered": pages.get("pages", 0),
            "dpi": pages.get("dpi", 0),
        },
        "text": {
            "text_layer_papers": sum(
                1 for row in unique if row.get("source_kind") == "text"),
            "ocr_papers": sum(
                1 for row in unique if row.get("source_kind") == "ocr"),
            "layout_lines": layout.get("lines", 0),
            "caption_lines": layout.get("caption_lines", 0),
        },
        "assets": {
            "total": len(asset_rows),
            "by_kind": dict(sorted(kinds.items())),
            "by_confidence": dict(sorted(confidence.items())),
            "unresolved": len(unresolved),
            "manifest": _rel(TRACKING / "assets" / "manifest.json")
            if asset_rows else "",
        },
        "questions": {
            "total": len(questions),
            "by_part": dict(sorted(by_part.items())),
            "with_marks": with_marks,
            "without_marks": len(questions) - with_marks,
            "with_assets": with_assets,
            "bank": _rel(TRACKING / "question_bank_draft.json")
            if questions else "",
        },
        "unsure": unsure,
        "unsure_count": len(unsure),
        "status": "ok" if asset_rows and questions else "partial",
    }
    report_path = TRACKING / "stage1_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    summary["assets"] = {
        "status": report["status"],
        "schema_version": 1,
        "pages_rendered": report["pages"]["rendered"],
        "figures": kinds.get("figure", 0),
        "tables": kinds.get("table", 0),
        "assets_total": len(asset_rows),
        "unresolved_refs": len(unresolved),
        "questions_extracted": len(questions),
        "questions_with_assets": with_assets,
        "manifest": report["assets"]["manifest"],
        "question_bank": report["questions"]["bank"],
        "report": _rel(report_path),
        "cost_usd": 0.0,
        "unsure": unsure,
    }
    (TRACKING / "papers_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    return report


def run_pipeline(subject: str, papers_dir: Path | None = None,
                 tracking_dir: Path | None = None, rows=None,
                 summary=None, ocr: bool = True) -> dict:
    """Run the subject-owned Stage 1 capture/layout/assets/report pipeline."""
    global TRACKING

    from src.subjects.csc429 import capture, layout

    if papers_dir is not None:
        capture.PAPERS = Path(papers_dir)
        layout.PAPERS = Path(papers_dir)
    if tracking_dir is not None:
        tracking = Path(tracking_dir)
        TRACKING = tracking
        capture.TRACKING = tracking
        capture.REGISTER = tracking / "papers_register.json"
        capture.PAGES_DIR = tracking / "pages"
        capture.MANIFEST = tracking / "pages_manifest.json"
        layout.TRACKING = tracking
        layout.REGISTER = tracking / "papers_register.json"
        layout.PAGES = tracking / "pages"
        layout.LAYOUT = tracking / "layout"
    tracking = Path(tracking_dir) if tracking_dir is not None else TRACKING
    capture.capture_pages(force=True)
    layout.build_layout(force=True)
    try:
        from src.subjects.csc429 import assets
        assets.TRACKING = tracking
        assets.PAGES = tracking / "pages"
        assets.LAYOUT = tracking / "layout"
        assets.ASSETS = tracking / "assets"
        assets.REGISTER = tracking / "papers_register.json"
        assets.build_assets(force=True)
    except ImportError:
        pass
    try:
        from src.subjects.csc429 import questions
        questions.build_question_bank(tracking_dir=tracking)
    except ImportError:
        pass
    report = build_report()
    return {
        "status": report["status"],
        "pages": report["pages"],
        "text": report["text"],
        "assets": report["assets"],
        "questions": report["questions"],
        "unsure_count": report["unsure_count"],
        "cost_usd": 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="store_true")
    parser.parse_args()
    print(json.dumps(build_report(), indent=2))


if __name__ == "__main__":
    main()
