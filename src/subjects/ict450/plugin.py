"""Registry plugin adapter for ICT450."""
from __future__ import annotations

from pathlib import Path


def plan(mode: str, style: str, computed_marks: int | None, seed: int):
    from src.subjects.ict450.planner import build_plan, validate_plan
    if mode != "realistic":
        raise ValueError("ICT450 supports realistic mode only")
    if computed_marks not in (None, 0):
        raise ValueError("ICT450 has no computed-mark split")
    result = build_plan(int(seed), style=style)
    validate_plan(result)
    return result["slots"], result


def plan_markdown(summary: dict) -> str:
    from src.subjects.ict450.planner import plan_markdown as _markdown
    return _markdown(summary)


def plan_inputs(seed: int) -> dict[str, Path]:
    from src import config
    tracking = config.TRACKING_DIR / "ict450"
    return {
        "plan": tracking / f"planner_seed_{int(seed):02d}.json",
        "taxonomy": tracking / "taxonomy.json",
        "question_log": tracking / "question_log.json",
    }
