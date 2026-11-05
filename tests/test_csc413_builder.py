"""CSC413 stage-7 DOCX builder (no Word/PDF dependency)."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

from src.subjects.csc413.build_docx import build_seed, _docx_text


def test_docx_paper_and_scheme_are_structurally_valid(tmp_path):
    qa = build_seed(1, tmp_path, export=False, force=True)
    assert qa["problems"] == []
    paper = Path(qa["files"]["paper_docx"])
    scheme = Path(qa["files"]["scheme_docx"])
    assert paper.is_file()
    assert scheme.is_file()
    assert qa["paper_docx"]["xml_valid"] is True
    assert qa["scheme_docx"]["xml_valid"] is True
    paper_text = _docx_text(paper)
    scheme_text = _docx_text(scheme)
    assert "PART A (15 MARKS)" in paper_text
    assert "PART B (15 MARKS)" in paper_text
    assert "PART C (30 MARKS)" in paper_text
    assert "PART D (40 MARKS)" in paper_text
    assert "CSC413" in paper_text
    assert "NOV 2026" in paper_text
    assert "MARKING SCHEME" in scheme_text
    assert "PART A - ANSWER KEY" in scheme_text
    assert "PART B - ANSWER KEY" in scheme_text
    assert "PART C - ANSWER KEY" in scheme_text
    assert "PART D - WORKED ANSWERS" in scheme_text
    assert "CSC662" not in paper_text
    assert "CSC662" not in scheme_text
    with zipfile.ZipFile(str(scheme)) as archive:
        xml = archive.read("word/document.xml").decode("utf-8")
    assert "NOV 2026 (MOCK)" in xml


def test_plugin_writes_library_meta(tmp_path):
    result = build_seed(2, tmp_path, export=False, force=True)
    assert result["accepted"] == 72
    assert result["total_marks"] == 100
    meta = json.loads((tmp_path / "meta.json").read_text(encoding="utf-8"))
    assert meta["subject"] == "CSC413"
    assert meta["accepted"] == meta["total_slots"] == 72
    assert meta["placeholders"] == 0
    assert meta["total_marks"] == 100
    assert meta["has_practice_mode"] is False
    assert meta["has_placeholders"] is False
    assert len(meta["progress"]) == 72
