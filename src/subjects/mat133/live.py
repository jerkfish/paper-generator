"""On-demand MAT133 v2 seed generation for the local app.

Seeds 1-20 are pre-generated in the Library.  The same role planner can build
any other seed up to the deterministic cap without an LLM key; the seed is
rendered into the job run directory and cached like any other deterministic
subject.
"""
from __future__ import annotations

import json
import time
from functools import lru_cache
from pathlib import Path

from src.subjects.mat133.assemble_v2 import build_role_plans
from src.subjects.mat133.render_v5 import build_seed as _render_seed


@lru_cache(maxsize=1)
def seed_cap() -> int:
    """Largest seed the current bank can build under the role rules."""
    low, high, best = 1, 200, 0
    while low <= high:
        middle = (low + high) // 2
        try:
            build_role_plans(seed_count=middle)
        except ValueError:
            high = middle - 1
        else:
            best = middle
            low = middle + 1
    return best


def build_seed(seed: int, out_dir: Path | None = None,
               force: bool = True, scheme_only: bool = False) -> dict:
    seed = int(seed)
    cap = seed_cap()
    if seed < 1 or seed > cap:
        raise ValueError(
            f"MAT133 seed must be between 1 and {cap}")
    target = Path(out_dir) if out_dir is not None else None
    result = _render_seed(seed, out_dir=target, preview=False)
    qa = result["qa"]
    if qa["problems"]:
        raise RuntimeError(f"seed {seed} QA failed: {qa['problems']}")
    seed_dir = Path(result["meta"]).parent
    meta = json.loads((seed_dir / "meta.json").read_text(encoding="utf-8"))
    plan = json.loads((seed_dir / "plan.json").read_text(encoding="utf-8"))
    files = {
        "paper_docx": str(seed_dir / "paper.docx"),
        "paper_pdf": str(seed_dir / "paper.pdf"),
        "scheme_docx": str(seed_dir / "scheme.docx"),
        "scheme_pdf": str(seed_dir / "scheme.pdf"),
    }
    topics = {}
    for slot in plan["slots"]:
        topic = str(slot.get("topic") or "other")
        topics[topic] = topics.get(topic, 0) + int(slot.get("marks") or 0)
    meta.update({
        "subject": "MAT133",
        "seed": seed,
        "mode": "realistic",
        "model": "mat133-v2-role-recycle",
        "cost_usd": 0.0,
        "accepted": len(plan["slots"]),
        "placeholders": 0,
        "total_slots": len(plan["slots"]),
        "total_marks": plan["total_marks"],
        "has_practice_mode": False,
        "has_placeholders": False,
        "created": time.time(),
        "year": int(meta.get("year") or time.gmtime().tm_year),
        "topic_marks": topics,
        "summary": {"total_marks": plan["total_marks"]},
        "files": files,
        "progress": [{
            "question": slot["slot"],
            "slot": slot["slot"],
            "status": "accepted",
            "message": ", ".join(slot.get("topic_tags") or []),
            "cost_usd": 0,
            "calls": 0,
            "accepted": 1,
            "placeholders": 0,
        } for slot in plan["slots"]],
        "document_versions": {
            "2": {
                "label": "v2",
                "playbook_version": "2.0",
                "built": meta.get("created"),
                "files": files,
            }
        },
    })
    (seed_dir / "meta.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return {"seed": seed, "path": str(seed_dir), "cached": False,
            "files": files, "qa": qa}
