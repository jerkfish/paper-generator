"""Deterministic Stage-5 planner for ICT450.

The observed ICT450 papers have five structured questions worth 100 marks.
This planner emits five 20-mark theory slots. Topic selection is seeded and
weighted by the Stage-4 question log; the same seed always produces the same
topic sequence. No LLM is used here.
"""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path

from src import config

SUBJECT = "ICT450"
PLANNER_VERSION = 1
TRACKING = config.TRACKING_DIR / "ict450"
LOG_PATH = TRACKING / "question_log.json"
TAXONOMY_PATH = TRACKING / "taxonomy.json"
SLOT_COUNT = 5
SLOT_MARKS = 20
TOTAL_MARKS = SLOT_COUNT * SLOT_MARKS


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def topic_weights(log: dict) -> dict[str, int]:
    counts = Counter(
        entry["topic"] for entry in log["entries"]
        if entry.get("topic") and entry["topic"] != "other")
    if not counts:
        raise ValueError("ICT450 question log has no topic entries")
    return dict(counts)


def _topic_labels(taxonomy: dict) -> dict[str, str]:
    return {topic["key"]: topic["label"]
            for topic in taxonomy.get("topics", []) if topic.get("key")}


def _choose_topics(weights: dict[str, int], seed: int) -> list[str]:
    pool = [topic for topic, weight in weights.items() if weight > 0]
    if len(pool) < SLOT_COUNT:
        raise ValueError("not enough ICT450 topics for five slots")
    rng = random.Random(int(seed))
    chosen: list[str] = []
    while pool and len(chosen) < SLOT_COUNT:
        topic = rng.choices(pool, weights=[weights[t] for t in pool])[0]
        chosen.append(topic)
        pool.remove(topic)
    if len(chosen) != SLOT_COUNT:
        raise ValueError("could not allocate five distinct ICT450 topics")
    rng.shuffle(chosen)
    return chosen


def _slot(index: int, topic: str, label: str) -> dict:
    return {
        "slot": f"Q{index}",
        "part": "A",
        "question": str(index),
        "kind": "theory",
        "marks": SLOT_MARKS,
        "topic": topic,
        "topic_label": label,
        "task": "structured_question",
        "title": f"{label} — {SLOT_MARKS} marks",
        "resolver": "ict450.theory",
        "variant_policy": "grounded_theory",
        "asset_policy": "reuse_source_asset_optional",
        "generator_pool": [],
    }


def build_plan(seed: int, style: str = "modern") -> dict:
    if style != "modern":
        raise ValueError("ICT450 planner supports style 'modern' only")
    if int(seed) < 1:
        raise ValueError("seed must be a positive integer")
    log = _load(LOG_PATH)
    taxonomy = _load(TAXONOMY_PATH)
    weights = topic_weights(log)
    labels = _topic_labels(taxonomy)
    topics = _choose_topics(weights, int(seed))
    slots = [_slot(index, topic, labels.get(topic, topic))
             for index, topic in enumerate(topics, start=1)]
    topic_marks = Counter()
    for slot in slots:
        topic_marks[slot["topic"]] += slot["marks"]
    plan = {
        "subject": SUBJECT,
        "planner_version": PLANNER_VERSION,
        "generated_by": "src.subjects.ict450.planner",
        "style": style,
        "seed": int(seed),
        "target_format": {
            "questions": SLOT_COUNT,
            "marks": TOTAL_MARKS,
            "slot_marks": [SLOT_MARKS] * SLOT_COUNT,
        },
        "source_evidence": [
            "data/tracking/ict450/question_log.json",
            "data/tracking/ict450/taxonomy.json",
        ],
        "topic_quota": dict(Counter(slot["topic"] for slot in slots)),
        "part_marks": {"A": TOTAL_MARKS},
        "topic_marks": dict(topic_marks),
        "total_marks": TOTAL_MARKS,
        "question_count": len(slots),
        "slot_count": len(slots),
        "slots": slots,
        "notes": (
            "Five 20-mark structured questions. Topic order is a seeded "
            "weighted sample without replacement from the 60-question log. "
            "Every slot needs the grounded theory generator at Stage 6."),
    }
    validate_plan(plan)
    return plan


def validate_plan(plan: dict) -> None:
    if plan.get("subject") != SUBJECT:
        raise ValueError("wrong planner subject")
    slots = plan.get("slots") or []
    if len(slots) != SLOT_COUNT:
        raise ValueError(f"planner must contain {SLOT_COUNT} slots")
    if sum(slot["marks"] for slot in slots) != TOTAL_MARKS:
        raise ValueError("planner marks must sum to 100")
    if any(slot["marks"] != SLOT_MARKS for slot in slots):
        raise ValueError("every ICT450 slot must be 20 marks")
    topics = [slot["topic"] for slot in slots]
    if len(set(topics)) != SLOT_COUNT:
        raise ValueError("topic sequence must be distinct")
    taxonomy = _load(TAXONOMY_PATH)
    valid = {topic["key"] for topic in taxonomy.get("topics", [])}
    if any(topic not in valid or topic == "other" for topic in topics):
        raise ValueError("invalid ICT450 topic in plan")
    for slot in slots:
        if slot.get("resolver") != "ict450.theory":
            raise ValueError("ICT450 slots must resolve to the theory generator")
        if slot.get("kind") != "theory":
            raise ValueError("ICT450 slots must be theory slots")


def write_plan(seed: int, style: str = "modern",
               out: Path | None = None) -> dict:
    plan = build_plan(seed, style)
    path = Path(out) if out is not None else (
        TRACKING / f"planner_seed_{seed:02d}.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    return {"plan": plan, "path": str(path)}


def plan_markdown(plan: dict) -> str:
    lines = [
        f"# ICT450 seed {plan['seed']} planner",
        "",
        f"- Total marks: {plan['total_marks']}",
        f"- Slots: {plan['slot_count']} (five 20-mark questions)",
        f"- Part marks: {plan['part_marks']}",
        "",
        "| Slot | Marks | Topic | Resolver |",
        "|---|---:|---|---|",
    ]
    for slot in plan["slots"]:
        lines.append(
            f"| {slot['slot']} | {slot['marks']} | {slot['topic_label']} | "
            f"{slot['resolver']} |")
    lines.append("")
    lines.append("Every slot requires the grounded ICT450 theory generator.")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--out", default="")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    if args.markdown:
        plan = build_plan(args.seed)
        print(plan_markdown(plan))
        return
    result = write_plan(args.seed, out=Path(args.out) if args.out else None)
    print(json.dumps(result["plan"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
