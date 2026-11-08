"""CSC429 Stage-5 deterministic planner."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.skip(
    reason="legacy CSC429 Type C planner/generator/builder path retired by the P0 Type D strategy lock")

import json

from src.subjects.csc429 import planner, plugin


def test_planner_is_deterministic_and_balanced():
    plan = planner.build_plan(1)
    planner.validate_plan(plan)
    assert plan["slot_count"] == 11
    assert plan["total_marks"] == 100
    assert plan["part_marks"] == {"A": 80, "B": 20}
    assert [slot["marks"] for slot in plan["slots"]] == [
        5, 5, 5, 5, 10, 10, 10, 10, 10, 10, 20
    ]
    assert plan["slots"][-1]["topic"] == "assembly_programming"
    data_slots = [slot for slot in plan["slots"]
                  if slot["topic"] == "data_representation"]
    assert data_slots
    assert all(slot["resolver"] == "csc429.generator" for slot in data_slots)
    assert all(slot["variant_policy"] == "controlled_numeric"
               for slot in data_slots)
    topics = {slot["topic"] for slot in plan["slots"] if slot["part"] == "A"}
    assert len(topics) == 7
    assert "other" not in topics
    assert plan == planner.build_plan(1)


def test_topic_quota_comes_from_the_stage4_log():
    log = json.loads(planner.LOG_PATH.read_text(encoding="utf-8"))
    quota = planner.topic_quota(log)
    assert sum(quota.values()) == 10
    assert set(quota) == {
        entry["topic"] for entry in log["entries"] if entry["part"] == "A"
    }
    five, ten = planner.mark_pools(log, quota)
    assert len(five) == 4
    assert len(ten) == 6


def test_plugin_returns_slots_and_plan():
    slots, plan = plugin.plan("realistic", "modern", None, 2)
    assert slots == plan["slots"]
    planner.validate_plan(plan)
    assert plan["seed"] == 2
