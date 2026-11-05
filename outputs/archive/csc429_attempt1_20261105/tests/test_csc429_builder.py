"""CSC429 stage-7 builder (DOCX-only; PDF export needs Word)."""
from __future__ import annotations

import json

import docx

from src.subjects.csc429.builder import build_seed


def test_build_seed_writes_valid_docx_pair(tmp_path):
    result = build_seed(1, out_dir=tmp_path, force=True, export=False)
    assert result["cached"] is False
    assert result["pdf"] is False
    for name in ("paper.docx", "scheme.docx", "meta.json", "qa.json"):
        assert (tmp_path / name).is_file()
    qa = json.loads((tmp_path / "qa.json").read_text(encoding="utf-8"))
    assert qa["problems"] == []
    assert qa["paper_docx"]["xml_valid"] is True
    assert qa["scheme_docx"]["xml_valid"] is True
    assert qa["paper_docx"]["question_headings"] == 11
    assert qa["paper_docx"]["part_labels_found"] == 27
    assert qa["paper_docx"]["answers_present"] == 0
    assert qa["scheme_docx"]["answers_present"] == 27
    assert qa["paper_docx"]["forbidden_tokens"] == []
    assert qa["scheme_docx"]["forbidden_tokens"] == []
    assert qa["paper_docx"]["figure_questions"] == 3
    assert qa["paper_docx"]["figure_captions_found"] == 3
    assert qa["paper_docx"]["media_count"] >= 4
    assert qa["scheme_docx"]["figure_questions"] == 3
    assert qa["scheme_docx"]["figure_captions_found"] == 3
    assert qa["scheme_docx"]["media_count"] >= 4
    assert len(list((tmp_path / "figures").glob("*.png"))) == 3


def test_build_seed_uses_15_spacing_and_question_separators(tmp_path):
    build_seed(1, out_dir=tmp_path, force=True, export=False)
    for name in ("paper.docx", "scheme.docx"):
        document = docx.Document(str(tmp_path / name))
        paragraphs = document.paragraphs
        headings = [
            index for index, paragraph in enumerate(paragraphs)
            if paragraph.text.startswith("QUESTION ")]
        assert len(headings) == 11
        for index in headings:
            assert paragraphs[index].paragraph_format.line_spacing == 1.5
            assert not paragraphs[index - 1].text.strip()
            assert (paragraphs[index - 1].paragraph_format.line_spacing
                    == 1.5)
            cursor = index + 1
            while (cursor < len(paragraphs)
                   and paragraphs[cursor].text.strip()
                   and not paragraphs[cursor].text.startswith(
                       ("QUESTION ", "PART "))):
                assert (paragraphs[cursor].paragraph_format.line_spacing
                        == 1.5)
                cursor += 1
    scheme = docx.Document(str(tmp_path / "scheme.docx"))
    scheme_text = "\n".join(p.text for p in scheme.paragraphs)
    assert "Computed slots: 4; descriptive slots: 7" in scheme_text
    assert "deterministic for seed 1" in scheme_text
    assert "CSC662" not in scheme_text


def test_build_seed_meta_shape(tmp_path):
    build_seed(1, out_dir=tmp_path, force=True, export=False)
    meta = json.loads((tmp_path / "meta.json").read_text(encoding="utf-8"))
    assert meta["subject"] == "CSC429"
    assert meta["seed"] == 1
    assert meta["mode"] == "realistic"
    assert meta["total_marks"] == 100
    assert meta["question_count"] == 11
    assert meta["accepted"] == 11
    assert meta["placeholders"] == 0
    assert meta["total_slots"] == 11
    assert meta["cost_usd"] == 0.0
    assert meta["year"] == 2026
    assert meta["files"]["paper_docx"].endswith("paper.docx")
    assert meta["files"]["scheme_docx"].endswith("scheme.docx")
    assert meta["files"]["paper_pdf"] == ""
    assert meta["files"]["scheme_pdf"] == ""
    assert len(meta["progress"]) == 27
    assert meta["figure_questions"] == 3
    assert len(meta["figures"]) == 3
    assert meta["summary"]["figure_questions"] == 3
    assert meta["summary"]["pdf_available"] is False
    assert meta["summary"]["qa_problems"] == []
