"""Unit tests for the ICT502 V2 bank text and mark parser."""
from __future__ import annotations

from src.subjects.ict502.bank_build import (
    _build_parts,
    _clean_md,
    _latex_to_text,
    _part_marks,
    _question_chunks,
    _topic_tags,
)
from src.subjects.ict502.answers import _part_level_points
from src.subjects.ict502.assemble_v5 import (_is_code_continuation,
                                             _is_code_line)
from src.subjects.ict502.review_apply import _apply_asset, _owner_html


def test_question_chunks_split_a_lost_heading():
    full_md = """## QUESTION 1

a) First question part one.

(4 marks)

b) First question part two.

(6 marks)

## QUESTION 2

a) Second question part one.

(10 marks)

b) Second question part two.

(10 marks)

a) Third question, heading lost by MinerU.

(4 marks)

b) Third question part two.

(16 marks)

## QUESTION 4

a) Fourth question.

(20 marks)

## QUESTION 5

a) Fifth question.

(20 marks)
"""
    chunks = _question_chunks(full_md)
    assert len(chunks) == 5
    assert chunks[2].startswith("a) Third question, heading lost")
    assert chunks[1].startswith("a) Second question")


def test_part_marks_sums_nested_marks():
    assert _part_marks("i) One. (2 marks)\n\nii) Two. (2 marks)") == (
        4.0, "sum of the printed marks")
    assert _part_marks("Explain. (4 marks)") == (4.0, "")
    assert _part_marks("No mark line") == (
        None, "no printed (N marks) line in this part")


def test_build_parts_keeps_a_whole_question():
    stem, parts, reasons = _build_parts(
        "Draw an ERD for the case.\n\n(20 marks)")
    assert stem == ""
    assert len(parts) == 1
    assert parts[0]["label"] == ""
    assert parts[0]["marks"] == 20.0
    assert reasons == []


def test_build_parts_reads_letters_and_nested_marks():
    stem, parts, reasons = _build_parts(
        "Study the schema.\n\na) First.\n\n(4 marks)\n\n"
        "b) Second.\n\ni) One. (2 marks)\n\nii) Two. (6 marks)")
    assert stem == "Study the schema."
    assert [part["label"] for part in parts] == ["a", "b"]
    assert [part["marks"] for part in parts] == [4.0, 8.0]
    assert reasons == []


def test_latex_and_markdown_are_made_readable():
    latex = _latex_to_text(
        r"\text {CNF: (last_name like \%n') \wedge (postal_code = 'X')}")
    assert "\\text" not in latex
    assert "\\wedge" not in latex
    assert "(4 marks)" not in latex
    assert "CNF:" in latex
    assert "∧" in latex

    clean = _clean_md(
        "## QUESTION 1\n\n```txt\nSTAFF (StaffID, StaffName)\n```\n\n"
        "<table><tr><td>x</td></tr></table>\n\n(4 marks)\n\n"
        "CONFIDENTIAL")
    assert "```" not in clean
    assert "<table" not in clean
    assert "CONFIDENTIAL" not in clean
    assert "STAFF (StaffID, StaffName)" in clean
    assert "(4 marks)" in clean


def test_topic_tags_cover_database_topics():
    tags = _topic_tags(
        "Write an SQL query and draw a precedence graph for the transaction.")
    assert "sql" in tags
    assert "transaction" in tags or "concurrency_control" in tags


def test_owner_html_is_extracted_from_a_decision_comment():
    document, note = _owner_html(
        "Please use this. <html><body><p>Schema</p></body></html> Done.")
    assert document.startswith("<html>")
    assert "Schema" in document
    assert note == "Please use this.  Done."


def test_owner_html_recreation_wins_over_a_use_original_choice():
    asset = {
        "id": "A-TEST-Q1-T1",
        "path": "C:/bank/assets/A-TEST-Q1-T1.png",
        "review_original_path": "../assets/A-TEST-Q1-T1.png",
        "verdict": "pending",
    }
    updated, document, note = _apply_asset(asset, {
        "choice": "use_original",
        "comment": "<!DOCTYPE html><html><body>Schema</body></html>",
    })
    assert document.startswith("<!DOCTYPE html>")
    assert updated["review_choice"] == "use_recreation"
    assert updated["review_choice_original"] == "use_original"
    assert updated["owner_recreation_file"] == "A-TEST-Q1-T1.png"
    assert updated["verdict"] == "pending"
    assert "recreation was selected" in note


def test_use_original_without_html_is_approved():
    asset = {
        "id": "A-TEST-Q1-T1",
        "path": "C:/bank/assets/A-TEST-Q1-T1.png",
        "review_original_path": "../assets/A-TEST-Q1-T1.png",
        "verdict": "pending",
    }
    updated, document, note = _apply_asset(asset, {"choice": "use_original"})
    assert document == ""
    assert note == ""
    assert updated["review_choice"] == "use_original"
    assert updated["verdict"] == "approved"


def test_sql_code_detection_ignores_prose_imperatives():
    assert _is_code_line("SELECT L.LectName")
    assert _is_code_line("INSERT INTO STUDENT VALUES (1);")
    assert _is_code_continuation("WHERE Sc.ScYear = 2024")
    assert _is_code_continuation("AND Sc.ScYear = 2024")
    assert not _is_code_line("Select four distinct problems and state each briefly.")
    assert not _is_code_line("From Table 1, identify the measure Quantity.")


def test_part_level_points_sum_to_question_marks():
    question = {"parts": [{"label": "a", "marks": 6},
                          {"label": "b", "marks": 14}]}
    answer = {"subparts": [
        {"label": "a", "answer": "First answer."},
        {"label": "b", "answer": "Second answer."},
    ]}
    points = _part_level_points(question, answer)
    assert len(points) == 2
    assert points[0].startswith("6 marks: part a")
    assert points[1].startswith("14 marks: part b")
