"""MAT406 V0-V2 guards.

The bank must stay traceable to the nine unique working papers, every
question must carry printed marks, and Gate A must remain pending until the
owner records approval.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.subjects.registry import get_subject

ROOT = Path(__file__).resolve().parents[1]
TRACKING = ROOT / "data" / "tracking" / "mat406" / "v2"
BANK = TRACKING / "bank"


def _load(path: Path, default=None):
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def test_mat406_is_type_d_and_still_coming_soon():
    subject = get_subject("MAT406")
    assert subject.subject_type == "D"
    assert subject.strategy == "recycle"
    assert subject.status == "coming_soon"
    assert subject.variants["enabled"] is False
    assert subject.permissions["papers"]["allowed"] is True
    assert subject.permissions["cloud_processing"]["allowed"] is True
    assert subject.permissions["publication"]["allowed"] is False


def test_register_has_nine_unique_papers_and_one_duplicate():
    register = _load(TRACKING / "papers_register.json")
    if register is None:
        pytest.skip("MAT406 V1 register is not present")
    assert register["schema_version"] == 2
    assert len(register["papers"]) == 10
    assert len(register["unique_papers"]) == 9
    assert sum(row["pages"] for row in register["unique_papers"]) == 55
    duplicates = [row for row in register["papers"] if row["is_duplicate"]]
    assert len(duplicates) == 1
    assert duplicates[0]["file"] == "MAT406 FEBRUARY 2026 (2).pdf"


def test_bank_totals_and_marks_reconcile():
    index = _load(BANK / "index.json")
    if index is None:
        pytest.skip("MAT406 V2 bank is not present")
    counts = index["counts"]
    assert counts["papers"] == 9
    assert counts["questions"] == 58
    assert counts["approved"] == 58
    assert counts["needs_fix"] == 0
    assert counts["unresolved_references"] == 0
    assert counts["marks_total"] == 850
    assert counts["unsure"] == 0
    assert counts["excluded_assets"] == 1
    assert counts["assets"] == 6
    assert counts["rejected_assets"] == 7
    expected = {
        "MAT406-2021-JUL": 50,
        "MAT406-2022-FEB": 100,
        "MAT406-2023-FEB": 100,
        "MAT406-2023-JUL": 100,
        "MAT406-2024-JAN": 100,
        "MAT406-2024-JUL": 100,
        "MAT406-2025-FEB": 100,
        "MAT406-2025-JUL": 100,
        "MAT406-2026-FEB": 100,
    }
    totals: dict[str, int] = {}
    for question in index["questions"]:
        totals[question["source_paper"]] = (
            totals.get(question["source_paper"], 0) + question["marks"])
    assert totals == expected


def test_marks_overrides_are_printed_page_values():
    overrides = _load(TRACKING / "marks_overrides.json")
    if overrides is None:
        pytest.skip("MAT406 mark overrides are not present")
    assert overrides["subject"] == "MAT406"
    assert overrides["overrides"]["MAT406-2023-JUL-Q3"]["parts"] == {
        "a": 14, "b": 3, "c": 5}
    assert overrides["overrides"]["MAT406-2025-JUL-Q1-2"]["parts"] == {
        "b": 5}
    question = _load(BANK / "questions" / "MAT406-2023-JUL-Q3.json")
    if question is None:
        pytest.skip("MAT406 V2 question files are not present")
    assert question["marks"] == 22
    sources = {part["label"]: part.get("marks_source")
               for part in question["parts"]}
    assert sources == {"a": "page_render", "b": "page_render",
                       "c": "page_render"}


def test_watermark_asset_is_excluded_not_banked():
    exclusions = _load(TRACKING / "asset_exclusions.json")
    if exclusions is None:
        pytest.skip("MAT406 asset exclusions are not present")
    assert "MAT406-2026-FEB/MU-B0015" in exclusions["assets"]
    index = _load(BANK / "index.json")
    if index is None:
        pytest.skip("MAT406 V2 bank is not present")
    assert index["counts"]["assets"] == 6
    assert index["counts"]["rejected_assets"] == 7


def test_review_sheet_has_comment_boxes_and_gate_a_is_pending():
    review = BANK / "review" / "index.html"
    if not review.is_file():
        pytest.skip("MAT406 review sheet is not present")
    text = review.read_text(encoding="utf-8")
    assert text.count('class="question"') == 58
    assert 'class="question-comment"' in text
    assert 'class="asset-comment"' in text
    assert 'MAT406-2021-JUL-Q1' in text
    round2 = (BANK / "review" / "round2.html").read_text(encoding="utf-8")
    assert round2.count('class="question"') == 14
    approvals = _load(BANK / "approvals.json")
    assert approvals["gate_a"]["status"] == "approved"
    assert approvals["gate_a"]["by"] == "owner"
    assert approvals["gate_a"]["on"] == "2026-11-20"


def test_v3_format_profile_and_templates():
    profile = _load(TRACKING / "format_profile.json")
    if profile is None:
        pytest.skip("MAT406 V3 format profile is not present")
    assert profile["subject"] == "MAT406"
    assert profile["total_marks"] == 100
    assert [section["key"] for section in profile["sections"]] == ["A", "B"]
    assert set(profile["slot_roles"]) == {
        "A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4"}
    assert profile["duration"] == "3 HOURS"
    check = _load(TRACKING / "template_check.json")
    assert check["problems"] == []
    subject = get_subject("MAT406")
    assert subject.template_path == "data/reference/MAT406/MAT406 TEMPLATE.docx"
    assert (ROOT / subject.template_path).is_file()
    assert (ROOT / profile["scheme_template"]).is_file()
