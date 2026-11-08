"""Regression checks for the Stage-1 extraction problems found in review."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.skip(
    reason="legacy CSC429 Type C planner/generator/builder path retired by the P0 Type D strategy lock")

import json
from pathlib import Path

from src import config

TRACKING = config.TRACKING_DIR / "csc429"


def _bank() -> dict:
    return json.loads(
        (TRACKING / "question_bank_draft.json").read_text(encoding="utf-8"))


def _assets() -> dict:
    return json.loads(
        (TRACKING / "assets" / "manifest.json").read_text(encoding="utf-8"))


def test_a1_diagram_is_an_asset_not_flattened_prose():
    bank = _bank()
    question = next(
        row for row in bank["questions"]
        if row["question_id"] == "CSC429-2016-06-A10")
    assert "CSC429-2016-06-D1" in question["asset_ids"]
    assert question["text"].strip().endswith("example.")
    assert "Single Instruction" not in question["text"]
    assert "iv" not in question["text"].split()
    asset = next(
        row for row in _assets()["assets"]
        if row["asset_id"] == "CSC429-2016-06-D1")
    assert asset["kind"] == "figure"
    assert (config.PROJECT_ROOT / asset["path"]).is_file()
    assert asset["width_px"] > asset["height_px"]


def test_a4_third_subpart_and_continuation_are_recovered():
    bank = _bank()
    question = next(
        row for row in bank["questions"]
        if row["question_id"] == "CSC429-2014-06-A9")
    labels = [part["label"] for part in question["subparts"]]
    assert labels == ["a", "b", "c"]
    assert question["subparts"][2]["text"].rstrip().endswith("9(a).")
    assert [part["marks"] for part in question["subparts"]] == [1, 2, 2]


def test_a5_and_a8_figures_are_tightened_around_their_labels():
    assets = {row["asset_id"]: row for row in _assets()["assets"]}
    a5 = assets["CSC429-2024-07-F1"]
    a8 = assets["CSC429-2014-12-F2"]
    assert a5["tightened"] is True
    assert a8["tightened"] is True
    assert a5["bbox_pdf"][2] - a5["bbox_pdf"][0] < 0.45 * 597.84
    assert a8["bbox_pdf"][2] - a8["bbox_pdf"][0] < 0.35 * 594.72


def test_owner_verified_unsure_items_are_resolved():
    bank = _bank()
    by_id = {row["question_id"]: row for row in bank["questions"]}
    assert bank.get("unsure") == []
    assert len(bank.get("resolved_unsure") or []) == 6

    marks = {
        qid: [(part["label"], part["marks"])
              for part in by_id[qid]["subparts"]]
        for qid in ("CSC429-2014-06-A10", "CSC429-2023-07-A4")
    }
    assert marks["CSC429-2014-06-A10"] == [("a", 4), ("b", 4), ("c", 2)]
    assert marks["CSC429-2023-07-A4"] == [("a", 2), ("b", 3)]

    assert by_id["CSC429-2016-12-B1"]["figure_refs"] == ["Figure 4", "Table 3"]
    assert by_id["CSC429-2017-07-B1"]["figure_refs"] == ["Figure 2", "Table 2"]
    assert by_id["CSC429-2023-02-B1"]["figure_refs"] == ["Figure 4", "Table 3"]

    table = by_id["CSC429-2014-12-A1"]
    assert table["asset_ids"] == ["CSC429-2014-12-T1"]
    asset = next(
        row for row in _assets()["assets"]
        if row["asset_id"] == "CSC429-2014-12-T1")
    assert asset["kind"] == "table"
    assert len(asset["table_data"]["rows"]) == 6
    assert asset["table_data"]["rows"][0]["cells"][0]["text"] == "Scenario"
