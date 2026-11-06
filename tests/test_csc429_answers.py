"""CSC429 unofficial model answers are cached, labelled and costed."""
from __future__ import annotations

from src.llm import Usage
from src.subjects.csc429 import answers, build_docx


def _slot():
    return {
        "kind": "real_bank_question",
        "question_id": "CSC429-TEST-A1",
        "paper_id": "CSC429-TEST",
        "slot": "A1",
        "marks": 5,
        "topic": "computer_generations",
        "topic_label": "Computer generations and history",
        "source_file": "test.pdf",
        "text": "Explain the stored-program concept.",
        "subparts": [],
        "content": [],
    }


def test_answers_are_generated_once_and_cached(tmp_path, monkeypatch):
    monkeypatch.setattr(answers, "CACHE_PATH", tmp_path / "answers.json")
    calls = []

    def fake_generate(slot, *, model):
        calls.append(slot["question_id"])
        usage = Usage()
        usage.add(100, 50, 150, model=model)
        return {
            "answer": "The stored-program concept keeps instructions in memory.",
            "marking": ["5 marks: correct explanation."],
            "confidence": "high",
            "notes": "",
            "marks": slot["marks"],
        }, usage

    monkeypatch.setattr(answers, "_generate", fake_generate)
    slot = _slot()
    report = answers.ensure_answers([slot], allow_llm=True, strict=True)
    assert report["generated"] == 1
    assert report["failed"] == 0
    assert slot["model_answer"]["unofficial"] is True
    assert slot["model_answer"]["answer"].startswith("The stored-program")
    assert report["cost_usd"] > 0

    cached_slot = _slot()
    second = answers.ensure_answers([cached_slot], allow_llm=True, strict=True)
    assert second["generated"] == 0
    assert second["cache_hits"] == 1
    assert second["cost_usd"] == 0
    assert calls == ["CSC429-TEST-A1"]
    assert cached_slot["model_answer"]["answer"] == slot["model_answer"]["answer"]


def test_model_markup_is_removed():
    assert build_docx._clean_model_markup("**Answer** with `code`") == (
        "Answer with code")
