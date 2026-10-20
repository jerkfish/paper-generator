"""Planner invariants: 24 slots, 100 marks, no repeated cipher types."""
from __future__ import annotations

import pytest

from src.planner.calibration import CALIBRATIONS
from src.planner.planner import build_plan


def test_realistic_slot_shape_and_distribution():
    table, summary = build_plan("realistic", "modern", None, 9)
    assert len(table) == 24
    assert sum(s.marks for s in table) == 100
    assert sum(s.marks for s in table if s.slot.startswith("A")) == 80
    assert sum(s.marks for s in table if s.slot.startswith("B")) == 20
    assert summary["computed_marks"] == 6
    computed = [s for s in table if s.kind == "computed"]
    assert len(computed) == 1
    assert computed[0].computed_type == "vigenere"
    assert all(s.topic for s in table)
    assert all(s.task for s in table)


def test_practice_default_is_22_marks_without_repeated_types():
    table, summary = build_plan("practice", "modern", None, 9)
    assert summary["computed_marks"] == 22
    computed = [s for s in table if s.kind == "computed"]
    assert sum(s.marks for s in computed) == 22
    types = [s.computed_type for s in computed]
    assert len(types) == len(set(types))
    acm = [s for s in computed if s.computed_type == "acm"]
    assert all(s.acm_scope == "matrix only (6 marks)" for s in acm)


def test_older_realistic_is_rejected():
    with pytest.raises(SystemExit):
        build_plan("realistic", "older", None, 9)


def test_older_practice_can_use_playfair_or_affine():
    table, _ = build_plan("practice", "older", 22, 9)
    types = {s.computed_type for s in table if s.kind == "computed"}
    assert "playfair" in types or "affine" in types


def test_calibration_reports_widening_and_acm_scope():
    assert any(c.n < 3 and "widened" in c.note for c in CALIBRATIONS)
    assert any(c.kind == "acm" and "matrix only" in c.note
               for c in CALIBRATIONS)
