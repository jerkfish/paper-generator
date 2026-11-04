"""CSC402 stage-6 deterministic generators."""
from __future__ import annotations

from src.subjects.csc402.generators import (
    generate_paper,
    validate_paper,
    validate_seeds,
)
from src.subjects.csc402.planner import build_plan


def test_generated_paper_has_expected_shape_and_marks():
    plan = build_plan(1)
    paper = generate_paper(plan)
    assert paper["total_marks"] == 100
    assert paper["question_count"] == 17
    assert paper["slot_count"] == 22
    assert validate_paper(paper, plan) == []
    assert paper["slot_map"]["B5b"] == "B5"
    assert paper["slot_map"]["C2"] == "C2"


def test_generator_is_deterministic():
    plan = build_plan(7)
    assert generate_paper(plan) == generate_paper(plan)
    assert generate_paper(build_plan(7)) == generate_paper(build_plan(7))


def test_mcq_and_program_answers_are_complete():
    paper = generate_paper(build_plan(3))
    for question in paper["questions"]:
        if question["part"] == "A":
            assert len(question["options"]) == 4
            assert question["answer"] in "ABCD"
        if question["part"] == "C":
            assert "#include" in question["parts"][0]["answer"]
            assert "int main" in question["parts"][0]["answer"]


def test_twenty_seeds_pass_generation_validation():
    report = validate_seeds(1, 20)
    assert report["papers_valid"] == report["papers_total"] == 20
    assert all(not row["problems"] for row in report["results"])
    assert "csc402.mcq.control_structures" in report["generator_ids"]
    assert "csc402.complete_program.arrays" in report["generator_ids"]
