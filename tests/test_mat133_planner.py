"""Deterministic MAT133 planner and Library prebuild contract."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.app.jobs import JobManager
from src.mat133.generators.registry import REGISTRY
from src.mat133.planner import (GENERATOR_LABELS, TOPIC_SHORT, TOPIC_TITLES,
                                build_paper)


def test_planner_is_deterministic(tmp_path):
    first, first_meta = build_paper(7, out_dir=tmp_path / "a")
    second, second_meta = build_paper(7, out_dir=tmp_path / "b")
    assert first.total_marks == second.total_marks
    assert first_meta["generator_ids"] == second_meta["generator_ids"]
    assert [p.text for q in first.questions for p in q.parts] == [
        p.text for q in second.questions for p in q.parts]


def test_planner_builds_five_questions_with_parts():
    paper, meta = build_paper(3)
    assert len(paper.questions) == 5
    assert [q.number for q in paper.questions] == [1, 2, 3, 4, 5]
    assert meta["accepted"] == sum(len(q.parts) for q in paper.questions)
    assert meta["accepted"] == 15
    for question in paper.questions:
        assert [part.label for part in question.parts] == ["a", "b", "c"]
        assert all(part.text and part.answer for part in question.parts)
        assert all(part.solution_latex for part in question.parts)
        assert all(part.marks > 0 for part in question.parts)


def test_every_generator_id_is_registered():
    for seed in range(1, 21):
        _, meta = build_paper(seed)
        assert set(meta["generator_ids"]) <= set(REGISTRY)
        assert len(meta["generator_ids"]) == 15


def test_twenty_seed_library_covers_all_generators():
    used = set()
    for seed in range(1, 21):
        _, meta = build_paper(seed)
        used.update(meta["generator_ids"])
    assert used == set(REGISTRY)
    assert len(used) == 57


def test_topic_maps_cover_the_whole_taxonomy():
    _, meta = build_paper(11)
    for topic in meta["topic_marks"]:
        assert topic in TOPIC_SHORT
        assert topic in TOPIC_TITLES
    assert len(GENERATOR_LABELS) == 57
    assert set(GENERATOR_LABELS) == set(REGISTRY)


def test_topic_marks_equal_part_marks():
    paper, meta = build_paper(5)
    expected = {}
    for question in paper.questions:
        for part in question.parts:
            expected[part.topic] = expected.get(part.topic, 0) + part.marks
    assert {key: float(value) for key, value in meta["topic_marks"].items()} \
        == {key: float(value) for key, value in expected.items()}


def test_mat133_rejects_practice_mode():
    with pytest.raises(ValueError, match="deterministic"):
        JobManager().create("practice", 1, None, subject="MAT133")


def test_same_seed_same_generator_diagrams(tmp_path):
    paper_a, _ = build_paper(9, out_dir=tmp_path / "a")
    paper_b, _ = build_paper(9, out_dir=tmp_path / "b")
    pictures_a = [part.diagram.path for q in paper_a.questions
                  for part in q.parts if part.diagram]
    pictures_b = [part.diagram.path for q in paper_b.questions
                  for part in q.parts if part.diagram]
    assert len(pictures_a) == len(pictures_b)
    assert [Path(p).name for p in pictures_a] == [
        Path(p).name for p in pictures_b]
    assert all(Path(p).exists() for p in pictures_a)
