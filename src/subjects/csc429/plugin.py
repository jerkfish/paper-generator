"""Subject plugin scaffold for CSC429 (hybrid: deterministic + LLM theory).

This file is the only place subject-specific pipeline code belongs.  The
shared app loads it through ``subjects/CSC429/subject.json``.  Stage 0/1 do
not implement generation; the stubs below fail closed until later stages.
"""
from __future__ import annotations


def plan(mode: str, style: str, computed_marks: int | None, seed: int):
    """Return ``(plan_object, summary_dict)`` for the planner."""
    raise NotImplementedError(
        "CSC429 planner is not implemented; complete stages 4-5 first")


def plan_markdown(summary: dict) -> str:
    """Render the planner summary used by the local UI."""
    return "".join(f"- {key}: {value}\n" for key, value in summary.items())


def plan_inputs(seed: int) -> dict:
    """Return paths to {plan, theory} for prebuild/bundle rebuilds."""
    raise NotImplementedError("CSC429 plan inputs are not implemented")


def library_seeds() -> list[int]:
    """Return the accepted Library seed list (empty until stage 8)."""
    return []


def library_metadata(seed: int) -> dict:
    """Return planner metadata for one Library seed."""
    return {}


def build_seed(seed: int, **kwargs) -> dict:
    """Build one deterministic paper and write meta.json in ``out_dir``."""
    raise NotImplementedError(
        "CSC429 deterministic builder is not implemented; complete stages "
        "5-7 first")


def generator_labels() -> dict:
    return {}


def topic_labels() -> dict:
    return {}
