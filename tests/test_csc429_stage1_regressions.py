"""Regression checks for the Stage-1 extraction problems found in review."""
from __future__ import annotations

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
