"""MAT406 V5 seed assembly guards."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.subjects.mat406.assemble_v5 import build_plans

ROOT = Path(__file__).resolve().parents[1]
SEEDS = ROOT / "outputs" / "review" / "mat406_v2" / "seeds"


def _load(path: Path, default=None):
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def test_three_seed_plans_are_complete_and_distinct():
    plans = build_plans(3)
    if not plans:
        pytest.skip("MAT406 bank answers are not present")
    assert len(plans) == 3
    for plan in plans:
        assert len(plan["slots"]) == 8
        assert plan["total_marks"] == 100
        assert sum(row["marks"] for row in plan["slots"]) == 100
        assert len({row["question_id"] for row in plan["slots"]}) == 8
        assert len({row["source_paper"] for row in plan["slots"]}) == 8
        assert set(row["slot"] for row in plan["slots"]) == {
            "A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4"}


def test_seed_qa_and_files_are_present():
    if not (SEEDS / "seed_01" / "qa.json").is_file():
        pytest.skip("MAT406 V5 seeds are not built")
    for seed in (1, 2, 3):
        folder = SEEDS / f"seed_{seed:02d}"
        qa = _load(folder / "qa.json")
        assert qa["problems"] == []
        for name in ("paper.docx", "paper.pdf", "scheme.docx", "scheme.pdf",
                     "plan.json", "meta.json", "evidence.json"):
            assert (folder / name).is_file(), f"seed {seed} missing {name}"


def test_gate_b_is_not_approved_by_seed_build():
    state = _load(ROOT / "subjects" / "MAT406" / "lifecycle_state.json")
    assert state["gates"]["A"]["status"] == "approved"
    assert state["gates"]["B"]["status"] == "pending"
    assert state["stages"]["V5_seeds_1_3"]["status"] == "in_progress"
