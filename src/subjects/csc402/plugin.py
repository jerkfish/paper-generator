"""CSC402 registry plugin adapter.

The shared app resolves these entry points from
``subjects/CSC402/subject.json``.  No subject code is imported by the app.
"""
from __future__ import annotations

from pathlib import Path


def build_seed(seed: int, out_dir: Path | None = None,
               force: bool = False, **kwargs) -> dict:
    from src.subjects.csc402.build_docx import build_seed as _build_seed
    if out_dir is None:
        # Lazy import avoids a jobs -> plugins -> plugin import cycle.
        from src.app.jobs import cache_path
        out_dir = cache_path("realistic", seed, None, subject="CSC402")
    export = bool(kwargs.get("export", True))
    return _build_seed(seed, out_dir=out_dir, export=export, force=force)


def generator_labels() -> dict:
    return {
        "csc402.mcq.fundamentals": "MCQ — programming fundamentals",
        "csc402.mcq.data_types": "MCQ — data types and expressions",
        "csc402.mcq.control_structures": "MCQ — control structures",
        "csc402.mcq.arrays": "MCQ — arrays",
        "csc402.mcq.input_output": "MCQ — input/output",
        "csc402.mcq.debugging_testing": "MCQ — debugging/testing",
        "csc402.mcq.structures": "MCQ — structures",
        "csc402.short_answer": "Short answer",
        "csc402.flowchart_or_pseudocode": "Flowchart / pseudocode",
        "csc402.code_statement": "C++ statements",
        "csc402.trace_or_debug": "Tracing / debugging",
        "csc402.array_program_segment": "Array program segment",
        "csc402.complete_program.control_structures": "Complete program — control",
        "csc402.complete_program.input_output": "Complete program — input/output",
        "csc402.complete_program.arrays": "Complete program — arrays",
        "csc402.complete_program.structures": "Complete program — structures",
    }


def topic_labels() -> dict:
    return {
        "fundamentals": "FUN",
        "data_types": "DAT",
        "control_structures": "CTL",
        "functions": "FNC",
        "arrays": "ARR",
        "input_output": "I/O",
        "debugging_testing": "DBG",
        "file_handling": "FIL",
        "structures": "STR",
        "other": "OTH",
    }
