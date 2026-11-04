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


def test_generated_paper_captures_styled_question_formats():
    paper = generate_paper(build_plan(1))
    quizzes = [q for q in paper["questions"] if q["part"] == "A"]
    assert any(q["format"] == "code" for q in quizzes)
    assert any(q["format"] == "roman_items" for q in quizzes)
    assert any(q.get("items") for q in quizzes)
    tables = []
    code_blocks = 0
    for question in paper["questions"]:
        groups = [question.get("stem_blocks") or [],
                  question.get("blocks") or []]
        groups += [part.get("blocks") or [] for part in question.get("parts", [])]
        for blocks in groups:
            for block in blocks:
                if block.get("type") == "table":
                    tables.append(block)
                elif block.get("type") == "code":
                    code_blocks += 1
    assert len(tables) >= 3
    assert [table["caption"].split(".")[0] for table in tables] == [
        f"Table {index}" for index in range(1, len(tables) + 1)]
    assert code_blocks >= 2
    assert paper["style_profile"]["table_count"] >= 3
    assert paper["style_profile"]["code_block_count"] >= 2
    assert paper["style_profile"]["mcq_formats"]["code"] >= 1
    assert paper["style_profile"]["mcq_formats"]["roman_items"] >= 1


def test_seeds_one_to_five_have_varied_style_signatures():
    signatures = set()
    for seed in range(1, 6):
        paper = generate_paper(build_plan(seed))
        formats = tuple(sorted(
            q.get("format", "standard") for q in paper["questions"]
            if q["part"] == "A"))
        tables = tuple(
            block.get("caption", "")
            for q in paper["questions"]
            for blocks in [q.get("stem_blocks") or []]
            + [part.get("blocks") or [] for part in q.get("parts", [])]
            for block in blocks if block.get("type") == "table")
        signatures.add((formats, tables))
    assert len(signatures) >= 2
