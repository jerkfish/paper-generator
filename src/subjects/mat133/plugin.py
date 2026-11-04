"""MAT133 plugin adapter.

MAT133 is the reference type-B subject: deterministic paper-derived
generators, no lecture slides and no LLM call.  The existing implementation
under ``src/mat133`` is reused; this adapter is the only entry point the
shared app sees, and it is declared in
``subjects/MAT133/subject.json``.
"""
from __future__ import annotations

from src.mat133.library import build_seed as _build_seed
from src.mat133.planner import GENERATOR_LABELS, TOPIC_SHORT

LIBRARY_SEEDS = list(range(1, 21))


def build_seed(seed: int, **kwargs) -> dict:
    return _build_seed(seed, **kwargs)


def library_seeds() -> list[int]:
    """The public Library is the standard 20-seed set."""
    return list(LIBRARY_SEEDS)


def generator_labels() -> dict:
    return dict(GENERATOR_LABELS)


def topic_labels() -> dict:
    return dict(TOPIC_SHORT)
