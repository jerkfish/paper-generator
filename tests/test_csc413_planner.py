"""CSC413 stage-5 deterministic planner."""
from __future__ import annotations

import pytest

from src.subjects.csc413.planner import build_plan


def test_plan_has_modern_format_and_marks():
    plan = build_plan(1)
    assert plan["total_marks"] == 100
    assert plan["part_marks"] == {"A": 15, "B": 15, "C": 30, "D": 40}
    assert plan["question_count"] == 64
    assert plan["slot_count"] == 72
    assert plan["target_format"]["D"] == {"questions": 4, "marks": 40}
    assert len([s for s in plan["slots"] if s["part"] == "A"]) == 15
    assert len([s for s in plan["slots"] if s["part"] == "B"]) == 15
    assert len([s for s in plan["slots"] if s["part"] == "C"]) == 30
    d = [s for s in plan["slots"] if s["part"] == "D"]
    assert len(d) == 12
    for question in ("D1", "D2", "D3", "D4"):
        assert sum(s["marks"] for s in d if s["question"] == question) == 10


def test_plan_is_deterministic_and_varies_by_seed():
    assert build_plan(7) == build_plan(7)
    assert build_plan(7) != build_plan(8)


def test_twenty_seeds_validate():
    for seed in range(1, 21):
        plan = build_plan(seed)
        assert plan["total_marks"] == 100
        assert plan["slot_count"] == 72
        assert len({s["topic"] for s in plan["slots"] if s["part"] == "D"}) == 4


def test_invalid_style_and_seed_fail_closed():
    with pytest.raises(ValueError):
        build_plan(1, style="legacy")
    with pytest.raises(ValueError):
        build_plan(0)
