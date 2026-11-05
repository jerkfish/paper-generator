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
    import json
    from src import config
    seeds = set()
    root = config.WEB_CACHE_DIR / "CSC429"
    for meta in root.glob("*/meta.json"):
        try:
            payload = json.loads(meta.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if payload.get("subject") != "CSC429":
            continue
        try:
            seeds.add(int(payload.get("seed")))
        except (TypeError, ValueError):
            continue
    return sorted(seed for seed in seeds if seed > 0)


def library_metadata(seed: int) -> dict:
    import json
    from src import config
    candidates = []
    for meta in (config.WEB_CACHE_DIR / "CSC429").glob("*/meta.json"):
        try:
            payload = json.loads(meta.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if payload.get("subject") != "CSC429":
            continue
        if int(payload.get("seed", -1)) != int(seed):
            continue
        candidates.append((float(payload.get("created") or 0), payload))
    if candidates:
        return max(candidates, key=lambda row: row[0])[1]
    path = config.TRACKING_DIR / "csc429" / f"planner_seed_{int(seed):02d}.json"
    if not path.exists():
        return {}
    try:
        return dict(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return {}


def build_seed(seed: int, out_dir: Path | None = None,
               force: bool = False, **kwargs) -> dict:
    from src.subjects.csc429.build_docx import build_seed as _build_seed
    if out_dir is None:
        from src.app.jobs import cache_path
        out_dir = cache_path("realistic", seed, None, subject="CSC429")
    export = bool(kwargs.get("export", True))
    return _build_seed(seed, out_dir=out_dir, export=export, force=force)
