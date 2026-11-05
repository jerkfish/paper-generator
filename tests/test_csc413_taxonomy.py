"""CSC413 stage-4 question-log parser."""
from __future__ import annotations

from src.subjects.csc413 import taxonomy


def test_parse_paper_extracts_parts_questions_and_marks(tmp_path):
    text = (
        "PART A (3 Questions)\n"
        "PART B (2 Questions)\n"
        "PART C (2 Questions)\n"
        "PART D (2 Questions)\n"
        "PART A (3 MARKS)\n"
        "1. Text uses serif fonts.\n"
        "2. A bitmap image has pixels.\n"
        "3. Audio sampling uses Hertz.\n"
        "PART B (2 MARKS)\n"
        "1. Which is a video format?\n"
        "2. Which is an authoring tool?\n"
        "PART C (2 MARKS)\n"
        "QUESTION 1\n"
        "Which statement about multimedia is true? (1 mark)\n"
        "QUESTION 2\n"
        "Which is a virtual reality device? (1 mark)\n"
        "PART D (10 MARKS)\n"
        "QUESTION 1\n"
        "a) Define animation. (2 marks)\n"
        "b) Explain keyframes. (3 marks)\n"
        "QUESTION 2\n"
        "a) Design a storyboard for a kiosk. (5 marks)\n"
    )
    path = tmp_path / "CSC413 TEST 2026.txt"
    path.write_text(text, encoding="utf-8")
    row = {
        "paper": "CSC413 TEST 2026.pdf",
        "month": "FEBRUARY",
        "year": 2026,
        "text_file": str(path),
        "source_kind": "text",
    }
    parsed = taxonomy.parse_paper(row)
    assert parsed["paper_id"] == "CSC413-2026-02"
    assert parsed["part_marks"] == {"A": 3, "B": 2, "C": 2, "D": 10}
    assert parsed["expected_marks"] == 17
    assert parsed["parsed_marks"] == 17
    assert parsed["marks_complete"] is True
    slots = {entry["slot"]: entry["marks"] for entry in parsed["entries"]}
    assert slots == {
        "A1": 1, "A2": 1, "A3": 1,
        "B1": 1, "B2": 1,
        "C1": 1, "C2": 1,
        "D1": 5, "D2": 5,
    }
    d1 = next(entry for entry in parsed["entries"] if entry["slot"] == "D1")
    assert [row["label"] for row in d1["subparts"]] == ["a", "b"]


def test_topic_classification_uses_multimedia_vocabulary():
    topic, scores, confidence = taxonomy.classify(
        "A serif font and kerning control the text appearance.")
    assert topic == "text"
    assert scores["text"] > 0
    assert confidence in {"medium", "high"}
    topic, _, _ = taxonomy.classify(
        "A bitmap image stores pixels and RGB colour values.")
    assert topic == "graphics"


def test_marks_regex_only_accepts_parenthesised_marks():
    assert taxonomy._marks("(4 marks) and ('10 marks)") == [4, 10]
    assert taxonomy._marks("student mark 90 is the highest") == []
