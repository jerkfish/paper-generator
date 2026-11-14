"""Formatting rules for the ICT450 question-paper assembler."""
from collections import Counter

import docx
import pytest
from docx.shared import Pt

from src.bank.store import BankStore
from src.subjects.ict450.assemble import (
    BANK,
    CATEGORIES,
    _render_preamble,
    build_category_plans,
)


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


def test_library_plans_are_category_ordered_and_reuse_capped():
    if not BANK.exists():
        pytest.skip("ICT450 bank is not present")
    questions = list(BankStore(BANK).approved_questions())
    plans = build_category_plans(questions, seed_count=20, reuse_cap=4)
    assert len(plans) == 20
    uses: Counter[str] = Counter()
    for plan in plans:
        slots = plan["slots"]
        assert [slot["category"] for slot in slots] == list(CATEGORIES)
        assert len({slot["source_paper"] for slot in slots}) == 5
        assert sum(int(slot["marks"]) for slot in slots) == 100
        uses.update(slot["question_id"] for slot in slots)
    assert max(uses.values()) <= 4
