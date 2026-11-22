"""Build the CSC404 Library cache and manifest after Gate B.

Run:
    uv run python -m src.subjects.csc404.library --seeds 1-20
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from src import config
from src.app.jobs import cache_path
from src.subjects.csc404.plugin import build_seed, library_seeds, seed_cap

OUT = config.WEB_CACHE_DIR / "CSC404"
MANIFEST = OUT / "manifest.json"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_library(seeds: list[int] | None = None, *,
                  force: bool = False) -> dict:
    seeds = list(seeds or library_seeds())
    rows = []
    for seed in seeds:
        target = cache_path("realistic", seed, None, subject="CSC404")
        result = build_seed(seed, out_dir=target, force=force)
        plan = json.loads((target / "plan.json").read_text(encoding="utf-8"))
        qa = json.loads((target / "qa.json").read_text(encoding="utf-8"))
        meta = json.loads((target / "meta.json").read_text(encoding="utf-8"))
        rows.append({
            "seed": seed,
            "path": str(target),
            "paper_pdf": meta["files"]["paper_pdf"],
            "scheme_pdf": meta["files"]["scheme_pdf"],
            "paper_pages": meta.get("paper_pages", 0),
            "scheme_pages": meta.get("scheme_pages", 0),
            "total_marks": plan.get("total_marks", 0),
            "distinct_papers": plan.get("distinct_papers", 0),
            "questions": [slot["question_id"] for slot in plan["slots"]],
            "qa": qa.get("problems") or [],
        })
    reuse = Counter(qid for row in rows for qid in row["questions"])
    manifest = {
        "schema_version": 2,
        "subject": "CSC404",
        "generated_on": _now(),
        "seed_cap": seed_cap(),
        "seeds": rows,
        "counts": {
            "seeds": len(rows),
            "questions_per_seed": 6,
            "marks_per_seed": 100,
            "qa_problems": sum(len(row["qa"]) for row in rows),
            "max_question_reuse": max(reuse.values()) if reuse else 0,
            "reuse_cap": 4,
        },
        "feasibility": {
            "seeds_possible": seed_cap(),
            "exact_slot_marks_possible": 0,
        },
        "cost_usd": 0.0,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n",
                        encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", default="1-20")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if "-" in args.seeds:
        first, last = args.seeds.split("-", 1)
        seeds = list(range(int(first), int(last) + 1))
    else:
        seeds = [int(value) for value in args.seeds.split(",")]
    manifest = build_library(seeds, force=args.force)
    print(json.dumps({
        "manifest": str(MANIFEST),
        "counts": manifest["counts"],
        "seeds": [row["seed"] for row in manifest["seeds"]],
    }, indent=2))


if __name__ == "__main__":
    main()
