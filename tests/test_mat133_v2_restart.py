"""MAT133 restarted at V0 as a Type D recycle migration.

The rejected contract-only pilot is archived. v1 stays published and the v2
lifecycle begins with the raw working copies.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.app import jobs
from src.subjects.lifecycle import is_v2, load_state, status_report
from src.subjects.registry import get_subject

ROOT = Path(__file__).resolve().parents[1]
LIFECYCLE = ROOT / "subjects/MAT133/lifecycle_state.json"
LIFECYCLE_V1 = ROOT / "subjects/MAT133/lifecycle_state_v1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v1_lifecycle_is_still_preserved_verbatim():
    state = _load(LIFECYCLE)
    assert state["legacy_state"] == "subjects/MAT133/lifecycle_state_v1.json"
    assert state["legacy_state_sha256"] == hashlib.sha256(
        LIFECYCLE_V1.read_bytes()).hexdigest()
    v1 = _load(LIFECYCLE_V1)
    assert v1["schema_version"] == 1
    assert "0_intake" in v1["stages"]


def test_mat133_is_type_d_recycle():
    subject = get_subject("MAT133")
    assert subject.subject_type == "D"
    assert subject.strategy == "recycle"
    assert subject.variants["enabled"] is False
    assert subject.extraction["method"] == "mineru"
    assert subject.permissions["cloud_processing"]["allowed"] is True
    assert subject.permissions["cloud_processing"]["confirmed_on"] == (
        "2026-11-14")
    assert subject.public_document_versions == {"1"}


def test_v2_lifecycle_reaches_gate_a():
    state = _load(LIFECYCLE)
    assert state["schema_version"] == 2
    assert state["playbook_version"] == "2.0"
    assert state["type"] == "D"
    assert state["strategy"] == "recycle"
    assert is_v2(state)
    assert state["stages"]["V0_intake"]["status"] == "done"
    assert state["stages"]["V1_extract"]["status"] == "done"
    assert state["stages"]["V2_bank"]["status"] == "in_progress"
    assert set(state["gates"]) == {"A", "B", "C"}
    assert state["gates"]["A"]["status"] == "pending"
    assert state["gates"]["B"]["status"] == "pending"
    assert state["gates"]["C"]["status"] == "pending"
    assert state["bank"]["questions"] >= 0
    assert state["answers"]["solver_verified"] == 0

    report = status_report(ROOT, "MAT133")
    assert report["next_stage"] == "V2_bank"
    assert report["next_gate"] == "A"


def test_rejected_pilot_documents_are_not_in_the_library():
    item = jobs.library_item(1, "MAT133")
    if item is None:
        return
    assert len(item["versions"]) == 1
    assert item["versions"][0]["version"] == 1
    assert "paper_v2_docx" not in item["downloads"]
