"""CSC429 deterministic stage-5 planner.

Targets the modern 2023-2026 CSC429 format:

  PART A  10 structured questions: 5,5,5,5,10,10,10,10,10,10 = 80 marks
  PART B   1 assembly question:                              20 marks

The topic sequences are derived from the clean modern papers in the stage-4
question log.  The seed chooses one observed sequence; the mark pattern is
fixed because every clean modern paper uses it.  No LLM is called.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from src import config

SUBJECT = "CSC429"
PLANNER_VERSION = 1
TRACKING = config.TRACKING_DIR / "csc429"

MODERN_PAPERS = (
    "CSC429-2023-02", "CSC429-2023-07", "CSC429-2024-01",
    "CSC429-2024-07", "CSC429-2025-02", "CSC429-2025-07",
    "CSC429-2026-02",
)

PART_A_MARKS = (5, 5, 5, 5, 10, 10, 10, 10, 10, 10)
PART_B_MARKS = 20

TOPIC_SEQUENCES = (
    {
        "id": "2024_01",
        "source": "CSC429-2024-01",
        "topics": [
            "computer_generations_history",
            "computer_generations_history",
            "data_representation",
            "data_representation",
            "data_representation",
            "buses_interconnection",
            "cpu_organization",
            "memory_cache",
            "interrupts_io",
            "parallel_architectures",
        ],
    },
    {
        "id": "2025_02",
        "source": "CSC429-2025-02",
        "topics": [
            "computer_generations_history",
            "cpu_organization",
            "data_representation",
            "data_representation",
            "data_representation",
            "cpu_organization",
            "memory_cache",
            "interrupts_io",
            "interrupts_io",
            "parallel_architectures",
        ],
    },
    {
        "id": "2023_02",
        "source": "CSC429-2023-02",
        "topics": [
            "computer_generations_history",
            "computer_generations_history",
            "data_representation",
            "data_representation",
            "data_representation",
            "cpu_organization",
            "memory_cache",
            "interrupts_io",
            "interrupts_io",
            "parallel_architectures",
        ],
    },
    {
        "id": "2024_07",
        "source": "CSC429-2024-07",
        "topics": [
            "computer_generations_history",
            "cpu_organization",
            "data_representation",
            "data_representation",
            "data_representation",
            "cpu_organization",
            "buses_interconnection",
            "memory_cache",
            "interrupts_io",
            "parallel_architectures",
        ],
    },
)

TITLES = {
    "computer_generations_history": "Computer generations and history",
    "data_representation": "Data representation and number systems",
    "cpu_organization": "CPU organization and machine cycle",
    "memory_cache": "Memory hierarchy and cache",
    "interrupts_io": "Interrupts, I/O and DMA",
    "buses_interconnection": "Buses and system interconnection",
    "instruction_set_assembly": "Instruction set and assembly programming",
    "parallel_architectures": "Parallel architectures",
    "storage_devices": "Storage and I/O devices",
    "other": "Other",
}


def _slot(part: str, number: int, kind: str, marks: int, topic: str) -> dict:
    task = "assembly" if part == "B" else topic
    return {
        "slot": f"{part}{number}",
        "part": part,
        "question": f"{part}{number}",
        "kind": kind,
        "marks": marks,
        "topic": topic,
        "task": task,
        "title": TITLES.get(topic, topic),
        "generator_id": f"csc429.{task}",
    }


def build_plan(seed: int, style: str = "modern",
               mode: str = "realistic",
               computed_marks: int | None = None) -> dict:
    if style != "modern":
        raise ValueError("CSC429 planner supports style 'modern' only")
    if mode not in {"realistic", "practice"}:
        raise ValueError("mode must be realistic or practice")
    if int(seed) < 1:
        raise ValueError("seed must be a positive integer")
    if computed_marks is not None:
        computed_marks = int(computed_marks)
        if not 0 <= computed_marks <= 100:
            raise ValueError("computed_marks must be between 0 and 100")

    rng = random.Random(int(seed))
    sequence = rng.choice(TOPIC_SEQUENCES)
    slots: list[dict] = []
    for index, (marks, topic) in enumerate(
            zip(PART_A_MARKS, sequence["topics"]), start=1):
        slots.append(_slot("A", index, "structured", marks, topic))
    slots.append(_slot("B", 1, "assembly", PART_B_MARKS,
                       "instruction_set_assembly"))

    topic_marks: dict[str, int] = {}
    part_marks: dict[str, int] = {}
    for slot in slots:
        topic_marks[slot["topic"]] = (
            topic_marks.get(slot["topic"], 0) + slot["marks"])
        part_marks[slot["part"]] = (
            part_marks.get(slot["part"], 0) + slot["marks"])
    total = sum(part_marks.values())
    if total != 100 or part_marks != {"A": 80, "B": 20}:
        raise AssertionError(f"CSC429 planner produced invalid totals: {part_marks}")

    computed_value = 100 if computed_marks is None else computed_marks
    return {
        "subject": SUBJECT,
        "planner_version": PLANNER_VERSION,
        "generated_by": "src.subjects.csc429.planner",
        "style": style,
        "mode": mode,
        "seed": int(seed),
        "target_format": {
            "A": {"questions": 10, "marks": 80},
            "B": {"questions": 1, "marks": 20},
        },
        "source_papers": list(MODERN_PAPERS),
        "source_evidence": [
            "data/tracking/csc429/taxonomy.json",
            "data/tracking/csc429/question_log.json",
            "data/tracking/csc429/taxonomy_summary.json",
        ],
        "sequence_id": sequence["id"],
        "sequence_source": sequence["source"],
        "part_marks": part_marks,
        "topic_marks": topic_marks,
        "assigned_topic_marks": topic_marks,
        "total_marks": total,
        "computed_marks": computed_value,
        "requested_computed_marks": computed_marks,
        "question_count": 11,
        "slot_count": len(slots),
        "total_slots": len(slots),
        "slots": slots,
        "notes": (
            "Modern 2023-2026 format: ten Part A structured questions using "
            "the observed 5,5,5,5,10,10,10,10,10,10 mark pattern and one "
            "20-mark Part B assembly question. The seed selects one observed "
            "topic sequence."
        ),
    }


def write_plan(seed: int, style: str = "modern", mode: str = "realistic",
               computed_marks: int | None = None,
               out: Path | None = None) -> dict:
    plan = build_plan(seed, style=style, mode=mode,
                      computed_marks=computed_marks)
    path = Path(out) if out is not None else (
        TRACKING / f"planner_seed_{int(seed):02d}.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    return {"plan": plan, "path": str(path)}


def validate_seeds(start: int = 1, end: int = 20) -> dict:
    results = []
    failures = []
    for seed in range(start, end + 1):
        plan = build_plan(seed)
        repeat = build_plan(seed)
        slots = plan["slots"]
        part_a = [slot for slot in slots if slot["part"] == "A"]
        part_b = [slot for slot in slots if slot["part"] == "B"]
        checks = {
            "deterministic": plan == repeat,
            "slot_count_11": len(slots) == 11,
            "part_a_10": len(part_a) == 10,
            "part_b_1": len(part_b) == 1,
            "part_a_80": sum(s["marks"] for s in part_a) == 80,
            "part_b_20": sum(s["marks"] for s in part_b) == 20,
            "total_100": sum(s["marks"] for s in slots) == 100,
            "assembly_b1": (
                part_b[0]["topic"] == "instruction_set_assembly"
                and part_b[0]["marks"] == 20),
            "observed_sequence": plan["sequence_id"] in {
                item["id"] for item in TOPIC_SEQUENCES},
        }
        passed = all(checks.values())
        if not passed:
            failures.append({"seed": seed,
                             "failed": [key for key, value in checks.items()
                                        if not value]})
        results.append({
            "seed": seed,
            "passed": passed,
            "sequence_id": plan["sequence_id"],
            "part_marks": plan["part_marks"],
            "topic_marks": plan["topic_marks"],
        })
        if passed:
            write_plan(seed)
    validation = {
        "subject": SUBJECT,
        "generated_by": "src.subjects.csc429.planner",
        "seeds": [start, end],
        "passed": sum(1 for row in results if row["passed"]),
        "failed": failures,
        "results": results,
    }
    (TRACKING / "planner_validation.json").write_text(
        json.dumps(validation, indent=2), encoding="utf-8")
    _update_fingerprint(validation)
    return validation


def _update_fingerprint(validation: dict) -> None:
    path = config.PROJECT_ROOT / "subjects" / SUBJECT / "subject.json"
    if not path.is_file():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    fingerprint = dict(data.get("fingerprint") or {})
    fingerprint["planner"] = {
        "module": "src.subjects.csc429.planner",
        "style": "modern",
        "seed_range": validation["seeds"],
        "seeds_passed": validation["passed"],
        "slot_marks": list(PART_A_MARKS) + [PART_B_MARKS],
        "part_marks": {"A": 80, "B": 20},
        "question_count": 11,
        "slot_count": 11,
        "topic_sequences": [
            {"id": item["id"], "source": item["source"],
             "topics": item["topics"]}
            for item in TOPIC_SEQUENCES
        ],
        "source_papers": list(MODERN_PAPERS),
    }
    data["fingerprint"] = fingerprint
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def to_markdown(summary: dict) -> str:
    lines = [
        f"# CSC429 plan — seed {summary.get('seed')}",
        "",
        f"- Sequence: `{summary.get('sequence_id')}` "
        f"(source {summary.get('sequence_source')})",
        f"- Part marks: {summary.get('part_marks')}",
        f"- Total marks: {summary.get('total_marks')}",
        f"- Slots: {summary.get('slot_count')}",
        "",
        "| Slot | Marks | Topic | Task |",
        "|---|---:|---|---|",
    ]
    for slot in summary.get("slots", []):
        lines.append(
            f"| {slot['slot']} | {slot['marks']} | {slot['topic']} | "
            f"{slot['title']} |")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--style", default="modern")
    ap.add_argument("--mode", default="realistic",
                    choices=["realistic", "practice"])
    ap.add_argument("--computed-marks", type=int, default=None)
    ap.add_argument("--out", default="")
    ap.add_argument("--validate", action="store_true")
    args = ap.parse_args()
    if args.validate:
        result = validate_seeds()
        print(json.dumps({
            "seeds": result["seeds"],
            "passed": result["passed"],
            "failed": result["failed"],
        }, indent=2))
        return
    out = Path(args.out) if args.out else None
    result = write_plan(args.seed, args.style, args.mode,
                        args.computed_marks, out)
    print(json.dumps({
        "path": result["path"],
        "seed": result["plan"]["seed"],
        "sequence_id": result["plan"]["sequence_id"],
        "part_marks": result["plan"]["part_marks"],
        "topic_marks": result["plan"]["topic_marks"],
        "slot_count": result["plan"]["slot_count"],
        "question_count": result["plan"]["question_count"],
    }, indent=2))


if __name__ == "__main__":
    main()
