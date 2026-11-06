"""Deterministic Stage-5 planner for CSC429.

The plan is an 11-slot contract for the real-question bank:

  PART A  4 x 5-mark questions + 6 x 10-mark questions = 80
  PART B  1 x 20-mark assembly-programming question     = 20

Topic quotas are derived from the Stage-4 Part A log rather than hard-coded:
the ten most common topic slots are allocated by largest remainder, then the
5-mark and 10-mark pools are filled using each topic's observed 5/10-mark
availability. The same seed always produces the same slot/topic/marks plan.
"""
from __future__ import annotations

import argparse
import json
import random
import re
from collections import Counter
from pathlib import Path

from src import config
from src.subjects.csc429.generators import GENERATOR_IDS
from src.subjects.csc429.taxonomy import TOPICS

SUBJECT = "CSC429"
PLANNER_VERSION = 1
TRACKING = config.TRACKING_DIR / "csc429"
LOG_PATH = TRACKING / "question_log.json"
TAXONOMY_PATH = TRACKING / "taxonomy.json"
SUMMARY_PATH = TRACKING / "taxonomy_summary.json"
PLAN_PATH = TRACKING / "planner_seed_01.json"
PART_A_SLOTS = 10
FIVE_MARK_SLOTS = 4
TEN_MARK_SLOTS = 6

