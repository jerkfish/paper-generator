"""CSC413 stage-6 deterministic generators."""
from __future__ import annotations

from src.subjects.csc413.generators import (
    generate_paper,
    validate_paper,
    validate_seeds,
)
from src.subjects.csc413.planner import build_plan


def test_generated_paper_has_expected_shape_and_marks():
    plan = build_plan(1)
    paper = generate_paper(plan)
    assert paper["total_marks"] == 100
    assert paper["question_count"] == 64
    assert paper["slot_count"] == 72
    assert paper["part_marks"] == {"A": 15, "B": 15, "C": 30, "D": 40}
    assert validate_paper(paper, plan) == []
    assert paper["slot_map"]["D1a"] == "D1"


def test_generator_is_deterministic():
    plan = build_plan(7)
    assert generate_paper(plan) == generate_paper(plan)
    assert generate_paper(build_plan(7)) == generate_paper(build_plan(7))


def test_answers_and_matching_options_are_complete():
    paper = generate_paper(build_plan(3))
    matching = [q for q in paper["questions"] if q["part"] == "B"]
    assert len({q["answer_term"] for q in matching}) == 15
    assert len(paper["matching_options"]) == 15
    for question in paper["questions"]:
        if question["part"] == "A":
            assert question["answer"] in {"TRUE", "FALSE"}
        if question["part"] == "C":
            assert len(question["options"]) == 4
            assert question["answer"] in "ABCD"
        if question["part"] == "D":
            assert len(question["parts"]) == 3
            assert sum(p["marks"] for p in question["parts"]) == 10
            assert all(p["answer"] for p in question["parts"])


def test_twenty_seeds_pass_generation_validation(tmp_path):
    report = validate_seeds(1, 20, path=tmp_path / "validation.json")
    assert report["papers_valid"] == report["papers_total"] == 20
    assert all(not row["problems"] for row in report["results"])
