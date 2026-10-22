"""Deterministic MAT133 planner and Library prebuild contract."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.app import jobs, main
from src.app.jobs import JobManager, filter_library, library_item
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


def _write_cached_paper(tmp_path, monkeypatch, subject: str, **extra):
    monkeypatch.setattr(jobs.config, "WEB_CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(jobs.config, "OUTPUTS_DIR", tmp_path)
    out = jobs.cache_path("realistic", 1, None, subject=subject)
    out.mkdir(parents=True)
    paper = out / "paper.pdf"
    paper.write_bytes(b"%PDF")
    meta = {
        "subject": subject, "seed": 1, "mode": "realistic",
        "computed_marks": None, "created": 1767225600, "year": 2026,
        "accepted": 15, "placeholders": 0, "model": "test",
        "topic_marks": {"functions": 9},
        "files": {"paper_pdf": str(paper)},
        "summary": {}, "progress": [],
    }
    meta.update(extra)
    (out / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    return out


def test_mat133_library_item_exposes_total_marks_and_flags(tmp_path,
                                                           monkeypatch):
    _write_cached_paper(
        tmp_path, monkeypatch, "MAT133", total_marks=68,
        has_practice_mode=False, has_placeholders=False)
    item = library_item(1, "MAT133")
    assert item is not None
    assert item["computed_display"] == 0
    assert item["total_marks"] == 68
    assert item["marks_value"] == 68
    assert item["marks_label"] == "Total marks"
    assert item["has_practice_mode"] is False
    assert item["has_placeholders"] is False


def test_mat133_filter_uses_total_marks(tmp_path, monkeypatch):
    _write_cached_paper(
        tmp_path, monkeypatch, "MAT133", total_marks=68,
        has_practice_mode=False, has_placeholders=False)
    items = [library_item(1, "MAT133")]
    assert [i["seed"] for i in filter_library(items, computed="68")] == [1]
    assert filter_library(items, computed="70") == []
    # A subject without placeholders is not excluded by the placeholder filter.
    assert [i["seed"] for i in filter_library(items, placeholders="0")] == [1]


def test_mat133_library_page_shows_total_marks_and_dash(tmp_path, monkeypatch):
    _write_cached_paper(
        tmp_path, monkeypatch, "MAT133", total_marks=68,
        has_practice_mode=False, has_placeholders=False)
    html = TestClient(main.app).get("/mat133/library").text
    assert "Total marks" in html
    assert "Computed marks" not in html
    assert "68" in html
    assert "&mdash;" in html or "—" in html
    assert 'id="placeholders"' not in html


def test_public_manifest_exports_mat133_total_marks(tmp_path):
    from scripts.build_public_bundle import _write_manifests
    item = {
        "subject": "MAT133", "seed": 1, "mode": "realistic",
        "computed_display": 0, "total_marks": 68, "marks_value": 68,
        "has_practice_mode": False, "has_placeholders": False,
        "year": 2026, "accepted": 15, "placeholders": 0,
        "topic_marks": {"functions": 9}, "topic_mix": "FUN 9",
        "downloads": {
            "paper_docx": "MAT133 Seed 01 2026.docx",
            "paper_pdf": "MAT133 Seed 01 2026.pdf",
            "scheme_docx": "MAT133 Seed 01 2026 - Marking Scheme.docx",
            "scheme_pdf": "MAT133 Seed 01 2026 - Marking Scheme.pdf",
        },
    }
    _write_manifests(tmp_path, {"MAT133": [item]})
    manifest = json.loads(
        (tmp_path / "library" / "MAT133" / "manifest.json").read_text(
            encoding="utf-8"))
    paper = manifest["papers"][0]
    assert manifest["has_practice_mode"] is False
    assert manifest["has_placeholders"] is False
    assert paper["total_marks"] == 68
    assert paper["marks_value"] == 68
    assert paper["has_practice_mode"] is False
    subject = json.loads(
        (tmp_path / "subjects" / "MAT133" / "subject.json").read_text(
            encoding="utf-8"))
    assert subject["has_practice_mode"] is False
    assert subject["has_placeholders"] is False


def test_csc662_library_page_keeps_computed_marks(tmp_path, monkeypatch):
    _write_cached_paper(
        tmp_path, monkeypatch, "CSC662", computed_marks=22,
        has_practice_mode=True, has_placeholders=True, placeholders=2)
    src = tmp_path / "eval_final_deepseek"
    src.mkdir()
    (src / "seed_01_theory.json").write_text("{}", encoding="utf-8")
    html = TestClient(main.app).get("/csc662/library").text
    assert "Computed" in html
    assert "Placeholders" in html
    assert 'id="placeholders"' in html
    assert (">—<" not in html) and ("&mdash;" not in html)


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
