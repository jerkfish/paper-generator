"""MAT133 owner review-decision application."""
from __future__ import annotations

from src.subjects.mat133 import review_apply as ra


def test_owner_text_instructions_are_removed():
    text = (
        "question c) is cutted offed\n"
        "full question c)\n"
        "c) Graph the system.\n"
        "$$x > -1$$\n(8 marks)")
    cleaned = ra._clean_reviewer_text(text, "MAT133-2011-SEP-Q4")
    assert cleaned.startswith("c) Graph")
    assert "cutted" not in cleaned
    assert "(8 marks)" in cleaned


def test_owner_markdown_emphasis_is_normalised():
    text = "a) Solve.\n*(5 marks)*\n\nb) Find.\n*(4 marks)*"
    cleaned = ra._clean_reviewer_text(text, "MAT133-2021-JUL-Q4-2")
    assert "*(5 marks)*" not in cleaned
    assert "(5 marks)" in cleaned
    assert "(4 marks)" in cleaned


def test_owner_parts_parse_nested_marks():
    parts = ra._parse_reviewer_parts(
        "a) Find:\n"
        "i) one\n(3 marks)\n"
        "ii) two\n(4 marks)\n"
        "b) Solve.\n(5 marks)")
    assert [(part["label"], part["marks"]) for part in parts] == [
        ("a", 7), ("b", 5)]


def test_missing_part_c_is_replaced():
    question = {
        "id": "MAT133-2011-SEP-Q4",
        "pages": [4],
        "parts": [
            {"label": "a", "text": "a) part a\n(4 marks)", "marks": 4},
            {"label": "b", "text": "b) part b\n(8 marks)", "marks": 8},
            {"label": "c", "text": "c) cut", "marks": 8},
        ],
        "refs": [],
        "native_text": "",
        "native_text_blocks": [],
        "subpart_marks": [],
    }
    changed = ra._apply_text(
        question,
        "question c) is cutted offed\nfull question c)\n"
        "c) Graph the system.\n$$x > -1$$\n(8 marks)",
        "MAT133-2011-SEP-Q4")
    assert changed
    assert "Graph the system" in question["native_text"]
    assert question["marks"] == 20
    assert [(part["label"], part["marks"]) for part in question["parts"]] == [
        ("a", 4), ("b", 8), ("c", 8)]


def test_equation_comment_fills_missing_part_a():
    question = {
        "id": "MAT133-2026-FEB-Q3",
        "pages": [2],
        "parts": [
            {"label": "a", "text": "a) Solve:", "marks": None},
            {"label": "b", "text": "b) Graph:\n(5 marks)", "marks": 5},
        ],
        "refs": [],
        "native_text": "",
        "native_text_blocks": [],
        "subpart_marks": [],
    }
    changed = ra._apply_text(
        question,
        "\\begin{align*} 2^x &= 8 \\\\ x + y^2 &= 6 \\end{align*}\n"
        "(5 marks)\n\nThat is not a Figure it is a equation.",
        "MAT133-2026-FEB-Q3")
    assert changed
    assert question["marks"] == 10
    assert [(part["label"], part["marks"]) for part in question["parts"]] == [
        ("a", 5), ("b", 5)]
    assert "2^x" in question["parts"][0]["text"]


def test_asset_only_comment_does_not_replace_question_text():
    question = {
        "id": "MAT133-2017-MAR-Q5",
        "pages": [3],
        "parts": [{"label": "a", "text": "a) real question", "marks": 5}],
        "refs": [],
        "native_text": "a) real question",
        "native_text_blocks": [],
        "subpart_marks": [],
    }
    changed = ra._apply_text(question, "figure 1 need fix figure 2 approved.",
                             "MAT133-2017-MAR-Q5")
    assert changed is False
    assert question["native_text"] == "a) real question"
