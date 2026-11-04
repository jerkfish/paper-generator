"""Subject plugin scaffold for CSC413 (deterministic computed papers (no LLM)).

This file is the only place subject-specific pipeline code belongs.
Replace the stubs after the stage-0 intake checkpoint.  The shared app
loads this module through subjects/CSC413/subject.json.
"""
from __future__ import annotations



def build_seed(seed: int, **kwargs) -> dict:
    """Build one deterministic paper and write meta.json in ``out_dir``."""
    raise NotImplementedError(
        f"CSC413 deterministic builder is not implemented; complete "
        "stages 5-7 first")


def generator_labels() -> dict:
    return {}


def topic_labels() -> dict:
    return {}
