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
