"""CSC413 stage-3 template candidate helpers (no Word/PDF build in tests)."""
from __future__ import annotations

from src.subjects.csc413 import template_build


def test_cover_text_nodes_are_subject_specific():
    xml = (
        '<w:t>PRE</w:t><w:t xml:space="preserve"> </w:t>'
        '<w:t>CALCULUS</w:t><w:t>2026/MAT133</w:t>'
        '<w:t>CS/FEB</w:t><w:t>FEBRUARI</w:t>'
    )
    out = template_build._replace_text_nodes(xml)
    assert "INTRODUCTION TO" in out
    assert "INTERACTIVE MULTIMEDIA" in out
    assert "2026/CSC413" in out
    assert "CS/NOV" in out
    assert "NOVEMBER" in out
    assert "MAT133" not in out


def test_title_box_duration_and_two_line_fit():
    xml = (
        '<v:shape style="left:3275;top:524;width:1873;height:1549">'
        '<w:p><w:pPr><w:spacing w:line="245" w:lineRule="exact"/></w:pPr>'
        '<w:r><w:rPr><w:sz w:val="24"/></w:rPr>'
        '<w:t>INTRODUCTION TO</w:t></w:r></w:p>'
        '<w:t>2</w:t><w:t xml:space="preserve"> </w:t><w:t>HOURS</w:t>'
        '</v:shape>'
    )
    widened = template_build._widen_title_box(xml)
    assert "width:2650" in widened
    assert "width:1873" not in widened
    fitted = template_build._shrink_title_font(widened)
    assert 'w:val="18"' in fitted
    assert 'w:line="200"' in fitted
    out = template_build._set_duration_hours(fitted)
    assert "<w:t>3</w:t>" in out
    assert "<w:t>2</w:t>" not in out


def test_value_rows_break_after_course_code():
    xml = (
        '<w:p><w:pPr><w:spacing w:before="155" w:line="387" '
        'w:lineRule="auto"/></w:pPr><w:r><w:t>CSC413</w:t></w:r>'
        '<w:r><w:t xml:space="preserve"> </w:t></w:r>'
        '<w:r><w:t>NOVEMBER</w:t></w:r></w:p>'
    )
    out = template_build._align_value_rows(xml)
    assert 'w:before="0"' in out
    assert "<w:br/>" in out
    assert out.index("<w:br/>") < out.index("NOVEMBER")
