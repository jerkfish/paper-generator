"""MAT133 v2 bank parser rules.

The parser must keep printed text and marks, and must flag missing or merged
marks for Gate A rather than inventing them.
"""
from __future__ import annotations

from src.subjects.mat133 import bank_build as b


def test_nested_marks_are_summed():
    part = (
        "Given the following, find:\n"
        "i) $\\sin 2A$\n(3 marks)\n"
        "ii) $\\cos(A+B)$\n(3 marks)")
    marks, note = b._part_marks(part)
    assert marks == 6
    assert "nested" in note


def test_single_total_mark_is_kept():
    marks, note = b._part_marks("Find the value.\n(5 marks)")
    assert marks == 5
    assert note == ""


def test_missing_mark_is_flagged():
    marks, note = b._part_marks("Solve the equation.")
    assert marks is None
    assert "no printed" in note


def test_merged_part_is_flagged():
    text = (
        "a) Write a system of inequalities.\n(5 marks)\n"
        "The graph of a function is shown.\n"
        "i) $f(x+1)$ ii) $-2-f(x)$\n(4 marks)")
    warning = b._merged_part_warning(text)
    assert "merged" in warning


def test_normal_part_is_not_flagged():
    text = (
        "a) Find:\n"
        "i) the domain\n(2 marks)\n"
        "ii) the range\n(3 marks)")
    assert b._merged_part_warning(text) == ""


def test_appendix_is_stripped_from_the_last_question():
    text = (
        "QUESTION 4\n"
        "a) Solve the equation.\n(5 marks)\n"
        "END OF QUESTION PAPER\nCONFIDENTIAL\n"
        "1. $\\sin^2 A + \\cos^2 A = 1$")
    cleaned = b._clean_question_text(text)
    assert "END OF QUESTION PAPER" not in cleaned
    assert "CONFIDENTIAL" not in cleaned
    assert "sin^2" not in cleaned
    assert cleaned.startswith("a) Solve")


def test_ocr_mark_fallback_reads_printed_marks(monkeypatch, tmp_path):
    monkeypatch.setattr(b, "OCR_DIR", tmp_path)
    (tmp_path / "PAPER.txt").write_text(
        "QUESTION 1\n"
        "a) Solve the equation.\n(5 marks)\n"
        "b) Solve the inequality.\n(4 marks)\n"
        "QUESTION 2\n"
        "a) Another question.\n(6 marks)\n",
        encoding="utf-8")
    assert b._ocr_part_marks("PAPER.pdf", 1) == {"a": 5, "b": 4}
    assert b._ocr_part_marks("PAPER.pdf", 2) == {"a": 6}


def test_ocr_mark_fallback_ignores_ambiguous_blocks(monkeypatch, tmp_path):
    monkeypatch.setattr(b, "OCR_DIR", tmp_path)
    (tmp_path / "PAPER.txt").write_text(
        "QUESTION 1\n"
        "a) Find:\n"
        "i) one\n(3 marks)\n"
        "ii) two\n(3 marks)\n",
        encoding="utf-8")
    assert b._ocr_part_marks("PAPER.pdf", 1) == {}


def test_page_noise_is_stripped():
    text = (
        "QUESTION 2\n"
        "CONFIDENTIAL\n"
        "CS/NOV 2026/MAT133\n"
        "a) Solve the equation.\n(5 marks)\n"
        "© Hak Cipta Universiti Teknologi MARA\n"
        "b) Find the value.\n(4 marks)")
    cleaned = b._clean_question_text(text)
    assert "CONFIDENTIAL" not in cleaned
    assert "CS/NOV" not in cleaned
    assert "Hak Cipta" not in cleaned
    assert cleaned.startswith("a) Solve")


def test_topic_tags_use_math_keywords():
    assert "trigonometry" in b._topic_tags(
        "Solve $\\sin 2x = \\cos x$ for all angles.")
    assert "complex_numbers" in b._topic_tags(
        "Express the complex number in the form a + bi.")
    assert "circles" in b._topic_tags(
        "Find the center and radius of the circle.")
