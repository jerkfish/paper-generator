"""CLI for a recycle subject's question bank.

Read-only unless a command explicitly writes a file (``review``, ``plans
--write``).  Nothing here publishes, uploads or deploys.

Examples:

    uv run python -m src.bank.cli status ICT450
    uv run python -m src.bank.cli review ICT450
    uv run python -m src.bank.cli plans ICT450 --sections sections.json --seeds 1-3
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from src.assemble.recycle import (
    build_plans,
    feasibility,
    pool_summary,
    requirements_from_sections,
)
from src.bank.duplicates import cluster_duplicates
from src.bank.gates import bank_root, require_seed_gate
from src.bank.quality import quality_band, quality_score
from src.bank.review import build_review_sheet
from src.bank.store import BankStore, save_json
from src.subjects.registry import get_subject


def _store(code: str) -> BankStore:
    return BankStore(bank_root(code))


def _parse_seeds(value: str) -> list[int]:
    if "-" in value:
        first, last = value.split("-", 1)
        return list(range(int(first), int(last) + 1))
    return [int(item) for item in value.split(",") if item.strip()]


def bank_status(code: str) -> dict:
    subject = get_subject(code)
    store = _store(subject.code)
    questions = list(store.questions())
    assets = list(store.assets())
    statuses = Counter(str(row.get("status") or "unknown")
                       for row in questions)
    kinds = Counter(str(row.get("kind") or "unknown") for row in assets)
    asset_map = {str(row.get("id")): row for row in assets}
    scores = {str(row.get("id")): quality_score(row, asset_map)
              for row in questions}
    average = round(sum(scores.values()) / len(scores), 3) if scores else 0.0
    clusters = [row for row in cluster_duplicates(questions)
                if row["count"] > 1]
    return {
        "subject": subject.code,
        "strategy": subject.strategy,
        "bank": str(store.root),
        "questions": len(questions),
        "assets": len(assets),
        "statuses": dict(sorted(statuses.items())),
        "asset_kinds": dict(sorted(kinds.items())),
        "approved": statuses.get("approved", 0),
        "duplicate_clusters": len(clusters),
        "duplicates": clusters,
        "quality_average": average,
        "quality_bands": dict(sorted(Counter(
            quality_band(score) for score in scores.values()).items())),
    }


def sections_from_file(path: Path) -> list[dict]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = payload.get("sections") or []
    return list(payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["status", "review", "plans"])
    parser.add_argument("code")
    parser.add_argument("--sections", type=Path,
                        help="JSON sections for feasibility/plans")
    parser.add_argument("--seeds", default="1-3",
                        help="seed range for plans, e.g. 1-3 or 1,2,3")
    parser.add_argument("--reuse-cap", type=int, default=4)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--write", action="store_true",
                        help="write plan JSON files into the bank")
    args = parser.parse_args()

    subject = get_subject(args.code)
    store = _store(subject.code)
    if args.command == "status":
        payload = bank_status(subject.code)
        if args.sections:
            requirements = requirements_from_sections(
                sections_from_file(args.sections))
            payload["pool"] = pool_summary(list(store.questions()),
                                           requirements)
            payload["feasibility"] = feasibility(
                list(store.questions()), requirements,
                reuse_cap=args.reuse_cap, max_seeds=20)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    if args.command == "review":
        out = args.out or store.review_dir
        index = build_review_sheet(store, out, subject=subject.code)
        print(index)
        return

    if not args.sections:
        raise SystemExit("plans requires --sections")
    requirements = requirements_from_sections(
        sections_from_file(args.sections))
    seeds = _parse_seeds(args.seeds)
    require_seed_gate(subject.code, min(seeds))
    if any(seed >= 4 for seed in seeds):
        require_seed_gate(subject.code, 4)
    plans = build_plans(list(store.questions()), requirements,
                        seed_count=max(seeds), reuse_cap=args.reuse_cap)
    selected = [plan for plan in plans if plan["seed"] in set(seeds)]
    if args.write:
        for plan in selected:
            save_json(store.plans_dir / f"seed_{plan['seed']:02d}.json", plan)
    print(json.dumps(selected, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
