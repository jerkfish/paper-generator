"""CSC429 stage-5 deterministic planner."""
from __future__ import annotations

from src.subjects.csc429 import planner
from src.subjects.csc429 import plugin


def test_build_plan_modern_format():
    plan = planner.build_plan(1)
    slots = plan["slots"]
    part_a = [slot for slot in slots if slot["part"] == "A"]
    part_b = [slot for slot in slots if slot["part"] == "B"]
    assert plan["total_marks"] == 100
    assert plan["part_marks"] == {"A": 80, "B": 20}
    assert plan["computed_marks"] == 100
    assert len(part_a) == 10
    assert len(part_b) == 1
    assert [slot["marks"] for slot in part_a] == [
        5, 5, 5, 5, 10, 10, 10, 10, 10, 10]
    assert part_b[0]["marks"] == 20
    assert part_b[0]["topic"] == "instruction_set_assembly"
    assert part_b[0]["generator_id"] == "csc429.assembly"
    assert {slot["topic"] for slot in slots} >= {
        "computer_generations_history", "data_representation",
        "cpu_organization", "memory_cache", "interrupts_io",
        "parallel_architectures", "instruction_set_assembly",
    }


def test_plan_is_deterministic_and_seeded():
    first = planner.build_plan(1)
    second = planner.build_plan(1)
    assert first == second
    assert planner.build_plan(2)["sequence_id"] in {
        item["id"] for item in planner.TOPIC_SEQUENCES}
    assert len(planner.build_plan(2)["slots"]) == 11


def test_all_20_seeds_validate_without_writing():
    for seed in range(1, 21):
        plan = planner.build_plan(seed)
        assert plan["total_marks"] == 100
        assert plan["part_marks"] == {"A": 80, "B": 20}
        assert len(plan["slots"]) == 11
        assert plan == planner.build_plan(seed)
        assert plan["sequence_id"] in {
            item["id"] for item in planner.TOPIC_SEQUENCES}


def test_plugin_plan_returns_summary_and_table():
    table, summary = plugin.plan("realistic", "modern", None, 1)
    assert len(table) == 11
    assert summary["total_slots"] == 11
    assert summary["total_marks"] == 100
    assert summary["computed_marks"] == 100
    assert summary["part_marks"] == {"A": 80, "B": 20}
    assert summary["slots"][-1]["slot"] == "B1"
