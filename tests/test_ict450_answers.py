"""V4 answer-content checks for the ICT450 seed 1–3 pilot."""
import pytest

from src.bank.store import BankStore
from src.subjects.ict450.answers import BANK, _check_content, _sub_marks
from src.subjects.ict450.answers_content import ANSWERS


def test_seed_1_3_answer_content_reconciles_to_question_marks():
    if not BANK.exists():
        pytest.skip("ICT450 bank is not present")
    approved = {str(question["id"]): question
                for question in BankStore(BANK).approved_questions()}
    assert len(ANSWERS) == 15
    for question_id, content in ANSWERS.items():
        question = approved.get(question_id)
        assert question is not None, question_id
        assert not _check_content(question, content), question_id
        assert _sub_marks(content["blocks"]) == int(question["marks"])


def test_answer_content_has_provenance_and_marking_points():
    for question_id, content in ANSWERS.items():
        assert content.get("blocks"), question_id
        assert content.get("marking"), question_id
        assert content.get("confidence") in {"high", "medium", "low"}
        assert content.get("assumptions") is not None
