"""CSC429 stage-4 taxonomy and question-log parser."""
from __future__ import annotations

from src.subjects.csc429 import taxonomy


def test_clean_text_keeps_question_when_header_is_joined():
    raw = ("QUESTION 1 Fill in the blank. 2 CSIJUN 2014/CSC429 "
           "a) The acronym EDSAC stands for ____.")
    cleaned = taxonomy.clean_text(raw)
    assert "QUESTION 1" in cleaned
    assert "EDSAC" in cleaned
    assert "CSIJUN" not in cleaned
    assert "CSC429" not in cleaned


def test_parse_paper_extracts_parts_questions_marks(tmp_path):
    text = (
        "PART A (2 Questions)\n"
        "PART B (1 Question)\n"
        "PART A (10 MARKS)\n"
        "QUESTION 1\n"
        "a) Convert 1010 to decimal. (4 marks)\n"
        "b) Define cache. (2 marks)\n"
        "QUESTION 2\n"
        "Explain interrupts. (4 marks)\n"
        "PART B (10 MARKS)\n"
        "QUESTION 1\n"
        "Write an assembly program. (10 marks)\n"
    )
    path = tmp_path / "CSC429 TEST 2026.txt"
    path.write_text(text, encoding="utf-8")
    row = {
        "paper": "CSC429 TEST 2026.pdf",
        "source": "CSC429 TEST 2026.pdf",
        "month": "FEBRUARY",
        "year": 2026,
        "pages": 1,
        "text_file": str(path),
        "source_kind": "text",
    }
    parsed = taxonomy.parse_paper(row)
    assert parsed["paper_id"] == "CSC429-2026-02"
    assert parsed["part_marks"] == {"A": 10, "B": 10}
    assert parsed["expected_marks"] == 20
    assert parsed["parsed_marks"] == 20
    assert parsed["marks_complete"] is True
    slots = {entry["slot"]: entry["marks"] for entry in parsed["entries"]}
    assert slots == {"A1": 6, "A2": 4, "B1": 10}
    topics = {entry["slot"]: entry["topic"] for entry in parsed["entries"]}
    assert topics["A1"] == "data_representation"
    assert topics["A2"] == "interrupts_io"
    assert topics["B1"] == "instruction_set_assembly"
    assert parsed["entries"][0]["subparts"] == [
        {"label": "a", "text": "Convert 1010 to decimal. (4 marks)",
         "marks": 4},
        {"label": "b", "text": "Define cache. (2 marks)", "marks": 2},
    ]


def test_marks_regex_handles_ocr_one_and_ignores_plain_numbers():
    assert taxonomy._marks("(4 marks) and ('l mark)") == [4, 1]
    assert taxonomy._marks("student mark 90 is the highest") == []
    assert taxonomy._marks("5 marks)") == [5]


def test_classify_csc429_vocabulary():
    topic, _, _, _ = taxonomy.classify(
        "Convert the binary value to hexadecimal using 2's complement.")
    assert topic == "data_representation"
    topic, _, _, _ = taxonomy.classify(
        "Explain the interrupt priority and the DMA transfer.")
    assert topic == "interrupts_io"
    topic, _, _, _ = taxonomy.classify(
        "Write a three-address assembly program with registers.")
    assert topic == "instruction_set_assembly"


def test_figure_refs_and_asset_strategy():
    refs = taxonomy._figure_refs("Refer to Figure 1 and Table 2.")
    assert refs == ["Figure 1", "Table 2"]
