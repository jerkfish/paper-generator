"""CSC413 deterministic stage-5 planner.

Targets the modern 2022-2023 CSC413 format:

  PART A  15 TRUE/FALSE questions, 1 mark each      15 marks
  PART B  15 matching questions, 1 mark each        15 marks
  PART C  30 multiple-choice questions, 1 mark each 30 marks
  PART D   4 structured questions, 10 marks each    40 marks

Part D questions use three lettered subparts with the observed 2/3/5,
2/4/4, 3/3/4 and 3/3/4 mark patterns.  Every choice is derived from the
seed; the planner does not generate questions yet.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from src import config

SUBJECT = "CSC413"
PLANNER_VERSION = 1
MODERN_PAPERS = ("CSC413-2022-02", "CSC413-2023-02")
TRACKING = config.TRACKING_DIR / "csc413"

# Smoothed topic mix for the 60 one-mark objective slots, derived from the
# 2022/2023 papers.  Shuffled per seed.
OBJECTIVE_TOPICS = (
    ["multimedia_fundamentals"] * 10 +
    ["graphics"] * 8 +
    ["animation"] * 7 +
    ["authoring_interactivity"] * 7 +
    ["audio"] * 6 +
    ["hardware_devices"] * 6 +
    ["video"] * 5 +
    ["web_hypermedia"] * 5 +
    ["text"] * 3 +
    ["design_project"] +
    ["legal_ethics"] +
    ["virtual_reality"]
)

D_TOPIC_POOL = (
    "text", "animation", "graphics", "web_hypermedia",
    "authoring_interactivity", "design_project",
)

D_PATTERNS = ((2, 3, 5), (2, 4, 4), (3, 3, 4), (3, 3, 4))


def _slot(part: str, question: str, label: str, kind: str, marks: int,
          topic: str, task: str, title: str) -> dict:
    return {
        "slot": label,
        "part": part,
        "question": question,
        "kind": kind,
        "marks": marks,
        "topic": topic,
        "task": task,
        "title": title,
        "generator_id": f"csc413.{task}",
    }


def build_plan(seed: int, style: str = "modern") -> dict:
    if style != "modern":
        raise ValueError("CSC413 planner supports style 'modern' only")
    if int(seed) < 1:
        raise ValueError("seed must be a positive integer")
    rng = random.Random(int(seed))
    slots: list[dict] = []

    topics = list(OBJECTIVE_TOPICS)
    if len(topics) != 60:
        raise AssertionError("objective topic mix must contain 60 slots")
    rng.shuffle(topics)

    for index in range(15):
        slots.append(_slot(
            "A", f"A{index + 1}", f"A{index + 1}", "true_false", 1,
            topics[index], "true_false", "TRUE/FALSE question"))
    for index in range(15):
        slots.append(_slot(
            "B", f"B{index + 1}", f"B{index + 1}", "matching", 1,
            topics[15 + index], "matching", "Matching question"))
    for index in range(30):
        slots.append(_slot(
            "C", f"C{index + 1}", f"C{index + 1}", "mcq", 1,
            topics[30 + index], "mcq", "Multiple-choice question"))

    d_topics = rng.sample(D_TOPIC_POOL, 4)
    d_patterns = list(D_PATTERNS)
    rng.shuffle(d_patterns)
    for index in range(4):
        question = f"D{index + 1}"
        for sub_index, marks in enumerate(d_patterns[index]):
            label = f"{question}{chr(ord('a') + sub_index)}"
            slots.append(_slot(
                "D", question, label, "structured", marks,
                d_topics[index], "structured", "Structured question"))

    topic_marks: dict[str, int] = {}
    part_marks: dict[str, int] = {}
    for slot in slots:
        topic_marks[slot["topic"]] = (
            topic_marks.get(slot["topic"], 0) + slot["marks"])
        part_marks[slot["part"]] = (
            part_marks.get(slot["part"], 0) + slot["marks"])
    total = sum(part_marks.values())
    if total != 100 or part_marks != {"A": 15, "B": 15, "C": 30, "D": 40}:
        raise AssertionError(f"CSC413 planner produced invalid totals: {part_marks}")
    return {
        "subject": SUBJECT,
        "planner_version": PLANNER_VERSION,
        "generated_by": "src.subjects.csc413.planner",
        "style": style,
        "seed": int(seed),
        "target_format": {
            "A": {"questions": 15, "marks": 15},
            "B": {"questions": 15, "marks": 15},
            "C": {"questions": 30, "marks": 30},
            "D": {"questions": 4, "marks": 40},
        },
        "source_papers": list(MODERN_PAPERS),
        "source_evidence": [
            "data/tracking/csc413/taxonomy.json",
            "data/tracking/csc413/question_log.json",
            "data/tracking/csc413/taxonomy_summary.json",
        ],
        "part_marks": part_marks,
        "topic_marks": topic_marks,
        "total_marks": total,
        "question_count": 64,
        "slot_count": len(slots),
        "slots": slots,
        "notes": (
            "Targets the 2022-2023 format: 15 TRUE/FALSE, 15 matching, "
            "30 MCQs and four 10-mark structured questions with three "
            "lettered subparts each."),
    }


def write_plan(seed: int, style: str = "modern",
               out: Path | None = None) -> dict:
    plan = build_plan(seed, style=style)
    path = Path(out) if out is not None else (
        TRACKING / f"planner_seed_{seed:02d}.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    return {"plan": plan, "path": str(path)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--style", default="modern")
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    out = Path(args.out) if args.out else None
    result = write_plan(args.seed, args.style, out)
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
