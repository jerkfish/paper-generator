"""CSC429 Stage-6 deterministic generators."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.skip(
    reason="legacy CSC429 Type C planner/generator/builder path retired by the P0 Type D strategy lock")

from src.subjects.csc429 import generators, planner


def test_all_generators_are_valid_and_used_across_20_seeds():
    seen = set()
    for seed in range(1, 21):
        plan = planner.build_plan(seed)
        for slot in plan["slots"]:
            if slot["resolver"] != "csc429.generator":
                continue
            question = generators.generate_for_slot(
                seed, slot["slot"], slot["topic"], slot["marks"])
            assert question is not None
            assert question["topic"] == "data_representation"
            assert question["marks"] == slot["marks"]
            assert generators.verify_question(question) == []
            subpart_marks = sum(part["marks"] for part in question["subparts"])
            assert subpart_marks in (0, slot["marks"])
            seen.add(question["generator_id"])
    assert seen == set(generators.GENERATOR_IDS)


def test_generated_answers_are_independently_recomputed():
    signed = generators.generate_for_slot(
        1, "A3", "data_representation", 5)
    assert signed["generator_id"] == "csc429.signed_arithmetic"
    meta = signed["metadata"]
    assert meta["result"] == meta["left"] - meta["right"]
    assert generators.verify_question(signed) == []

    ieee = generators.generate_for_slot(
        1, "A10", "data_representation", 10)
    assert ieee["generator_id"] == "csc429.ieee754_single"
    assert all(part["marks"] == 5 for part in ieee["subparts"])
    assert generators.verify_question(ieee) == []

    base = generators.generate_for_slot(
        3, "A3", "data_representation", 5)
    assert base["generator_id"] == "csc429.number_base_conversion"
    assert generators.verify_question(base) == []
