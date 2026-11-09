"""ICT450 Stage-7 DOCX/QA builder tests (no PDF export)."""
from __future__ import annotations

from src.subjects.ict450.build_docx import _docx_text, build_seed


def test_build_seed_docx_and_scheme(tmp_path):
    result = build_seed(1, out_dir=tmp_path, export=False, force=True)
    assert result["problems"] == []
    paper = tmp_path / "ICT450 Seed 01 2026.docx"
    scheme = tmp_path / "ICT450 Seed 01 2026 - Marking Scheme.docx"
    assert paper.is_file()
    assert scheme.is_file()
    paper_text = _docx_text(paper)
    scheme_text = _docx_text(scheme)
    assert "ICT450" in paper_text
    assert "five (5) questions" in paper_text
    assert "QUESTION 5" in paper_text
    assert "CSC662" not in paper_text
    assert "PART A (10 Questions)" not in paper_text
    assert "MARKING SCHEME" in scheme_text
    assert "CSC662" not in scheme_text
    assert "Five questions x 20 marks = 100 marks." in scheme_text
