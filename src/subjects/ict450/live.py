"""On-demand ICT450 v2 seed generation for the local app.

Seeds 1-20 are prebuilt in the Library.  The category planner can build any
seed up to the deterministic cap from the approved bank, without an LLM key.
"""
from __future__ import annotations

import json
import time
from collections import Counter
from functools import lru_cache
from pathlib import Path

from src.bank.store import BankStore
from src.bank.validators import validate_seed_plan
from src.subjects.ict450 import assemble, scheme


def _usable_questions() -> list[dict]:
    store = BankStore(assemble.BANK)
    categories = assemble._category_map()
    rows = []
    for question in store.approved_questions():
        category = categories.get(str(question.get("id")))
        if category not in assemble.CATEGORIES:
            continue
        flags = [str(flag) for flag in (question.get("review_flags") or [])]
        if "subpart label gap" in flags:
            continue
        if any(flag.lower().startswith("marks ") for flag in flags):
            continue
        rows.append(question)
    return rows


def library_seeds() -> list[int]:
    """Only seeds 1-20 are prebuilt Library entries."""
    return list(range(1, 21))


@lru_cache(maxsize=1)
def seed_cap() -> int:
    rows = _usable_questions()
    categories = assemble._category_map()
    counts = Counter(str(categories[str(row["id"])]) for row in rows)
    return min(counts[category] * 4 for category in assemble.CATEGORIES)


def build_seed(seed: int, out_dir: Path | None = None,
               force: bool = True, scheme_only: bool = False) -> dict:
    seed = int(seed)
    cap = seed_cap()
    if seed < 1 or seed > cap:
        raise ValueError(f"ICT450 seed must be between 1 and {cap}")
    store = BankStore(assemble.BANK)
    plans = assemble.build_category_plans(
        store.approved_questions(), seed_count=seed, reuse_cap=4)
    plan = plans[seed - 1]
    validate_seed_plan(plan, store, expected_slots=5,
                       require_assets=True, require_content_hash=True,
                       check_part=True)
    target = Path(out_dir) if out_dir is not None else assemble.OUT / f"seed_{seed:02d}"
    paper = assemble.build_seed(seed, plan, force=True, out_dir=target)
    answers = store.answers_by_question()
    scheme_info = scheme.build_scheme(seed, plan, answers, force=True,
                                      out_dir=target)
    if scheme_info.get("problems"):
        raise RuntimeError(
            f"seed {seed} scheme QA failed: {scheme_info['problems']}")
    paper_docx = target / "paper.docx"
    paper_pdf = target / "paper.pdf"
    scheme_docx = target / f"seed_{seed:02d}_scheme.docx"
    scheme_pdf = target / f"seed_{seed:02d}_scheme.pdf"
    files = {
        "paper_docx": str(paper_docx),
        "paper_pdf": str(paper_pdf),
        "scheme_docx": str(scheme_docx),
        "scheme_pdf": str(scheme_pdf),
    }
    topics = {}
    for slot in plan["slots"]:
        key = str(slot.get("category") or "other")
        topics[key] = topics.get(key, 0) + int(slot.get("marks") or 0)
    meta = {
        "subject": "ICT450",
        "seed": seed,
        "mode": "realistic",
        "computed_marks": None,
        "model": "ict450-v2-role-recycle",
        "cost_usd": 0.0,
        "accepted": len(plan["slots"]),
        "placeholders": 0,
        "total_slots": len(plan["slots"]),
        "total_marks": plan.get("total_marks") or sum(topics.values()),
        "has_practice_mode": False,
        "has_placeholders": False,
        "created": time.time(),
        "year": time.gmtime().tm_year,
        "topic_marks": topics,
        "summary": {"total_marks": plan["total_marks"]},
        "files": files,
        "progress": [{
            "question": slot["slot"],
            "slot": slot["slot"],
            "status": "accepted",
            "message": str(slot.get("category") or ""),
            "cost_usd": 0,
            "calls": 0,
            "accepted": 1,
            "placeholders": 0,
        } for slot in plan["slots"]],
        "document_versions": {
            "2": {
                "label": "v2",
                "playbook_version": "2.0",
                "built": time.time(),
                "files": files,
            }
        },
    }
    (target / "meta.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return {"seed": seed, "path": str(target), "cached": False,
            "files": files, "paper": paper, "scheme": scheme_info}
