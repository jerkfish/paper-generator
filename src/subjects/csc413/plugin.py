"""Subject plugin scaffold for CSC413 (deterministic computed papers (no LLM)).

This file is the only place subject-specific pipeline code belongs.
Replace the stubs after the stage-0 intake checkpoint.  The shared app
loads this module through subjects/CSC413/subject.json.
"""
from __future__ import annotations



def build_seed(seed: int, out_dir=None, force: bool = False, **kwargs) -> dict:
    """Build one deterministic paper and write meta.json in ``out_dir``."""
    from src.subjects.csc413.build_docx import build_seed as _build_seed
    if out_dir is None:
        from src.app.jobs import cache_path
        out_dir = cache_path("realistic", seed, None, subject="CSC413")
    export = bool(kwargs.get("export", True))
    return _build_seed(seed, out_dir=out_dir, export=export, force=force)


def library_seeds() -> list[int]:
    """The private Library is the standard 20-seed set."""
    return list(range(1, 21))


def generator_labels() -> dict:
    return {
        "csc413.true_false": "TRUE/FALSE item",
        "csc413.matching": "Matching item",
        "csc413.mcq": "Multiple-choice question",
        "csc413.structured": "Structured question",
    }


def topic_labels() -> dict:
    return {
        "multimedia_fundamentals": "FUN",
        "text": "TXT",
        "graphics": "GRA",
        "audio": "AUD",
        "video": "VID",
        "animation": "ANI",
        "authoring_interactivity": "AUT",
        "hardware_devices": "HW",
        "web_hypermedia": "WEB",
        "design_project": "DES",
        "legal_ethics": "LEG",
        "virtual_reality": "VR",
    }
