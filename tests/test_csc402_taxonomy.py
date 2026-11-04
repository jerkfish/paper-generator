"""CSC402 stage-4 question-log parser."""
from __future__ import annotations

from pathlib import Path

from src.subjects.csc402 import taxonomy


def test_parse_paper_extracts_parts_questions_and_marks(tmp_path):
    text = (
        "PART A (10 MARKS)\n"
        "1. Which of the following is an algorithm? A. Steps B. Loop\n"
        "PART B (20 MARKS)\n"
        "QUESTION 1\n"
        "a) Write a flowchart for the process. (4 marks)\n"
        "b) Explain parallel arrays. (6 marks)\n"
        "QUESTION 2\n"
        "Write a C++ program using a for loop. (10 marks)\n"
        "PART C (30 MARKS)\n"
        "QUESTION 1\n"
        "Write a complete C++ program using arrays. (30 marks)\n"
    )
    path = tmp_path / "CSC402 TEST 2026.txt"
    path.write_text(text, encoding="utf-8")
    row = {
        "paper": "CSC402 TEST 2026.pdf",
        "month": "FEBRUARY",
        "year": 2026,
        "text_file": str(path),
        "source_kind": "text",
    }
    parsed = taxonomy.parse_paper(row)
    assert parsed["paper_id"] == "CSC402-2026-02"
    assert parsed["part_marks"] == {"A": 10, "B": 20, "C": 30}
    assert parsed["expected_marks"] == 60
    assert parsed["parsed_marks"] == 60
    assert parsed["marks_complete"] is True
    slots = {entry["slot"]: entry["marks"] for entry in parsed["entries"]}
    assert slots == {"A": 10, "B1": 10, "B2": 10, "C1": 30}
    b1 = next(entry for entry in parsed["entries"]
              if entry["slot"] == "B1")
    assert [row["label"] for row in b1["subparts"]] == ["a", "b"]
    assert parsed["part_a_aggregate"] is True


def test_topic_classification_uses_paper_vocabulary():
    topic, scores, confidence = taxonomy.classify(
        "Design a flowchart and pseudo-code for the algorithm.")
    assert topic == "fundamentals"
    assert scores["fundamentals"] > 0
    assert confidence in {"medium", "high"}
    topic, _, _ = taxonomy.classify(
        "Declare an array and search for an element by index.")
    assert topic == "arrays"


def test_marks_regex_only_accepts_parenthesised_marks():
    assert taxonomy._marks("(4 marks) and ('10 marks)") == [4, 10]
    assert taxonomy._marks("student mark 90 is the highest") == []
