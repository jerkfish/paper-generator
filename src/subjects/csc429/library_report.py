"""Coverage report for the CSC429 20-seed Library cache.

The report is evidence for Stage 8.  It reads the cached ``meta.json`` and
``plan.json`` files, validates the loadable Library items and writes the same
JSON to tracking and to the cache root so the seed set can be audited after a
rebuild.

    uv run python -m src.subjects.csc429.library_report
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from src.app.jobs import library_items
from src import config

SUBJECT = "CSC429"
TRACKING = config.TRACKING_DIR / "csc429"
CACHE = config.WEB_CACHE_DIR / SUBJECT
REPORT = TRACKING / "stage8_coverage.json"
BANK = TRACKING / "question_bank_draft.json"
EXPECTED_SEEDS = list(range(1, 21))
PREVIOUS_CALLS = 18
PREVIOUS_COST_USD = 0.017014


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _seed_dirs() -> list[Path]:
    return sorted(path for path in CACHE.iterdir() if path.is_dir())


def build_report() -> dict:
    bank = json.loads(BANK.read_text(encoding="utf-8"))
    bank_ids = {row["question_id"] for row in bank["questions"]}
    rows: list[dict] = []
    real_use: Counter[str] = Counter()
    generator_use: Counter[str] = Counter()
    question_sets: dict[int, set[str]] = {}

    for directory in _seed_dirs():
        meta = json.loads((directory / "meta.json").read_text(encoding="utf-8"))
        plan = json.loads((directory / "plan.json").read_text(encoding="utf-8"))
        validation = meta.get("validation") or {}
        files = meta.get("files") or {}
        real = [slot["question_id"] for slot in plan["slots"]
                if slot["kind"] == "real_bank_question"]
        generated = [slot.get("generator_id") for slot in plan["slots"]
                     if slot["kind"] == "generated_question"]
        real_use.update(real)
        generator_use.update(item for item in generated if item)
        question_sets[int(meta["seed"])] = set(real)
        rows.append({
            "seed": meta["seed"],
            "cache_dir": directory.relative_to(config.PROJECT_ROOT).as_posix(),
            "created_year": meta.get("year"),
            "paper_pages": (validation.get("paper_pdf") or {}).get("pages"),
            "scheme_pages": (validation.get("scheme_pdf") or {}).get("pages"),
            "accepted": meta.get("accepted"),
            "placeholders": meta.get("placeholders"),
            "total_marks": meta.get("total_marks"),
            "generated_slots": len(generated),
            "real_bank_slots": len(real),
            "answers": {
                "requested": (meta.get("answers") or {}).get("requested"),
                "cache_hits": (meta.get("answers") or {}).get("cache_hits"),
                "generated": (meta.get("answers") or {}).get("generated"),
                "cost_usd": (meta.get("answers") or {}).get("cost_usd"),
            },
            "warnings": meta.get("warnings") or [],
            "qa": {
                "paper_xml_valid": (validation.get("paper_docx") or {}).get(
                    "xml_valid"),
                "scheme_xml_valid": (validation.get("scheme_docx") or {}).get(
                    "xml_valid"),
                "paper_problems": (validation.get("paper_docx") or {}).get(
                    "problems") or [],
                "scheme_problems": (validation.get("scheme_docx") or {}).get(
                    "problems") or [],
                "paper_pdf_problems": (validation.get("paper_pdf") or {}).get(
                    "problems") or [],
                "scheme_pdf_problems": (validation.get("scheme_pdf") or {}).get(
                    "problems") or [],
                "paper_right_overflow": (
                    validation.get("paper_pdf") or {}).get(
                        "right_overflow") or [],
                "scheme_right_overflow": (
                    validation.get("scheme_pdf") or {}).get(
                        "right_overflow") or [],
            },
            "files_exist": all(Path(path).is_file() for path in files.values()),
            "files": {key: str(value) for key, value in files.items()},
            "sha256": {
                "paper_docx": _sha256(directory / "paper.docx"),
                "paper_pdf": _sha256(directory / "paper.pdf"),
                "scheme_docx": _sha256(directory / "scheme.docx"),
                "scheme_pdf": _sha256(directory / "scheme.pdf"),
            },
            "real_question_ids": real,
            "generator_ids": generated,
        })

    rows.sort(key=lambda row: row["seed"])
    items = library_items(SUBJECT)
    real_slots = sum(row["real_bank_slots"] for row in rows)
    generated_slots = sum(row["generated_slots"] for row in rows)
    stage_cost = round(
        sum(row["answers"]["cost_usd"] or 0 for row in rows), 6)
    cache_meta = json.loads(
        (_seed_dirs()[0] / "meta.json").read_text(encoding="utf-8"))
    cache_usage = (cache_meta.get("answers") or {}).get("cache_usage") or {}
    checks = {
        "library_items_count": len(items),
        "seeds_1_to_20": [row["seed"] for row in rows] == EXPECTED_SEEDS,
        "all_seeds_distinct_question_sets": len({
            tuple(sorted(values)) for values in question_sets.values()
        }) == 20,
        "all_11_of_11_slots_accepted": all(
            row["accepted"] == 11 and row["placeholders"] == 0
            for row in rows),
        "all_total_marks_100": all(row["total_marks"] == 100 for row in rows),
        "all_files_exist": all(row["files_exist"] for row in rows),
        "all_qa_problems_empty": all(
            not any(row["qa"][key] for key in (
                "paper_problems", "scheme_problems", "paper_pdf_problems",
                "scheme_pdf_problems", "paper_right_overflow",
                "scheme_right_overflow"))
            for row in rows),
        "all_warnings_empty": all(not row["warnings"] for row in rows),
        "library_items_all_loadable": len(items) == 20 and all(
            item["files"] for item in items),
    }
    report = {
        "schema_version": 1,
        "subject": SUBJECT,
        "stage": 8,
        "report": "20-seed library prebuild coverage",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "builder_version": 2,
        "checks": checks,
        "aggregates": {
            "seed_count": len(rows),
            "paper_pages_min": min(row["paper_pages"] for row in rows),
            "paper_pages_max": max(row["paper_pages"] for row in rows),
            "scheme_pages_min": min(row["scheme_pages"] for row in rows),
            "scheme_pages_max": max(row["scheme_pages"] for row in rows),
            "real_bank_slots": real_slots,
            "generated_slots": generated_slots,
            "unique_real_questions": len(real_use),
            "bank_questions": len(bank_ids),
            "bank_coverage_percent": round(
                100 * len(set(real_use) & bank_ids) / len(bank_ids), 1),
            "reused_real_questions": sum(
                1 for count in real_use.values() if count > 1),
            "max_real_question_reuse": max(real_use.values()),
            "most_reused_real_questions": real_use.most_common(10),
            "generator_slots": dict(sorted(generator_use.items())),
            "answer_calls_generated": sum(
                row["answers"]["generated"] or 0 for row in rows),
            "stage_llm_cost_usd": stage_cost,
            "answer_cache_after": cache_usage,
            "answer_cache_before": {
                "calls": PREVIOUS_CALLS,
                "cost_usd": PREVIOUS_COST_USD,
            },
            "answer_cache_delta_calls": int(
                cache_usage.get("calls", 0)) - PREVIOUS_CALLS,
            "answer_cache_delta_cost_usd": round(
                float(cache_usage.get("cost_usd", 0.0))
                - PREVIOUS_COST_USD, 6),
        },
        "notes": [
            "All 20 seeds are deterministic real-bank/generator builds; no "
            "seed has a placeholder.",
            "The 20 seeds use 82 distinct real-bank questions across 180 "
            "real-bank slots; 40 slots are generated arithmetic.",
            "CSC429-2014-06-A9 is selected in all 20 seeds because it is the "
            "only 5-mark instruction_set_addressing candidate whose assets "
            "pass the readiness gate; four other candidates depend on "
            "fill-in tables that Stage 1 does not recreate from OCR.",
            "Seed 1 is the Stage-7 approved sample and is 8 paper pages; the "
            "other seeds use fewer figure-heavy questions and are 5-6 paper "
            "pages.",
        ],
        "seeds": rows,
    }
    return report


def main() -> None:
    report = build_report()
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    REPORT.write_text(text, encoding="utf-8")
    (CACHE / "stage8_coverage.json").write_text(text, encoding="utf-8")
    print(json.dumps({
        "report": str(REPORT),
        "checks": report["checks"],
        "aggregates": report["aggregates"],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
