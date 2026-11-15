"""V5 MAT133 assembly: five role-ordered recycled questions per seed.

Marks are not a selection parameter for MAT133 v2.  The arrangement follows
the owner's slot rules:

    Q1  inequalities, circles, complex numbers or parabolas
    Q2  coordinate geometry or functions; functions when Q1 used circles or
        parabolas
    Q3  functions; when Q2 already used functions, another Q2 topic
    Q4  systems of equations/inequalities, trigonometry or circular measure
    Q5  trigonometry

The shared recycle planner's mark-based selection is deliberately not used.

Run:
    uv run python -m src.subjects.mat133.assemble_v2 --seeds 1-3
"""
from __future__ import annotations

import argparse
import json
import random
import re
from collections import Counter
from pathlib import Path

from src import config
from src.bank.store import BankStore, load_json, save_json

TRACKING = config.TRACKING_DIR / "mat133" / "v2"
BANK = TRACKING / "bank"
FORMAT = TRACKING / "format_profile.json"
OUT = config.OUTPUTS_DIR / "review" / "mat133_v2" / "seeds"
REUSE_CAP = 4
SUBJECT = "MAT133"

Q1_TAGS = {"inequalities", "circles", "complex_numbers", "parabolas"}
Q2_TAGS = {"lines", "circles", "parabolas", "functions"}
Q2_GEOMETRY = {"lines", "circles", "parabolas"}
Q4_TAGS = {"systems_of_equations", "systems_of_inequalities",
           "trigonometry", "circular_measure"}
Q5_TAGS = {"trigonometry"}
ROLE_ORDER = ("Q1", "Q2", "Q3", "Q4", "Q5")
CURATED_SEEDS = {
    1: ["MAT133-2026-FEB-Q1", "MAT133-2016-OCT-Q3", "MAT133-2025-JUL-Q1",
        "MAT133-2017-MAR-Q5", "MAT133-2008-OCT-Q5"],
    2: ["MAT133-2024-JAN-Q1", "MAT133-2018-JUN-Q3", "MAT133-2022-FEB-Q2",
        "MAT133-2016-OCT-Q5", "MAT133-2012-OCT-Q5"],
    3: ["MAT133-2023-JUL-Q1", "MAT133-2010-OCT-Q2", "MAT133-2011-SEP-Q2",
        "MAT133-2024-JUL-Q5", "MAT133-2013-MAR-Q5"],
}



def _seeds(value: str) -> list[int]:
    if "-" in value:
        start, end = value.split("-", 1)
        return list(range(int(start), int(end) + 1))
    return [int(part) for part in value.split(",") if part.strip()]


def _tags(question: dict) -> set[str]:
    return set(question.get("topic_tags") or [])


def _has(question: dict, tags: set[str]) -> bool:
    return bool(_tags(question) & tags)


def structural_issues(question: dict) -> list[str]:
    """Printed structure that must exist before a question can be assembled."""
    issues = []
    parts = question.get("parts") or []
    if not parts:
        issues.append("no parts")
    for part in parts:
        label = part.get("label") or "?"
        text = str(part.get("text") or "").strip()
        if not text:
            issues.append(f"part {label} has no text")
        if not part.get("marks"):
            issues.append(f"part {label} has no marks")
        if text and not re.search(r"[$=<>≤≥]|\\[a-zA-Z]+", text) and re.search(
                r"\b(prove the identity|the identity|the equation|the system"
                r"|the inequalities|given below|shown below"
                r"|defined as below|as follows)\b", text, re.I):
            issues.append(
                f"part {label} refers to printed content that is missing")
        if re.search(r"defined as below|as follows", text, re.I):
            issues.append(
                f"part {label} defers to a definition that is missing")
        if re.search(r"(?mi)^\s*(and|or)\s*$", text):
            issues.append(
                f"part {label} has a conjunction with a missing expression")
        if re.search(r"(simultaneous equations|equations of circle)", text,
                     re.I) and not re.search(r"[$=]|\\[a-zA-Z]+", text):
            issues.append(
                f"part {label} states an equation problem without equations")
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


def _role_candidates(slot: str, rows: list[dict],
                     chosen: list[dict]) -> list[dict]:
    if slot == "Q1":
        pool = [q for q in rows if _has(q, Q1_TAGS)]
    elif slot == "Q2":
        q1 = chosen[0] if chosen else None
        if q1 and (_tags(q1) & {"circles", "parabolas"}):
            pool = [q for q in rows if _has(q, {"functions"})]
        else:
            pool = [q for q in rows if _has(q, Q2_TAGS)]
    elif slot == "Q3":
        q2 = chosen[1] if len(chosen) > 1 else None
        if q2 and _has(q2, {"functions"}):
            pool = [q for q in rows if _has(q, Q2_GEOMETRY)]
        else:
            pool = [q for q in rows if _has(q, {"functions"})]
    elif slot == "Q4":
        pool = [q for q in rows if _has(q, Q4_TAGS)]
    else:
        pool = [q for q in rows if _has(q, Q5_TAGS)]
    return pool


