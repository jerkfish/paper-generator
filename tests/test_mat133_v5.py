"""MAT133 V5 assembly guards.

The assembler must exclude approved questions whose printed structure is
missing and must not treat a model answer that admits missing source text as
usable.
"""
from __future__ import annotations

from src.subjects.mat133 import answers_compare, render_v5
from src.subjects.mat133.answers import _answer_unusable
from src.subjects.mat133.assemble_v2 import structural_issues


def test_structural_issues_flags_missing_marks():
    question = {
        "id": "Q1",
        "parts": [
            {"label": "a", "text": "Solve the equation.", "marks": None},
            {"label": "b", "text": "Find the value.", "marks": 5},
        ],
    }
    issues = structural_issues(question)
    assert "part a has no marks" in issues
    assert len(issues) == 1


def test_structural_issues_flags_empty_part_text():
    question = {
        "id": "Q1",
        "parts": [{"label": "a", "text": "  ", "marks": 5}],
    }
    assert "part a has no text" in structural_issues(question)


def test_structural_issues_accepts_complete_question():
    question = {
        "id": "Q1",
        "parts": [{"label": "a", "text": "Solve.", "marks": 5}],
    }
    assert structural_issues(question) == []


def test_answer_admitting_missing_text_is_unusable():
    assert _answer_unusable(
        "Assuming the missing inequality is (2x-1)/(x+3) <= 1, x=4.")
    assert _answer_unusable(
        "Cannot determine the graph because the piecewise definition is "
        "missing from the supplied question.")
    assert _answer_unusable("Insufficient information; no inequalities.")
    assert not _answer_unusable("$x=3$ or $x=-\\frac{1}{2}$.")


def test_latex_sanitiser_repairs_unsupported_commands():
    value = render_v5._sanitise_latex(
        r"\tfrac12\iff\big[(5-x)^2\le 9\big]\ \overline z")
    assert r"\frac{1}{2}" in value
    assert r"\Leftrightarrow" in value
    assert r"\big" not in value
    assert r"\overline{z}" in value
    assert r"\leq" in value


def test_compare_accepts_equivalent_answers():
    assert answers_compare._agree("$x=3$", "x=3")
    assert answers_compare._agree(
        r"$-\frac{20}{13}-\frac{17}{13}i$",
        r"\(-\frac{20}{13}-\frac{17}{13}i\)")
    assert not answers_compare._agree("$x=3$", "$x=4$")
