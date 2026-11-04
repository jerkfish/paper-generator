"""CSC402 stage-3 template candidate helpers (no Word/PDF build in tests)."""
from __future__ import annotations

from pathlib import Path

from src.subjects.csc402 import template_build


def test_cover_text_nodes_are_subject_specific():
    xml = (
        '<w:t>PRE</w:t><w:t xml:space="preserve"> </w:t>'
        '<w:t>CALCULUS</w:t><w:t>2026/MAT133</w:t>'
        '<w:t>CS/FEB</w:t><w:t>FEBRUARI</w:t>'
    )
    out = template_build._replace_text_nodes(xml)
    assert "PROGRAMMING" in out
    assert ">I<" in out
    assert "2026/CSC402" in out
    assert "CS/NOV" in out
    assert "NOVEMBER" in out
    assert "MAT133" not in out


def test_duration_and_title_box_are_corrected():
    xml = (
        '<v:shape style="left:3275;top:524;width:1873;height:1549">'
        '<w:t>2</w:t><w:t xml:space="preserve"> </w:t><w:t>HOURS</w:t>'
        '</v:shape>'
    )
    widened = template_build._widen_title_box(xml)
    assert "width:2250" in widened
    assert "width:1873" not in widened
    out = template_build._set_duration_hours(widened)
    assert "<w:t>3</w:t>" in out
    assert "<w:t>2</w:t>" not in out


def test_candidate_dry_run_does_not_write(tmp_path):
    source = tmp_path / "source.docx"
    source.write_bytes(b"placeholder")
    target = tmp_path / "out" / "CSC402 TEMPLATE.docx"
    result = template_build.build_candidate(source, target, apply=False)
    assert result["would_write"] is True
    assert not target.exists()
