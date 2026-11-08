"""CSC429 Stage-7 paper and marking-guide builder."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.skip(
    reason="legacy CSC429 Type C planner/generator/builder path retired by the P0 Type D strategy lock")

import json
from pathlib import Path

import docx
from docx.oxml.ns import qn

from src.subjects.csc429 import build_docx


def test_build_seed_writes_paper_and_scheme(tmp_path, monkeypatch):
    monkeypatch.setattr(
        build_docx.answers, "CACHE_PATH", tmp_path / "answers.json")
    result = build_docx.build_seed(
        1, tmp_path, export=False, force=True, allow_llm=False)
    assert result["problems"] == []
    for key in ("paper_docx", "scheme_docx"):
        assert Path(result["files"][key]).is_file()
    plan = json.loads((tmp_path / "plan.json").read_text(encoding="utf-8"))
    assert len(plan["slots"]) == 11
    assert sum(slot["marks"] for slot in plan["slots"]) == 100
    assert any(slot["kind"] == "generated_question"
               for slot in plan["slots"])
    assert any(slot["kind"] == "real_bank_question"
               for slot in plan["slots"])
    qa = json.loads((tmp_path / "qa.json").read_text(encoding="utf-8"))
    assert qa["paper_docx"]["xml_valid"] is True
    assert qa["scheme_docx"]["xml_valid"] is True
    assert qa["scheme_docx"]["inline_shapes"] >= 1
    assert qa["scheme_docx"]["compatibility_mode"] == 15
    assert qa["scheme_docx"]["cover_box_ok"] is True
    assert qa["scheme_docx"]["cover_groups"] >= 5
    assert qa["scheme_docx"]["cover_labels"]["COURSE"] >= 1
    scheme = docx.Document(result["files"]["scheme_docx"])
    cover_runs = scheme.paragraphs[0].runs
    drawing_at = next(index for index, run in enumerate(cover_runs)
                      if run._r.findall(qn("w:drawing")))
    label_at = next(index for index, run in enumerate(cover_runs)
                    if "CS/NOV" in run.text)
    assert drawing_at < label_at
    assert qa["forbidden_hits"] == []
    meta = json.loads((tmp_path / "meta.json").read_text(encoding="utf-8"))
    assert meta["total_marks"] == 100
    assert meta["question_count"] == 11
    assert meta["model"] == "csc429-deterministic"
    assert meta["builder_version"] == build_docx.BUILDER_VERSION
    assert meta["answers"]["failed"] == 9


def test_scheme_question_text_uses_clean_content_blocks():
    slot = {
        "text": "Raw OCR ffi /^ > Primary Memory CPU",
        "content": [
            {"type": "text", "text": "Explain the figure."},
            {"type": "figure", "asset_id": "CSC429-2024-07-F1"},
        ],
    }
    cleaned = build_docx._scheme_question_text(slot)
    assert cleaned.startswith("Explain the figure.")
    assert "Figure 1 reproduced in the question paper." in cleaned
    assert "ffi" not in cleaned
    assert "Primary Memory" not in cleaned


def test_paper_has_native_captions_and_scheme_has_no_question_body(
        tmp_path, monkeypatch):
    monkeypatch.setattr(
        build_docx.answers, "CACHE_PATH", tmp_path / "answers.json")
    result = build_docx.build_seed(
        1, tmp_path, export=False, force=True, allow_llm=False)
    plan = json.loads((tmp_path / "plan.json").read_text(encoding="utf-8"))
    scheme_text = build_docx._docx_text(Path(result["files"]["scheme_docx"]))
    paper_text = build_docx._docx_text(Path(result["files"]["paper_docx"]))
    for slot in plan["slots"]:
        if slot["kind"] != "real_bank_question":
            continue
        first_line = str(slot.get("text", "")).splitlines()[0].strip()
        if len(first_line) >= 20:
            assert first_line not in scheme_text
    assert "Figure 2: Conventional access architecture" in paper_text
