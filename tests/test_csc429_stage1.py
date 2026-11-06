"""CSC429 Stage 1 report aggregation."""
from __future__ import annotations

import json

from src.subjects.csc429 import stage1


def _write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_stage1_report_aggregates_artifacts(tmp_path, monkeypatch):
    tracking = tmp_path / "csc429"
    _write(tracking / "papers_register.json", [
        {"source": "paper.pdf", "month": "JANUARY", "year": 2024,
         "source_kind": "text", "duplicate_of": ""},
        {"source": "dup.pdf", "month": "JANUARY", "year": 2024,
         "source_kind": "text", "duplicate_of": "paper.pdf"},
    ])
    _write(tracking / "papers_summary.json", {
        "subject": "CSC429", "total": 2, "unique": 1, "duplicates": 1,
        "duplicate_groups": [{"canonical": "paper.pdf",
                              "duplicates": ["dup.pdf"]}],
    })
    _write(tracking / "pages_manifest.json", {"pages": 2, "dpi": 200})
    _write(tracking / "layout_manifest.json", {
        "lines": 10, "caption_lines": 1})
    _write(tracking / "assets" / "manifest.json", {
        "assets": [
            {"asset_id": "A", "kind": "figure", "confidence": "high"},
            {"asset_id": "B", "kind": "table", "confidence": "medium"},
        ],
        "unresolved": [{"label": "Figure 2"}],
    })
    _write(tracking / "question_bank_draft.json", {
        "questions": [
            {"question_id": "Q1", "part": "A", "marks": 5,
             "asset_ids": ["A"]},
            {"question_id": "Q2", "part": "A", "marks": None,
             "asset_ids": []},
            {"question_id": "Q3", "part": "B", "marks": 20,
             "asset_ids": ["B"]},
        ],
        "unsure": [{"id": "u1", "reason": "missing marks"}],
    })
    monkeypatch.setattr(stage1, "TRACKING", tracking)
    monkeypatch.setattr(stage1.config, "PROJECT_ROOT", tmp_path)
    report = stage1.build_report()
    assert report["status"] == "ok"
    assert report["inputs"]["unique"] == 1
    assert report["inputs"]["duplicates"] == 1
    assert report["pages"]["rendered"] == 2
    assert report["assets"]["total"] == 2
    assert report["assets"]["by_kind"] == {"figure": 1, "table": 1}
    assert report["questions"]["total"] == 3
    assert report["questions"]["with_marks"] == 2
    assert report["questions"]["with_assets"] == 2
    assert report["unsure_count"] == 1
    summary = json.loads(
        (tracking / "papers_summary.json").read_text(encoding="utf-8"))
    assert summary["assets"]["figures"] == 1
    assert summary["assets"]["questions_extracted"] == 3
    assert summary["assets"]["status"] == "ok"
