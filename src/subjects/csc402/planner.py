"""CSC402 deterministic stage-5 planner.

Targets the modern (2022-2026) CSC402 format observed in the question log:

  PART A  10 multiple-choice questions, 10 marks
  PART B   5 structured questions, 60 marks, two lettered subparts each
  PART C   2 complete-program questions, 30 marks (15 each)

Every choice is derived from the seed.  The planner does not generate the
questions yet; it produces the slot contract for stage 6.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from src import config

SUBJECT = "CSC402"
PLANNER_VERSION = 1
MODERN_PAPERS = (
    "CSC402-2022-02", "CSC402-2023-02", "CSC402-2024-01",
    "CSC402-2024-07", "CSC402-2025-02", "CSC402-2025-07",
    "CSC402-2026-02",
)
TRACKING = config.TRACKING_DIR / "csc402"

# Part A topic mix observed across modern papers.  Shuffled per seed.
PART_A_TOPICS = (
    ["data_types"] * 3 + ["control_structures"] * 3 +
    ["fundamentals"] * 2 + ["arrays"] + ["input_output"]
)

B_SPECS = (
    {
        "question": "B1",
        "topics": ("fundamentals", "debugging_testing"),
        "patterns": ((2, 3), (3, 2)),
        "task": "short_answer",
        "title": "Definitions and programming concepts",
    },
    {
        "question": "B2",
        "topics": ("fundamentals", "control_structures"),
        "patterns": ((5, 8), (6, 7), (8, 5)),
        "task": "flowchart_or_pseudocode",
        "title": "Algorithm, flowchart or pseudocode",
    },
    {
        "question": "B3",
        "topics": ("data_types",),
        "patterns": ((5, 6), (6, 5)),
        "task": "code_statement",
        "title": "Variables, expressions and C++ statements",
    },
    {
        "question": "B4",
        "topics": ("control_structures", "input_output"),
        "patterns": ((6, 9), (7, 8), (10, 5)),
        "task": "trace_or_debug",
        "title": "Program tracing, output or correction",
    },
    {
        "question": "B5",
        "topics": ("arrays",),
        "patterns": ((6, 10), (8, 8), (10, 6)),
        "task": "array_program_segment",
        "title": "Array declarations and program segments",
    },
)

C_TOPICS = ("control_structures", "input_output", "arrays", "structures")


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
        "generator_id": f"csc402.{task}",
    }


def build_plan(seed: int, style: str = "modern") -> dict:
    if style != "modern":
        raise ValueError("CSC402 planner supports style 'modern' only")
    if int(seed) < 1:
        raise ValueError("seed must be a positive integer")
    rng = random.Random(int(seed))
    slots: list[dict] = []

    part_a_topics = list(PART_A_TOPICS)
    rng.shuffle(part_a_topics)
    for index, topic in enumerate(part_a_topics, start=1):
        slots.append(_slot(
            "A", f"A{index}", f"A{index}", "mcq", 1, topic, "mcq",
            "Multiple-choice question"))

    for spec in B_SPECS:
        question = spec["question"]
        topic = rng.choice(spec["topics"])
        pattern = rng.choice(spec["patterns"])
        for index, marks in enumerate(pattern):
            label = f"{question}{chr(ord('a') + index)}"
            slots.append(_slot(
                "B", question, label, "structured", marks, topic,
                spec["task"], spec["title"]))

    c_topics = list(C_TOPICS)
    rng.shuffle(c_topics)
    for index in range(2):
        question = f"C{index + 1}"
        slots.append(_slot(
            "C", question, question, "program", 15, c_topics[index],
            "complete_program", "Complete C++ program"))

    topic_marks: dict[str, int] = {}
    part_marks: dict[str, int] = {}
    for slot in slots:
        topic_marks[slot["topic"]] = topic_marks.get(slot["topic"], 0) + slot["marks"]
        part_marks[slot["part"]] = part_marks.get(slot["part"], 0) + slot["marks"]
    total = sum(part_marks.values())
    if total != 100 or part_marks != {"A": 10, "B": 60, "C": 30}:
        raise AssertionError(f"CSC402 planner produced invalid totals: {part_marks}")
    return {
        "subject": SUBJECT,
        "planner_version": PLANNER_VERSION,
        "generated_by": "src.subjects.csc402.planner",
        "style": style,
        "seed": int(seed),
        "target_format": {
            "A": {"questions": 10, "marks": 10},
            "B": {"questions": 5, "marks": 60},
            "C": {"questions": 2, "marks": 30},
        },
        "source_papers": list(MODERN_PAPERS),
        "source_evidence": [
            "data/tracking/csc402/taxonomy.json",
            "data/tracking/csc402/question_log.json",
            "data/tracking/csc402/taxonomy_summary.json",
        ],
        "part_marks": part_marks,
        "topic_marks": topic_marks,
        "total_marks": total,
        "question_count": 17,
        "slot_count": len(slots),
        "slots": slots,
        "notes": (
            "Targets the 2022-2026 format. Part A is 10 one-mark MCQs; "
            "Part B is five two-subpart structured questions totalling 60; "
            "Part C is two 15-mark complete-program questions."),
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
