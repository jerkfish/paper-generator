"""P4: approved-only pool, feasibility and deterministic seed plans."""
from __future__ import annotations

import json
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from src import config

TRACKING = config.TRACKING_DIR / "csc429"
BANK = TRACKING / "bank"
QUESTIONS = BANK / "questions"
PLANS = BANK / "plans"
POOL = BANK / "pool.json"
FEASIBILITY = BANK / "feasibility.json"
MAX_SEEDS = 20


def _load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _save(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def approved_questions() -> list[dict]:
    rows = []
    for path in sorted(QUESTIONS.glob("*.json")):
        question = _load(path, {})
        if question.get("status") == "approved":
            rows.append(question)
    return rows


def build_pool() -> dict:
    approved = approved_questions()
    by_class = Counter()
    by_topic = Counter()
    for row in approved:
        by_class[f"{row['part']}:{row['marks']}"] += 1
        if row["part"] == "A":
            by_topic[row["topic_primary"]] += 1
    five = [row for row in approved
            if row["part"] == "A" and row["marks"] == 5]
    ten = [row for row in approved
           if row["part"] == "A" and row["marks"] == 10]
    twenty = [row for row in approved
              if row["part"] == "B" and row["marks"] == 20]
    distinct_seeds = min(len(five) // 4, len(ten) // 6, len(twenty))
    proposed_cap = 4
    feasible_20 = (
        len(five) * proposed_cap >= MAX_SEEDS * 4
        and len(ten) * proposed_cap >= MAX_SEEDS * 6
        and len(twenty) * proposed_cap >= MAX_SEEDS
    )
    payload = {
        "schema_version": 1,
        "subject": "CSC429",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "approved_questions": len(approved),
        "by_class": dict(sorted(by_class.items())),
        "by_topic": dict(sorted(by_topic.items())),
        "distinct_seeds_without_reuse": distinct_seeds,
        "proposed_reuse_cap": proposed_cap,
        "max_seeds_with_cap": min(
            len(five) * proposed_cap // 4,
            len(ten) * proposed_cap // 6,
            len(twenty) * proposed_cap,
        ),
        "twenty_seeds_feasible": feasible_20,
        "pools": {
            "five": len(five),
            "ten": len(ten),
            "twenty": len(twenty),
        },
        "questions": [
            {key: row[key] for key in (
                "id", "source_paper", "pages", "marks", "part",
                "topic_primary", "topic_tags", "assets", "refs",
                "content_hash")}
            for row in approved
        ],
    }
    _save(POOL, payload)
    _save(FEASIBILITY, payload)
    return payload


def _slot_record(label: str, question: dict) -> dict:
    return {
        "slot": label,
        "part": question["part"],
        "question_id": question["id"],
        "source_paper": question["source_paper"],
        "pages": question["pages"],
        "marks": question["marks"],
        "topic": question["topic_primary"],
        "topic_tags": question["topic_tags"],
        "assets": question["assets"],
        "refs": question["refs"],
        "content_hash": question["content_hash"],
    }


def build_plans(max_seeds: int = MAX_SEEDS,
                reuse_cap: int = 4) -> dict:
    pool = build_pool()
    approved = approved_questions()
    five = [row for row in approved
            if row["part"] == "A" and row["marks"] == 5]
    ten = [row for row in approved
           if row["part"] == "A" and row["marks"] == 10]
    twenty = [row for row in approved
              if row["part"] == "B" and row["marks"] == 20]
    if not (five and ten and twenty):
        raise RuntimeError("approved pool is missing a mark class")
    uses: Counter[str] = Counter()
    last_used: dict[str, int] = {}
    plans = []
    PLANS.mkdir(parents=True, exist_ok=True)
    for serial in range(1, max_seeds + 1):
        rng = random.Random(f"csc429:pure:plan:{serial}")
        chosen: list[dict] = []
        chosen_ids: set[str] = set()

        def pick(pool_rows: list[dict], label: str) -> dict:
            candidates = [
                row for row in pool_rows
                if row["id"] not in chosen_ids
                and uses[row["id"]] < reuse_cap
                and last_used.get(row["id"]) != serial - 1
            ]
            if not candidates:
                raise RuntimeError(
                    f"seed {serial} {label}: no approved candidate within cap")
            topic_counts = Counter(row["topic"] for row in chosen)
            def score(row):
                return (
                    topic_counts[row["topic_primary"]],
                    uses[row["id"]],
                    row["topic_primary"],
                    rng.random(),
                )
            return min(candidates, key=score)

        # B1: round-robin across the approved 20-mark questions.  Each B1
        # appears four times over 20 seeds and never in adjacent seeds.
        b1 = twenty[(serial - 1) % len(twenty)]
        if last_used.get(b1["id"]) == serial - 1:
            b1 = twenty[serial % len(twenty)]
        chosen.append(_slot_record("B1", b1))
        chosen_ids.add(b1["id"])
        for index in range(1, 5):
            question = pick(five, f"A{index}")
            chosen.append(_slot_record(f"A{index}", question))
            chosen_ids.add(question["id"])
        for index in range(5, 11):
            question = pick(ten, f"A{index}")
            chosen.append(_slot_record(f"A{index}", question))
            chosen_ids.add(question["id"])
        # Sort Part A slots by their assigned labels, then B1 last.
        chosen.sort(key=lambda row: (row["part"] != "A", int(row["slot"][1:])))
        for row in chosen:
            uses[row["question_id"]] += 1
            last_used[row["question_id"]] = serial
        paper = {
            "schema_version": 1,
            "subject": "CSC429",
            "seed": serial,
            "format": {"A": {"questions": 10, "marks": 80},
                        "B": {"questions": 1, "marks": 20}},
            "total_marks": 100,
            "reuse_cap": reuse_cap,
            "slots": chosen,
        }
        _save(PLANS / f"seed_{serial:02d}.json", paper)
        plans.append(paper)

    # Verify the constraints before reporting success.
    seen_in_seed = []
    for paper in plans:
        ids = [slot["question_id"] for slot in paper["slots"]]
        if len(ids) != len(set(ids)):
            raise AssertionError(f"seed {paper['seed']} repeats a question")
        if sum(slot["marks"] for slot in paper["slots"]) != 100:
            raise AssertionError(f"seed {paper['seed']} does not total 100")
        seen_in_seed.append(set(ids))
    for index in range(1, len(seen_in_seed)):
        overlap = seen_in_seed[index] & seen_in_seed[index - 1]
        if overlap:
            raise AssertionError(
                f"adjacent seeds {index} and {index + 1} reuse {overlap}")
    if max(uses.values()) > reuse_cap:
        raise AssertionError("reuse cap exceeded")
    index = {
        "schema_version": 1,
        "subject": "CSC429",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seeds": len(plans),
        "reuse_cap": reuse_cap,
        "max_uses": max(uses.values()),
        "distinct_questions_used": len(uses),
        "pool": pool["pools"],
        "plans": [
            {"seed": paper["seed"], "path": f"bank/plans/seed_{paper['seed']:02d}.json",
             "questions": [slot["question_id"] for slot in paper["slots"]]}
            for paper in plans
        ],
    }
    _save(PLANS / "index.json", index)
    return index


def main() -> None:
    print(json.dumps(build_plans(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
