"""ICT450 Stage-6 deterministic generator tests."""
from __future__ import annotations

from src.subjects.ict450 import generators, plugin


def test_generate_seed_one_is_complete():
    paper = generators.generate(1)
    assert paper["question_count"] == 5
    assert paper["total_marks"] == 100
    assert len(paper["questions"]) == 5
    for question in paper["questions"]:
        assert question["marks"] == 20
        assert sum(part["marks"] for part in question["subparts"]) == 20
        assert question["answer"].strip()
        assert all(point["points"] for point in question["marking_points"])


def test_generate_is_deterministic():
    assert generators.generate(1) == generators.generate(1)


def test_validate_seeds_one_to_five():
    report = generators.validate(list(range(1, 6)))
    assert report["failed"] == 0
    assert report["passed"] == 5


def test_plugin_generator_labels_cover_bank():
    labels = plugin.generator_labels()
    assert set(labels) == {
        template["generator_id"] for template in generators.QUESTION_BANK.values()
    }
