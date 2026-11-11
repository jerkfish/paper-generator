"""Phase 2: shared bank, assembler, lifecycle v2, scaffolds and gates."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src import config
from src.assemble.recycle import (
    SlotRequirement,
    build_plans,
    feasibility,
    requirements_from_sections,
)
from src.bank.duplicates import cluster_duplicates
from src.bank.gates import GateBlocked, require_seed_gate
from src.bank.schema import question_content_hash
from src.bank.store import BankStore
from src.bank.validators import validate_seed_plan
from src.subjects import lifecycle
from scripts import new_subject


def _question(qid: str, *, marks: int = 10, part: str = "A",
              status: str = "approved", text: str | None = None,
              assets: list[str] | None = None,
              refs: list[str] | None = None) -> dict:
    row = {
        "id": qid,
        "source_paper": "PAPER-2024-JUN",
        "part": part,
        "marks": marks,
        "status": status,
        "subpart_marks": [{"label": "a", "marks": marks}],
        "native_text_blocks": [
            {"text": text or f"Question {qid} about database normalisation."}
        ],
        "assets": list(assets or []),
        "refs": list(refs or []),
    }
    row["content_hash"] = question_content_hash(row)
    return row


def _asset(aid: str, label: str, *, verdict: str = "approved") -> dict:
    return {
        "id": aid,
        "kind": "figure",
        "label": label,
        "source_paper": "PAPER-2024-JUN",
        "verdict": verdict,
        "sha256": f"sha-{aid}",
    }


def _store(tmp_path: Path) -> BankStore:
    return BankStore(tmp_path / "bank").ensure()


def _plan(store: BankStore, qid: str, *, marks: int = 10,
          part: str = "A", content_hash: str | None = None) -> dict:
    question = store.load_question(qid)
    return {
        "seed": 1,
        "slots": [{
            "slot": f"{part}1",
            "part": part,
            "marks": marks,
            "question_id": qid,
            "content_hash": (content_hash if content_hash is not None
                             else question.get("content_hash")),
        }],
    }


def test_scaffold_defaults_to_type_d_with_v2_lifecycle_and_bank(tmp_path):
    root = tmp_path / "project"
    (root / "subjects" / "BASE01").mkdir(parents=True)
    (root / "subjects" / "BASE01" / "subject.json").write_text(
        json.dumps({"code": "BASE01", "title": "Base", "status": "coming_soon",
                    "type": "C"}), encoding="utf-8")
    new_subject.scaffold(root, "TESTD", "Database Systems", "D")
    subject = json.loads(
        (root / "subjects/TESTD/subject.json").read_text(encoding="utf-8"))
    assert subject["type"] == "D"
    assert subject["strategy"] == "recycle"
    assert subject["variants"]["enabled"] is False
    assert subject["library"]["size_policy"] == "min(20, feasible)"
    state = json.loads((root / "subjects/TESTD/lifecycle_state.json")
                       .read_text(encoding="utf-8"))
    assert state["schema_version"] == 2
    assert state["stages"]["V0_intake"]["status"] == "in_progress"
    assert set(state["gates"]) == {"A", "B", "C"}
    for name in ("questions", "assets", "plans", "review", "inbox"):
        assert (root / "data/tracking/testd/bank" / name).is_dir()
    report = lifecycle.status_report(root, "TESTD")
    assert report["lifecycle_schema"] == 2
    assert report["next_stage"] == "V0_intake"
    assert report["next_gate"] is None


def test_cli_defaults_to_d_and_dry_run_writes_nothing(tmp_path):
    root = tmp_path / "project"
    (root / "subjects" / "BASE01").mkdir(parents=True)
    (root / "subjects" / "BASE01" / "subject.json").write_text(
        json.dumps({"code": "BASE01", "title": "Base", "status": "coming_soon",
                    "type": "C"}), encoding="utf-8")
    plan = new_subject.scaffold(root, "TESTD", "Database", "D", dry_run=True)
    assert plan["subject"]["strategy"] == "recycle"
    assert not (root / "subjects" / "TESTD").exists()


def test_v1_state_is_read_only_and_still_maps_to_old_stages(tmp_path):
    root = tmp_path / "project"
    subject_dir = root / "subjects" / "OLD01"
    subject_dir.mkdir(parents=True)
    (subject_dir / "subject.json").write_text(json.dumps({
        "code": "OLD01", "title": "Old", "status": "available", "type": "C",
    }), encoding="utf-8")
    state = {
        "schema_version": 2,  # legacy number, v1 stage keys
        "subject": "OLD01",
        "type": "C",
        "stages": {"0_intake": {"status": "in_progress", "evidence": [],
                                "human_approval": {
                                    "required": True, "approved": False}}},
        "unsure": [],
        "llm_cost": {"total_usd": 0.0},
    }
    (subject_dir / "lifecycle_state.json").write_text(
        json.dumps(state), encoding="utf-8")
    report = lifecycle.status_report(root, "OLD01")
    assert report["lifecycle_schema"] == 1
    assert report["next_stage"] == "0_intake"
    assert report["human_checkpoint"] is True


def test_validator_accepts_approved_question_with_resolved_reference(tmp_path):
    store = _store(tmp_path)
    store.save_asset(_asset("A1", "Figure 1"))
    store.save_question(_question("Q1", assets=["A1"], refs=["Figure 1"]))
    validate_seed_plan(_plan(store, "Q1"), store,
                       expected_slots=1, expected_marks=10)


def test_validator_refuses_unapproved_question(tmp_path):
    store = _store(tmp_path)
    store.save_question(_question("Q1", status="extracted"))
    with pytest.raises(ValueError, match="not approved"):
        validate_seed_plan(_plan(store, "Q1"), store)


def test_validator_refuses_marks_mismatch(tmp_path):
    store = _store(tmp_path)
    store.save_question(_question("Q1", marks=10))
    with pytest.raises(ValueError, match="mark mismatch"):
        validate_seed_plan(_plan(store, "Q1", marks=8), store)


def test_validator_refuses_unresolved_reference(tmp_path):
    store = _store(tmp_path)
    store.save_question(_question("Q1", refs=["Figure 3"]))
    with pytest.raises(ValueError, match="unresolved reference"):
        validate_seed_plan(_plan(store, "Q1"), store)


def test_validator_refuses_asset_not_approved_or_wrong_paper(tmp_path):
    store = _store(tmp_path)
    store.save_asset(_asset("A1", "Figure 1", verdict="pending"))
    store.save_question(_question("Q1", assets=["A1"], refs=["Figure 1"]))
    with pytest.raises(ValueError, match="not approved"):
        validate_seed_plan(_plan(store, "Q1"), store)

    asset = _asset("A2", "Figure 2")
    asset["source_paper"] = "OTHER"
    store.save_asset(asset)
    store.save_question(_question("Q2", assets=["A2"], refs=["Figure 2"]))
    with pytest.raises(ValueError, match="belongs to"):
        validate_seed_plan(_plan(store, "Q2"), store)


def test_validator_refuses_changed_content_hash_and_in_seed_repeat(tmp_path):
    store = _store(tmp_path)
    store.save_question(_question("Q1"))
    with pytest.raises(ValueError, match="content hash changed"):
        validate_seed_plan(_plan(store, "Q1", content_hash="deadbeef"), store)
    repeated = _plan(store, "Q1")
    repeated["slots"].append(dict(repeated["slots"][0], slot="A2"))
    with pytest.raises(ValueError, match="reuses a question"):
        validate_seed_plan(repeated, store)


def test_feasibility_and_reuse_cap():
    questions = [_question(f"Q{i}") for i in range(1, 5)]
    requirements = [SlotRequirement("A1", "A", 10),
                    SlotRequirement("A2", "A", 10)]
    report = feasibility(questions, requirements, reuse_cap=4, max_seeds=20)
    assert report["distinct_seeds_without_reuse"] == 2
    assert report["max_seeds_with_cap"] == 8
    assert report["feasible_seeds"] == 8
    assert report["library_size"] == 8
    assert report["missing_classes"] == []


def test_build_plans_is_approved_only_and_never_repeats_in_a_seed():
    questions = [_question(f"Q{i}") for i in range(1, 5)]
    questions.append(_question("BAD", status="needs_fix"))
    requirements = requirements_from_sections([
        {"key": "A", "questions": 2, "marks_per_slot": 10}])
    plans = build_plans(questions, requirements, seed_count=4, reuse_cap=2)
    assert len(plans) == 4
    for plan in plans:
        ids = [slot["question_id"] for slot in plan["slots"]]
        assert len(ids) == len(set(ids))
        assert "BAD" not in ids
        assert plan["total_marks"] == 20
    counts = {}
    for plan in plans:
        for slot in plan["slots"]:
            counts[slot["question_id"]] = counts.get(
                slot["question_id"], 0) + 1
    assert max(counts.values()) <= 2


def test_build_plans_refuses_when_reuse_cap_is_exhausted():
    questions = [_question(f"Q{i}") for i in range(1, 3)]
    requirements = [SlotRequirement("A1", "A", 10),
                    SlotRequirement("A2", "A", 10)]
    with pytest.raises(ValueError, match="reuse cap"):
        build_plans(questions, requirements, seed_count=2, reuse_cap=1)


def test_near_duplicate_pairs_are_reported_not_merged():
    from src.bank.duplicates import near_duplicate_pairs

    left = _question("Q1", text="Explain database normalisation and its "
                                "normal forms with examples.")
    right = _question("Q2", text="Explain database normalisation and its "
                                 "normal forms using examples.")
    other = _question("Q3", text="Write a SQL query for the loan table.")
    pairs = near_duplicate_pairs([left, right, other])
    assert any({pair["left"], pair["right"]} == {"Q1", "Q2"}
               for pair in pairs)
    assert all("Q3" not in {pair["left"], pair["right"]} for pair in pairs)


def test_duplicate_clusters_pick_an_approved_canonical():
    same = "Explain database normalisation and its normal forms."
    questions = [
        _question("Q1", text=same, status="extracted"),
        _question("Q2", text=same, status="approved"),
        _question("Q3", text="Explain indexing."),
    ]
    clusters = cluster_duplicates(questions)
    duplicate = [row for row in clusters if row["count"] == 2][0]
    assert duplicate["canonical_id"] == "Q2"
    assert set(duplicate["ids"]) == {"Q1", "Q2"}


def test_bank_status_reports_counts_quality_and_duplicates(
        tmp_path, monkeypatch):
    from src.bank.cli import bank_status

    root = tmp_path / "project"
    tracking = tmp_path / "tracking"
    monkeypatch.setattr(config, "PROJECT_ROOT", root)
    monkeypatch.setattr(config, "TRACKING_DIR", tracking)
    _write_gate_subject(root, tracking)
    store = BankStore(tracking / "testd" / "bank")
    store.save_question(_question("Q2", status="needs_fix"))
    store.save_asset(_asset("A1", "Figure 1"))

    payload = bank_status("TESTD")
    assert payload["questions"] == 2
    assert payload["assets"] == 1
    assert payload["approved"] == 1
    assert payload["statuses"] == {"approved": 1, "needs_fix": 1}
    assert payload["duplicate_clusters"] == 0
    assert 0.0 <= payload["quality_average"] <= 1.0


def test_review_sheet_is_html_and_exports_decisions(tmp_path):
    from src.bank.review import build_review_sheet

    store = _store(tmp_path)
    question = _question("Q1", assets=["A1"], refs=["Figure 1"])
    store.save_question(question)
    store.save_asset(_asset("A1", "Figure 1"))
    index = build_review_sheet(store, store.review_dir, subject="TESTD")
    page = index.read_text(encoding="utf-8")
    assert "question bank review" in page
    assert 'data-qid="Q1"' in page
    assert "exportDecisions" in page


def _write_gate_subject(root: Path, tracking: Path) -> None:
    subject_dir = root / "subjects" / "TESTD"
    subject_dir.mkdir(parents=True)
    (subject_dir / "subject.json").write_text(json.dumps({
        "code": "TESTD", "title": "Database", "status": "available",
        "type": "D", "strategy": "recycle",
    }), encoding="utf-8")
    state = lifecycle.new_state_v2("TESTD")
    state["stages"]["V0_intake"]["status"] = "done"
    (subject_dir / "lifecycle_state.json").write_text(
        json.dumps(state), encoding="utf-8")
    store = BankStore(tracking / "testd" / "bank").ensure()
    store.save_question(_question("Q1"))


def test_gate_a_and_b_block_seed_assembly(tmp_path, monkeypatch):
    root = tmp_path / "project"
    tracking = tmp_path / "tracking"
    monkeypatch.setattr(config, "PROJECT_ROOT", root)
    monkeypatch.setattr(config, "TRACKING_DIR", tracking)
    _write_gate_subject(root, tracking)

    with pytest.raises(GateBlocked, match="Gate A"):
        require_seed_gate("TESTD", 1)

    state_path = root / "subjects/TESTD/lifecycle_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["gates"]["A"]["status"] = "approved"
    state_path.write_text(json.dumps(state), encoding="utf-8")
    require_seed_gate("TESTD", 1)

    with pytest.raises(GateBlocked, match="Gate B"):
        require_seed_gate("TESTD", 4)

    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["gates"]["B"]["status"] = "approved"
    state_path.write_text(json.dumps(state), encoding="utf-8")
    require_seed_gate("TESTD", 4)


def test_gate_a_cannot_be_honoured_without_approved_questions(
        tmp_path, monkeypatch):
    root = tmp_path / "project"
    tracking = tmp_path / "tracking"
    monkeypatch.setattr(config, "PROJECT_ROOT", root)
    monkeypatch.setattr(config, "TRACKING_DIR", tracking)
    _write_gate_subject(root, tracking)
    store = BankStore(tracking / "testd" / "bank")
    question = store.load_question("Q1")
    question["status"] = "needs_fix"
    store.save_question(question)
    state_path = root / "subjects/TESTD/lifecycle_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["gates"]["A"]["status"] = "approved"
    state_path.write_text(json.dumps(state), encoding="utf-8")
    with pytest.raises(GateBlocked, match="no approved questions"):
        require_seed_gate("TESTD", 1)
