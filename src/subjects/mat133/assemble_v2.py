"""V5 MAT133 assembly: 4 questions, 10+10+10+25 marks, no invented questions.

The shared recycle planner owns the deterministic selection.  This module
prepares MAT133 candidates (approved questions with usable answers), runs the
feasibility check and writes the first seed plans for Gate B review.

Run:
    uv run python -m src.subjects.mat133.assemble_v2 --seeds 1-3
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src import config
from src.assemble.recycle import (build_plans, feasibility,
                                  requirements_from_sections)
from src.bank.store import BankStore, load_json, save_json

TRACKING = config.TRACKING_DIR / "mat133" / "v2"
BANK = TRACKING / "bank"
FORMAT = TRACKING / "format_profile.json"
OUT = config.OUTPUTS_DIR / "review" / "mat133_v2" / "seeds"
REUSE_CAP = 4
SUBJECT = "MAT133"


def _seeds(value: str) -> list[int]:
    if "-" in value:
        start, end = value.split("-", 1)
        return list(range(int(start), int(end) + 1))
    return [int(part) for part in value.split(",") if part.strip()]


def structural_issues(question: dict) -> list[str]:
    """Printed structure that must exist before a question can be assembled."""
    issues = []
    parts = question.get("parts") or []
    if not parts:
        issues.append("no parts")
    for part in parts:
        label = part.get("label") or "?"
        if not str(part.get("text") or "").strip():
            issues.append(f"part {label} has no text")
        if not part.get("marks"):
            issues.append(f"part {label} has no marks")
    return issues


def answer_exclusions() -> list[dict]:
    data = load_json(BANK / "answer_exclusions.json", {})
    return list(data.get("excluded") or [])


def structural_exclusions() -> list[dict]:
    store = BankStore(BANK)
    rows = []
    for question in store.questions():
        if question.get("status") != "approved":
            continue
        issues = structural_issues(question)
        if issues:
            rows.append({"question_id": question["id"],
                         "marks": question.get("marks"),
                         "issues": issues})
    return rows


def usable_questions() -> list[dict]:
    store = BankStore(BANK)
    answers = load_json(BANK / "answers.json", {}).get("by_qid") or {}
    excluded = {str(row.get("question_id")) for row in answer_exclusions()}
    rows = []
    for question in store.questions():
        if question.get("status") != "approved":
            continue
        if question["id"] in excluded:
            continue
        if structural_issues(question):
            continue
        answer = answers.get(question["id"]) or {}
        if not answer or not answer.get("usable", False):
            continue
        row = dict(question)
        row["part"] = "Q"
        row["topic_primary"] = (
            (row.get("topic_tags") or ["other"])[0])
        row["answer_id"] = answer.get("answer_id")
        rows.append(row)
    return rows


def format_profile() -> dict:
    profile = load_json(FORMAT, {})
    if not profile:
        raise SystemExit(f"{FORMAT} is missing; run format_v3 first")
    return profile


def requirements() -> list:
    return requirements_from_sections(format_profile()["sections"])


def feasibility_report() -> dict:
    report = feasibility(
        usable_questions(), requirements(), reuse_cap=REUSE_CAP,
        max_seeds=20)
    report["structural_excluded"] = structural_exclusions()
    report["structural_excluded_count"] = len(report["structural_excluded"])
    report["answer_excluded"] = answer_exclusions()
    report["answer_excluded_count"] = len(report["answer_excluded"])
    return report


def plans_for(seeds: list[int]) -> list[dict]:
    questions = usable_questions()
    reqs = requirements()
    if not questions:
        raise SystemExit(
            "no usable approved MAT133 questions; run V4 answers first")
    count = max(seeds) if seeds else 0
    plans = build_plans(questions, reqs, seed_count=count,
                        reuse_cap=REUSE_CAP, rng_seed="mat133:v2")
    return [plan for plan in plans if int(plan["seed"]) in set(seeds)]


def write_plans(seeds: list[int]) -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    paths = []
    for plan in plans_for(seeds):
        path = OUT / f"seed_{int(plan['seed']):02d}" / "plan.json"
        save_json(path, plan)
        paths.append(path)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", default="1-3")
    parser.add_argument("--feasibility", action="store_true")
    args = parser.parse_args()
    if args.feasibility:
        print(json.dumps(feasibility_report(), indent=2))
        return
    seeds = _seeds(args.seeds)
    print(json.dumps({
        "feasibility": feasibility_report(),
        "plans": [str(path) for path in write_plans(seeds)],
    }, indent=2))


if __name__ == "__main__":
    main()
