"""CSC402 stage-7 DOCX builder (no Word/PDF dependency)."""
from __future__ import annotations

from pathlib import Path

from src.subjects.csc402.build_docx import build_seed


def test_docx_paper_and_scheme_are_structurally_valid(tmp_path):
    qa = build_seed(1, tmp_path, export=False)
    assert qa["problems"] == []
    paper = Path(qa["files"]["paper_docx"])
    scheme = Path(qa["files"]["scheme_docx"])
    assert paper.is_file()
    assert scheme.is_file()
    assert qa["paper_docx"]["xml_valid"] is True
    assert qa["scheme_docx"]["xml_valid"] is True
    assert qa["paper_docx"]["forbidden_tokens"] == []
    assert qa["scheme_docx"]["forbidden_tokens"] == []
    assert not qa["paper_docx"]["missing"]
    assert not qa["scheme_docx"]["missing"]
    assert (tmp_path / "paper.json").is_file()
    assert (tmp_path / "qa.json").is_file()
    from src.subjects.csc402.build_docx import _docx_text
    scheme_text = _docx_text(scheme)
    assert "MARKING SCHEME" in scheme_text
    assert "Part A = 10 x 1 mark" in scheme_text
    assert "CSC662" not in scheme_text
    import zipfile
    with zipfile.ZipFile(str(scheme)) as archive:
        xml = archive.read("word/document.xml").decode("utf-8")
    assert "NOV 2026 (MOCK)" in xml
