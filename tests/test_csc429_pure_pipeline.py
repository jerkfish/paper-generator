"""Type D approved-only planning, guard and seed QA tests."""
from __future__ import annotations

import json
from pathlib import Path

import docx
import pymupdf
import pytest

from src import config
from src.subjects.csc429 import pure_guard, pure_pool

TRACKING = config.TRACKING_DIR / "csc429"
BANK = TRACKING / "bank"
PLANS = BANK / "plans"
QUESTIONS = BANK / "questions"
ASSETS = BANK / "assets"
OUT = config.PROJECT_ROOT / "outputs" / "pure_extraction" / "CSC429_all_seeds"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def plans():
    index = _load(PLANS / "index.json")
    return index, [_load(path) for path in sorted(PLANS.glob("seed_*.json"))
                   if path.stem != "index"]


def test_plans_are_approved_only_and_respect_reuse_cap(plans):
    index, rows = plans
    assert index["seeds"] == 20
    assert index["max_uses"] <= index["reuse_cap"] == 4
    previous = set()
    for plan in rows:
        ids = [slot["question_id"] for slot in plan["slots"]]
        assert len(ids) == 11
        assert len(ids) == len(set(ids))
        assert sum(slot["marks"] for slot in plan["slots"]) == 100
        for qid in ids:
            assert _load(QUESTIONS / f"{qid}.json")["status"] == "approved"
        current = set(ids)
        assert not (current & previous)
        previous = current


def test_guard_refuses_non_approved_question():
    plan = _load(PLANS / "seed_01.json")
    replacement = None
    for path in QUESTIONS.glob("*.json"):
        question = _load(path)
        if (question.get("status") != "approved"
                and question["part"] == "A" and question["marks"] == 5):
            replacement = question
            break
    assert replacement is not None
    plan["slots"][0]["question_id"] = replacement["id"]
    plan["slots"][0]["content_hash"] = replacement["content_hash"]
    with pytest.raises(ValueError, match="not approved"):
        pure_guard.validate_plan(plan)


def test_rejected_registry_is_never_used_in_plans(plans):
    _, rows = plans
    rejected = _load(TRACKING / "rejected_registry.json")
    rejected_assets = set(rejected["assets"])
    for plan in rows:
        for slot in plan["slots"]:
            question = _load(QUESTIONS / f"{slot['question_id']}.json")
            for aid in question.get("assets") or []:
                asset = _load(ASSETS / f"{aid}.json")
                assert asset["sha256"] not in rejected_assets


def test_seed_quality_gate_and_answers():
    answers = _load(BANK / "answers.json")["by_qid"]
    assert len(answers) >= 33
    for seed in (1, 2, 3):
        out = OUT / f"seed_{seed:02d}"
        qa = _load(out / "qa.json")
        assert qa["problems"] == []
        assert qa["paper"]["part_a"] and qa["paper"]["part_b"]
        assert qa["scheme"]["part_a"] and qa["scheme"]["part_b"]
        assert qa["paper"]["right_overflow"] == []
        assert qa["scheme"]["right_overflow"] == []
        assert qa["paper"]["page1_images"] >= 1
        assert qa["scheme"]["page1_images"] >= 1
        with pymupdf.open(out / "paper.pdf") as pdf:
            paper = "\n".join(page.get_text() for page in pdf)
        with pymupdf.open(out / "scheme.pdf") as pdf:
            scheme = "\n".join(page.get_text() for page in pdf)
        plan = _load(PLANS / f"seed_{seed:02d}.json")
        for slot in plan["slots"]:
            number = 11 if slot["slot"].upper().startswith("B") else int(
                slot["slot"][1:])
            assert f"QUESTION {number}" in paper
            assert f"QUESTION {number}" in scheme
            assert answers[slot["question_id"]]["answer"].strip()
        assert "QUESTION A1" not in paper
        assert "QUESTION B1" not in paper


def test_pool_rebuild_is_deterministic_and_costs_zero():
    before = {path.name: path.read_text(encoding="utf-8")
              for path in sorted(PLANS.glob("seed_*.json"))}
    index = pure_pool.build_plans()
    after = {path.name: path.read_text(encoding="utf-8")
             for path in sorted(PLANS.glob("seed_*.json"))}
    assert index["seeds"] == 20
    assert index["max_uses"] <= 4
    assert before == after


def test_native_word_numbering_is_applied():
    paper = OUT / "seed_01" / "paper.docx"
    document = docx.Document(str(paper))
    numbered = [
        paragraph for paragraph in document.paragraphs
        if paragraph._p.pPr is not None
        and paragraph._p.pPr.numPr is not None
        and paragraph.style.name == "List Paragraph"
    ]
    assert len(numbered) >= 10
    assert len(document.part.numbering_part.element.findall(
        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}num"
    )) >= 10
    for paragraph in numbered:
        text = paragraph.text.strip()
        assert not text.startswith(("a)", "b)", "c)", "i)", "ii)"))


def test_question_headings_are_numeric_and_have_spacing():
    document = docx.Document(str(OUT / "seed_01" / "paper.docx"))
    headings = [p for p in document.paragraphs
                if p.text.strip().startswith("QUESTION ")]
    assert headings
    assert headings[0].text.strip().startswith("QUESTION 1")
    assert headings[-1].text.strip().startswith("QUESTION 11")
    for heading in headings:
        assert heading.paragraph_format.space_before.pt >= 18
        assert heading.paragraph_format.space_after.pt >= 10


def test_all_seeds_and_library_are_complete():
    from src.app.jobs import library_items
    manifest = _load(OUT / "p7_report.json")
    assert manifest["status"] == "complete"
    assert len(manifest["seeds"]) == 20
    assert manifest["checks"]["qa_failures"] == 0
    assert manifest["checks"]["max_reuse"] <= 4
    items = library_items("CSC429")
    assert len(items) == 20
    for item in items:
        assert item["total_marks"] == 100
        assert item["accepted"] == 11
        assert item["placeholders"] == 0
        assert all(Path(value).is_file() for value in item["files"].values())
    library_manifest = _load(
        config.WEB_CACHE_DIR / "CSC429" / "manifest.json")
    assert library_manifest["counts"]["seeds"] == 20
    assert library_manifest["publication"] is False
