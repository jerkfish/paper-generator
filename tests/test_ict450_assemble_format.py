"""Formatting rules for the ICT450 question-paper assembler."""
import docx
from docx.shared import Pt

from src.subjects.ict450.assemble import _render_preamble


def test_sql_schema_captions_use_consolas_and_are_spaced():
    document = docx.Document()
    _render_preamble(
        document,
        "Based on the relational schema, write SQL commands.\n"
        "STUDENT (StudentID, Name)\n"
        "COURSE (CourseID, CourseName)\n"
        "a) Create the STUDENT table.",
        schema=True,
    )
    paragraphs = document.paragraphs
    first = next(p for p in paragraphs if p.text.startswith("STUDENT ("))
    last = next(p for p in paragraphs if p.text.startswith("COURSE ("))
    assert first.runs[0].font.name == "Consolas"
    assert first.runs[0].font.size == Pt(10)
    assert first.paragraph_format.space_before == Pt(8)
    assert first.paragraph_format.space_after == Pt(6)
    assert last.paragraph_format.space_after == Pt(8)


def test_erd_dash_block_gets_space_and_uniform_dashes():
    document = docx.Document()
    _render_preamble(
        document,
        "Intro paragraph.\n- Rule one.\n• Rule two.\nAfter paragraph.",
        dash_spacing=True,
    )
    dash = next(p for p in document.paragraphs if "Rule one." in p.text)
    assert dash.paragraph_format.space_before == Pt(10)
    assert dash.paragraph_format.space_after == Pt(10)
    assert dash.text == "- Rule one.\n- Rule two."


def test_other_questions_keep_single_normal_paragraph():
    document = docx.Document()
    _render_preamble(document, "Approved opening.\n- Approved dash.")
    assert len(document.paragraphs) == 1
    assert document.paragraphs[0].text == "Approved opening.\n- Approved dash."
