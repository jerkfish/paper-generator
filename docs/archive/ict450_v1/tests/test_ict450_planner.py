"""ICT450 Stage-5 deterministic planner tests."""
from __future__ import annotations

import json

import pytest

from src.subjects.ict450 import plugin
from src.subjects.ict450.planner import (
    build_plan,
    validate_plan,
    write_plan,
)


def test_plan_is_deterministic_and_sums_to_100():
    first = build_plan(1)
    second = build_plan(1)
    assert first == second
    assert first["subject"] == "ICT450"
    assert len(first["slots"]) == 5
    assert sum(slot["marks"] for slot in first["slots"]) == 100
    assert all(slot["marks"] == 20 for slot in first["slots"])
    assert len({slot["topic"] for slot in first["slots"]}) == 5
    assert first["part_marks"] == {"A": 100}


def test_plan_topics_are_from_taxonomy():
    plan = build_plan(2)
    taxonomy = json.loads(
        (__import__("pathlib").Path("data/tracking/ict450/taxonomy.json"))
        .read_text(encoding="utf-8"))
    valid = {topic["key"] for topic in taxonomy["topics"]}
    assert all(slot["topic"] in valid for slot in plan["slots"])
    assert all(slot["resolver"] == "ict450.theory" for slot in plan["slots"])


def test_write_plan(tmp_path):
    result = write_plan(3, out=tmp_path / "planner.json")
    assert (tmp_path / "planner.json").is_file()
    assert result["plan"]["seed"] == 3


def test_plugin_returns_slots_and_summary():
    slots, summary = plugin.plan("realistic", "modern", None, 4)
    assert len(slots) == 5
    assert summary["total_marks"] == 100
    with pytest.raises(ValueError):
        plugin.plan("realistic", "modern", 10, 4)


def test_validate_rejects_bad_marks():
    plan = build_plan(1)
    plan["slots"][0]["marks"] = 10
    with pytest.raises(ValueError):
        validate_plan(plan)
