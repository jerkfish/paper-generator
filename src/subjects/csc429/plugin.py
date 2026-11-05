"""CSC429 plugin adapter (hybrid deterministic/LLM subject).

The planner is deterministic.  The builder is implemented in stage 7; until
then ``build_seed`` fails closed.  The app loads this module through
``subjects/CSC429/subject.json``.
"""
from __future__ import annotations

import json

from src import config


def plan(mode: str, style: str, computed_marks: int | None, seed: int):
    """Return ``(slot_table, summary_dict)`` for the CSC429 planner."""
    from src.subjects.csc429.planner import build_plan
    summary = build_plan(
        int(seed), style=style, mode=mode, computed_marks=computed_marks)
    return summary["slots"], summary


def plan_markdown(summary: dict) -> str:
    from src.subjects.csc429.planner import to_markdown
    return to_markdown(summary)


def plan_inputs(seed: int) -> dict:
    """Return the deterministic planner path for one seed.

    CSC429 has no separate theory file; the plan contains every slot.
    """
    path = config.TRACKING_DIR / "csc429" / f"planner_seed_{int(seed):02d}.json"
    return {"plan": path, "theory": path}


def library_seeds() -> list[int]:
    """The private Library is prepared at stage 8."""
    return []


def library_metadata(seed: int) -> dict:
    path = config.TRACKING_DIR / "csc429" / f"planner_seed_{int(seed):02d}.json"
    if not path.is_file():
        return {}
    try:
        return dict(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return {}


def build_seed(seed: int, **kwargs) -> dict:
    """Build one paper and write meta.json; implemented in stage 7."""
    raise NotImplementedError(
        "CSC429 deterministic builder is not implemented; complete stages "
        "6-7 first")


def generator_labels() -> dict:
    return {
        "csc429.computer_generations_history": "History/generations question",
        "csc429.data_representation": "Data representation question",
        "csc429.cpu_organization": "CPU organization question",
        "csc429.memory_cache": "Memory/cache question",
        "csc429.interrupts_io": "Interrupts/I-O question",
        "csc429.buses_interconnection": "Bus/interconnection question",
        "csc429.parallel_architectures": "Parallel architectures question",
        "csc429.assembly": "Assembly program question",
    }


def topic_labels() -> dict:
    return {
        "computer_generations_history": "HIS",
        "data_representation": "DAT",
        "cpu_organization": "CPU",
        "memory_cache": "MEM",
        "interrupts_io": "I/O",
        "buses_interconnection": "BUS",
        "instruction_set_assembly": "ASM",
        "parallel_architectures": "PAR",
        "storage_devices": "STO",
        "other": "OTH",
    }
