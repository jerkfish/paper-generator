"""CSC429 registry plugin adapter.

The planner is deterministic and the builder builds from the real past-paper
bank; no subject-specific imports leak into the shared app.
"""
from __future__ import annotations

from pathlib import Path


def generator_labels() -> dict:
    return {
        "csc429.number_base_conversion": "Number-base conversion",
        "csc429.signed_arithmetic": "Signed arithmetic and complements",
        "csc429.ieee754_single": "IEEE 754 single precision",
    }


def topic_labels() -> dict:
    return {
        "computer_generations": "GEN",
        "computer_architecture": "ARC",
        "data_representation": "DAT",
        "instruction_set_addressing": "ADR",
        "memory_system": "MEM",
        "io_system": "I/O",
        "parallel_architecture": "PAR",
        "assembly_programming": "ASM",
        "other": "OTH",
    }


def plan(mode: str, style: str, computed_marks: int | None, seed: int):
    from src.subjects.csc429.planner import build_plan, validate_plan
    if mode != "realistic":
        raise ValueError("CSC429 supports realistic mode only")
    if computed_marks is not None:
        raise ValueError("CSC429 is deterministic; computed marks are fixed")
    result = build_plan(int(seed), style=style)
    validate_plan(result)
    return result["slots"], result


def plan_markdown(summary: dict) -> str:
    from src.subjects.csc429.planner import plan_markdown as _markdown
    return _markdown(summary)


def plan_inputs(seed: int) -> dict[str, Path]:
    from src import config
    tracking = config.TRACKING_DIR / "csc429"
    return {
        "plan": tracking / f"planner_seed_{int(seed):02d}.json",
        "taxonomy": tracking / "taxonomy.json",
        "question_log": tracking / "question_log.json",
        "question_bank": tracking / "question_bank_draft.json",
    }


def library_seeds() -> list[int]:
    return []


def library_metadata(seed: int) -> dict:
    import json
    from src import config
    path = config.TRACKING_DIR / "csc429" / f"planner_seed_{int(seed):02d}.json"
    if not path.exists():
        return {}
    try:
        return dict(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return {}


def build_seed(seed: int, **kwargs) -> dict:
    raise NotImplementedError(
        "CSC429 builder is not implemented; complete stages 6-7 first")
