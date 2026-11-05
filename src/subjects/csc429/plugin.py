"""CSC429 plugin scaffold.

The corrected hybrid design uses the real past-paper question pool with its
original diagrams, jumbled per seed, plus controlled generated variants.
Implementation starts after the stage-1 checkpoint; every entry point below
fails closed until then.
"""
from __future__ import annotations


def generator_labels() -> dict:
    return {}


def topic_labels() -> dict:
    return {}


def plan(mode: str, style: str, computed_marks: int | None, seed: int):
    raise NotImplementedError(
        "CSC429 planner is not implemented; complete stages 4-5 first")


def plan_markdown(summary: dict) -> str:
    return "".join(f"- {key}: {value}\n" for key, value in summary.items())


def plan_inputs(seed: int) -> dict:
    raise NotImplementedError("CSC429 plan inputs are not implemented")


def library_seeds() -> list[int]:
    return []


def library_metadata(seed: int) -> dict:
    return {}


def build_seed(seed: int, **kwargs) -> dict:
    raise NotImplementedError(
        "CSC429 builder is not implemented; complete stages 6-7 first")