def _choose(slot: str, candidates: list[dict], chosen: list[dict],
            uses: Counter, last_used: dict[str, int], serial: int,
            rng: random.Random) -> dict:
    chosen_ids = {str(row["id"]) for row in chosen}
    papers = {str(row.get("source_paper") or "") for row in chosen}
    pool = [
        row for row in candidates
        if str(row["id"]) not in chosen_ids
        and uses[str(row["id"])] < REUSE_CAP
        and last_used.get(str(row["id"])) != serial - 1
    ]
    if not pool:
        pool = [
            row for row in candidates
            if str(row["id"]) not in chosen_ids
            and uses[str(row["id"])] < REUSE_CAP
        ]
    if not pool:
        raise ValueError(f"seed {serial} {slot}: no usable candidate")

    def score(row: dict):
        qid = str(row["id"])
        paper = str(row.get("source_paper") or "")
        return (
            0 if paper not in papers else 1,
            uses[qid],
            len(_tags(row) & (Q1_TAGS | Q2_TAGS | Q4_TAGS | Q5_TAGS)),
            rng.random(),
        )

    return min(pool, key=score)


def build_role_plans(*, seed_count: int) -> list[dict]:
    rows = usable_questions()
    uses: Counter[str] = Counter()
    last_used: dict[str, int] = {}
    plans = []
    by_id = {str(row["id"]): row for row in rows}
    for serial in range(1, int(seed_count) + 1):
        rng = random.Random(f"mat133:roles:{serial}")
        chosen: list[dict] = []
        slots: list[dict] = []
        curated = CURATED_SEEDS.get(serial)
        for index, slot in enumerate(ROLE_ORDER):
            if curated and index < len(curated):
                picked = by_id.get(curated[index])
                if picked is None:
                    raise ValueError(
                        f"curated question {curated[index]} is not usable")
            else:
                candidates = _role_candidates(slot, rows, chosen)
                picked = _choose(slot, candidates, chosen, uses, last_used,
                                 serial, rng)
            chosen.append(picked)
            slots.append({
                "slot": slot,
                "part": "Q",
                "marks": picked.get("marks"),
                "question_id": picked.get("id"),
                "source_paper": picked.get("source_paper"),
                "pages": picked.get("pages"),
                "topic": picked.get("topic_primary") or picked.get("topic"),
                "topic_tags": picked.get("topic_tags") or [],
                "assets": picked.get("assets") or [],
                "refs": picked.get("refs") or [],
                "content_hash": picked.get("content_hash"),
            })
        for slot in slots:
            qid = str(slot["question_id"])
            uses[qid] += 1
            last_used[qid] = serial
        plans.append({
            "schema_version": 2,
            "subject": SUBJECT,
            "seed": serial,
            "selection": "role_order_no_marks",
            "reuse_cap": REUSE_CAP,
            "total_marks": sum(int(slot["marks"] or 0) for slot in slots),
            "slots": slots,
        })
    return plans


def role_pool_report() -> dict:
    rows = usable_questions()
    pools = {}
    for slot in ROLE_ORDER:
        # Q2/Q3 are conditional, so report their unconditional pools.
        tags = {"Q1": Q1_TAGS, "Q2": Q2_TAGS, "Q3": {"functions"},
                "Q4": Q4_TAGS, "Q5": Q5_TAGS}[slot]
        pools[slot] = sorted(
            question["id"] for question in rows
            if _has(question, tags))
    return {
        "approved_questions": len(rows),
        "selection": "role_order_no_marks",
        "reuse_cap": REUSE_CAP,
        "pools": {slot: {"count": len(ids), "questions": ids}
                  for slot, ids in pools.items()},
        "structural_excluded": structural_exclusions(),
        "structural_excluded_count": len(structural_exclusions()),
        "answer_excluded": answer_exclusions(),
        "answer_excluded_count": len(answer_exclusions()),
    }


def feasibility_report() -> dict:
    report = role_pool_report()
    sizes = [row["count"] for row in report["pools"].values()]
    report["max_seeds_with_cap"] = min(
        size * REUSE_CAP for size in sizes) if sizes else 0
    report["feasible_seeds"] = min(20, report["max_seeds_with_cap"])
    report["distinct_seeds_without_reuse"] = min(sizes) if sizes else 0
    return report


def plans_for(seeds: list[int]) -> list[dict]:
    if not usable_questions():
        raise SystemExit(
            "no usable approved MAT133 questions; run V4 answers first")
    count = max(seeds) if seeds else 0
    plans = build_role_plans(seed_count=count)
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
