"""CSC429 Stage-7 paper and marking-guide builder."""
from __future__ import annotations

import json
from pathlib import Path

from src.subjects.csc429 import build_docx


def test_build_seed_writes_paper_and_scheme(tmp_path):
    result = build_docx.build_seed(1, tmp_path, export=False, force=True)
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
    assert qa["forbidden_hits"] == []
    meta = json.loads((tmp_path / "meta.json").read_text(encoding="utf-8"))
    assert meta["total_marks"] == 100
    assert meta["question_count"] == 11
    assert meta["model"] == "csc429-deterministic"
