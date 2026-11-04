"""CSC402 stage-5 deterministic planner contract."""
from __future__ import annotations

import pytest

from src.subjects.csc402.planner import build_plan


def test_plan_targets_modern_csc402_format():
    plan = build_plan(1)
    assert plan["part_marks"] == {"A": 10, "B": 60, "C": 30}
    assert plan["total_marks"] == 100
    assert plan["question_count"] == 17
    assert plan["slot_count"] == 22
    assert plan["target_format"] == {
        "A": {"questions": 10, "marks": 10},
        "B": {"questions": 5, "marks": 60},
        "C": {"questions": 2, "marks": 30},
    }
    assert len([slot for slot in plan["slots"]
                if slot["part"] == "A"]) == 10
    assert len({slot["question"] for slot in plan["slots"]
                if slot["part"] == "B"}) == 5
    assert len([slot for slot in plan["slots"]
                if slot["part"] == "C"]) == 2


def test_plan_is_deterministic_for_a_seed():
    first = build_plan(7)
    second = build_plan(7)
    assert first == second
    assert build_plan(8)["slots"] != first["slots"]


def test_twenty_seeds_all_total_100():
    for seed in range(1, 21):
        plan = build_plan(seed)
        assert plan["total_marks"] == 100
        assert plan["part_marks"] == {"A": 10, "B": 60, "C": 30}
        assert sum(plan["topic_marks"].values()) == 100


def test_unknown_style_and_bad_seed_are_rejected():
    with pytest.raises(ValueError, match="modern"):
        build_plan(1, style="classic")
    with pytest.raises(ValueError, match="positive"):
        build_plan(0)