SINGLE_MARK_TITLES = {
    "A1": "Five-mark question 1",
    "A2": "Five-mark question 2",
    "A3": "Five-mark question 3",
    "A4": "Five-mark question 4",
    "A5": "Ten-mark question 5",
    "A6": "Ten-mark question 6",
    "A7": "Ten-mark question 7",
    "A8": "Ten-mark question 8",
    "A9": "Ten-mark question 9",
    "A10": "Ten-mark question 10",
    "B1": "Twenty-mark assembly-programming question",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _largest_remainder(counts: dict[str, int], total_slots: int) -> dict[str, int]:
    total = sum(counts.values())
    if total <= 0:
        raise ValueError("cannot allocate topic quotas from an empty log")
    raw = {key: value * total_slots / total for key, value in counts.items()}
    quota = {key: int(value) for key, value in raw.items()}
    remaining = total_slots - sum(quota.values())
    order = sorted(raw, key=lambda key: (-(raw[key] - quota[key]), key))
    for key in order[:remaining]:
        quota[key] += 1
    return {key: value for key, value in quota.items() if value > 0}


def topic_quota(log: dict) -> dict[str, int]:
    """Give every observed topic one slot, then allocate the extras by size."""
    counts = Counter(
        entry["topic"] for entry in log["entries"] if entry["part"] == "A")
    observed = {key: value for key, value in counts.items()
                if value > 0 and key != "other"}
    if len(observed) > PART_A_SLOTS:
        return _largest_remainder(observed, PART_A_SLOTS)
    quota = {key: 1 for key in observed}
    remaining = PART_A_SLOTS - len(quota)
    order = sorted(observed, key=lambda key: (-observed[key], key))
    for key in order[:remaining]:
        quota[key] += 1
    return quota


def mark_pools(log: dict, quota: dict[str, int]) -> tuple[list[str], list[str]]:
    """Split each topic quota into 5-mark and 10-mark slots by availability."""
    five_available = Counter(
        entry["topic"] for entry in log["entries"]
        if entry["part"] == "A" and entry["marks"] == 5)
    ten_available = Counter(
        entry["topic"] for entry in log["entries"]
        if entry["part"] == "A" and entry["marks"] == 10)
    remaining = dict(quota)
    five_topics: list[str] = []
    five_left = FIVE_MARK_SLOTS

    def ratio(topic: str) -> float:
        total = five_available[topic] + ten_available[topic]
        return five_available[topic] / total if total else 0.0

    for topic in sorted(quota, key=lambda key: (-ratio(key), key)):
        if five_left <= 0:
            break
        if remaining[topic] > 0 and five_available[topic] > 0:
            five_topics.append(topic)
            remaining[topic] -= 1
            five_left -= 1
    if five_left:
        for topic in sorted(quota, key=lambda key: (-ratio(key), key)):
            while five_left and remaining[topic] > 0 and five_available[topic] > 0:
                five_topics.append(topic)
                remaining[topic] -= 1
                five_left -= 1
    if five_left:
        raise ValueError("not enough 5-mark questions for the topic quotas")
    ten_topics = [
        topic for topic in sorted(remaining) for _ in range(remaining[topic])
    ]
    if len(five_topics) != FIVE_MARK_SLOTS or len(ten_topics) != TEN_MARK_SLOTS:
        raise ValueError(
            f"invalid mark allocation: {len(five_topics)} five-mark, "
            f"{len(ten_topics)} ten-mark")
    return five_topics, ten_topics


def _slot(label: str, part: str, marks: int, topic: str) -> dict:
    if topic not in TOPICS or topic == "other":
        raise ValueError(f"unknown taxonomy topic: {topic}")
    generated = topic == "data_representation"
    return {
        "slot": label,
        "part": part,
        "question": label,
        "kind": "generated_question" if generated else "real_bank_question",
        "marks": marks,
        "topic": topic,
        "topic_label": TOPICS[topic]["title"],
        "task": "assembly_program" if part == "B" else "short_answer",
        "title": SINGLE_MARK_TITLES[label],
        "resolver": "csc429.generator" if generated else "csc429.real_bank",
        "variant_policy": "controlled_numeric" if generated else "verbatim",
        "generator_pool": list(GENERATOR_IDS) if generated else [],
        "asset_policy": "figure_capture_table_recreate_mixed_text_recreate",
    }


def build_plan(seed: int, style: str = "modern") -> dict:
    if style != "modern":
        raise ValueError("CSC429 planner supports style 'modern' only")
    if int(seed) < 1:
        raise ValueError("seed must be a positive integer")
    log = _load(LOG_PATH)
    quota = topic_quota(log)
    five_topics, ten_topics = mark_pools(log, quota)
    rng = random.Random(int(seed))
    rng.shuffle(five_topics)
    rng.shuffle(ten_topics)
    slots = []
    for index, topic in enumerate(five_topics, start=1):
        slots.append(_slot(f"A{index}", "A", 5, topic))
    for index, topic in enumerate(ten_topics, start=5):
        slots.append(_slot(f"A{index}", "A", 10, topic))
    slots.append(_slot("B1", "B", 20, "assembly_programming"))

    part_marks = Counter()
    topic_marks = Counter()
    for slot in slots:
        part_marks[slot["part"]] += slot["marks"]
        topic_marks[slot["topic"]] += slot["marks"]
    if part_marks != {"A": 80, "B": 20} or sum(part_marks.values()) != 100:
        raise AssertionError(f"invalid CSC429 part marks: {dict(part_marks)}")
    if len(slots) != 11:
        raise AssertionError(f"invalid CSC429 slot count: {len(slots)}")
    if Counter(slot["topic"] for slot in slots if slot["part"] == "A") != Counter(quota):
        raise AssertionError("CSC429 topic quotas do not match the plan")
    return {
        "subject": SUBJECT,
        "planner_version": PLANNER_VERSION,
        "generated_by": "src.subjects.csc429.planner",
        "style": style,
        "seed": int(seed),
        "target_format": {
            "A": {"questions": 10, "marks": 80,
                  "slot_marks": [5, 5, 5, 5, 10, 10, 10, 10, 10, 10]},
            "B": {"questions": 1, "marks": 20},
        },
        "source_evidence": [
            "data/tracking/csc429/taxonomy.json",
            "data/tracking/csc429/question_log.json",
            "data/tracking/csc429/taxonomy_summary.json",
        ],
        "topic_quota": quota,
        "part_marks": dict(part_marks),
        "topic_marks": dict(topic_marks),
        "total_marks": sum(part_marks.values()),
        "question_count": len(slots),
        "slot_count": len(slots),
        "slots": slots,
        "notes": (
            "Real past-paper questions only. Topic quotas are the largest-"
            "remainder allocation of the observed Part A topic mix; each quota "
            "is split between 5- and 10-mark slots using the topic's observed "
            "5/10-mark availability. Every slot resolves to the real bank."),
    }


def write_plan(seed: int, style: str = "modern",
               out: Path | None = None) -> dict:
    plan = build_plan(seed, style)
    path = Path(out) if out is not None else (
        TRACKING / f"planner_seed_{seed:02d}.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2, ensure_ascii=False),
                    encoding="utf-8")
    return {"plan": plan, "path": str(path)}


def plan_markdown(plan: dict) -> str:
    lines = [
        f"# CSC429 seed {plan['seed']} planner",
        "",
        f"- Total marks: {plan['total_marks']}",
        f"- Slots: {plan['slot_count']}",
        f"- Part marks: {plan['part_marks']}",
        "",
        "| Slot | Part | Marks | Topic | Resolver |",
        "|---|---:|---:|---|---|",
    ]
    for slot in plan["slots"]:
        lines.append(
            f"| {slot['slot']} | {slot['part']} | {slot['marks']} | "
            f"{slot['topic_label']} | {slot['resolver']} |")
    lines.append("")
    lines.append("Every slot resolves to a real question in the CSC429 bank.")
    return "\n".join(lines) + "\n"


def validate_plan(plan: dict) -> None:
    if plan.get("subject") != SUBJECT:
        raise ValueError("wrong planner subject")
    slots = plan.get("slots") or []
    if len(slots) != 11:
        raise ValueError("planner must contain 11 slots")
    if sum(slot["marks"] for slot in slots) != 100:
        raise ValueError("planner marks must sum to 100")
    labels = [slot["slot"] for slot in slots]
    if labels != ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10", "B1"]:
        raise ValueError("unexpected CSC429 slot order")
    if [slot["marks"] for slot in slots[:4]] != [5, 5, 5, 5]:
        raise ValueError("Part A must start with four 5-mark slots")
    if [slot["marks"] for slot in slots[4:10]] != [10] * 6:
        raise ValueError("Part A must end with six 10-mark slots")
    if slots[10]["marks"] != 20 or slots[10]["topic"] != "assembly_programming":
        raise ValueError("B1 must be the 20-mark assembly question")
    for slot in slots:
        if slot["topic"] not in TOPICS or slot["topic"] == "other":
            raise ValueError(f"invalid topic in slot {slot['slot']}")
        expected = ("csc429.generator" if slot["topic"] == "data_representation"
                    else "csc429.real_bank")
        if slot["resolver"] != expected:
            raise ValueError(
                f"slot {slot['slot']} has resolver {slot['resolver']!r}, "
                f"expected {expected!r}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--style", default="modern")
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    out = Path(args.out) if args.out else None
    result = write_plan(args.seed, args.style, out)
    validate_plan(result["plan"])
    print(json.dumps({
        "path": result["path"],
        "seed": result["plan"]["seed"],
        "part_marks": result["plan"]["part_marks"],
        "topic_marks": result["plan"]["topic_marks"],
        "slot_count": result["plan"]["slot_count"],
        "question_count": result["plan"]["question_count"],
    }, indent=2))


if __name__ == "__main__":
    main()
