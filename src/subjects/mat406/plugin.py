"""Subject plugin for MAT406 (Type D recycle).

The Library prebuilder calls :func:`build_seed`; all questions come from the
shared approved bank through the MAT406 recycle assembler.
"""
from __future__ import annotations

import json
import time
from functools import lru_cache
from pathlib import Path

from src.app.filenames import utc_year
from src.app.jobs import cache_path

SEED_CAP = 12


def generator_labels() -> dict:
    return {}


def topic_labels() -> dict:
    return {}


@lru_cache(maxsize=1)
def seed_cap() -> int:
    """Feasible seed count for the approved bank under the reuse cap.

    The Gate B feasibility report establishes 12 feasible seeds.  Keeping
    this as a constant avoids re-running the expensive plan search every
    time the Library opens; the assembler still validates each seed.
    """
    return SEED_CAP


def library_seeds() -> list[int]:
    return list(range(1, seed_cap() + 1))


def build_seed(seed: int, out_dir: Path | None = None,
               force: bool = True, scheme_only: bool = False) -> dict:
    """Build one MAT406 seed into the Library cache."""
    from src.subjects.mat406.assemble_v5 import build_seed as _build_seed

    seed = int(seed)
    cap = seed_cap()
    if seed < 1 or seed > cap:
        raise ValueError(f"MAT406 seed must be between 1 and {cap}")
    target = (Path(out_dir) if out_dir is not None else
              cache_path("realistic", seed, None, subject="MAT406"))
    target.mkdir(parents=True, exist_ok=True)
    if not force and (target / "meta.json").is_file():
        return {"seed": seed, "path": str(target), "cached": True}

    result = _build_seed(seed, out_dir=target)
    qa = result["qa"]
    if qa.get("problems"):
        raise RuntimeError(f"MAT406 seed {seed} QA failed: {qa['problems']}")

    meta_path = target / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    plan = json.loads((target / "plan.json").read_text(encoding="utf-8"))
    created = time.time()
    topics: dict[str, int] = {}
    for slot in plan.get("slots") or []:
        for topic in slot.get("topic_tags") or ["other"]:
            topics[topic] = topics.get(topic, 0) + int(slot.get("marks") or 0)
    files = {
        "paper_docx": str(target / "paper.docx"),
        "paper_pdf": str(target / "paper.pdf"),
        "scheme_docx": str(target / "scheme.docx"),
        "scheme_pdf": str(target / "scheme.pdf"),
    }
    meta.update({
        "subject": "MAT406",
        "seed": seed,
        "mode": "realistic",
        "model": "mat406-v2-role-recycle",
        "cost_usd": 0.0,
        "accepted": len(plan.get("slots") or []),
        "placeholders": 0,
        "total_slots": len(plan.get("slots") or []),
        "total_marks": plan.get("total_marks", 0),
        "paper_pages": result.get("paper_pages", 0),
        "scheme_pages": result.get("scheme_pages", 0),
        "has_practice_mode": False,
        "has_placeholders": False,
        "created": created,
        "year": utc_year(created),
        "topic_marks": topics,
        "summary": {"total_marks": plan.get("total_marks", 0)},
        "files": files,
        "progress": [{
            "question": slot["question_id"],
            "slot": slot["slot"],
            "status": "accepted",
            "message": ", ".join(slot.get("topic_tags") or []),
            "cost_usd": 0,
            "calls": 0,
            "accepted": 1,
            "placeholders": 0,
        } for slot in plan.get("slots") or []],
        "document_versions": {
            "2": {
                "label": "v2",
                "playbook_version": "2.0",
                "built": created,
                "files": files,
            }
        },
    })
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return {"seed": seed, "path": str(target), "cached": False,
            "files": files, "qa": qa}
