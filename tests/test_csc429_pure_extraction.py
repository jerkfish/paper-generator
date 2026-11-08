"""Type D asset-first CSC429 strategy and bank integrity tests."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

from src import config
from src.subjects.registry import get_subject

SUBJECT = "CSC429"
BANK = config.TRACKING_DIR / "csc429" / "bank"
REGISTRY = config.TRACKING_DIR / "csc429" / "rejected_registry.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def bank():
    if not (BANK / "questions_index.json").is_file():
        pytest.skip("CSC429 P1 bank has not been generated")
    return {
        "index": _load(BANK / "index.json"),
        "questions": _load(BANK / "questions_index.json")["questions"],
        "assets": _load(BANK / "assets_index.json")["assets"],
        "unsure": _load(BANK / "unsure.json")["items"],
    }


def test_strategy_lock_is_type_d_and_disables_legacy_paths():
    subject = get_subject(SUBJECT)
    assert subject.subject_type == "D"
    assert subject.status == "available"
    assert set(subject.plugins) <= {"library_seeds", "library_metadata", "prebuild"}
    assert "plan" not in subject.plugins
    assert subject.enabled_computed_generators == []
    payload = _load(config.PROJECT_ROOT / "subjects" / SUBJECT / "subject.json")
    assert payload["strategy"] == "pure_extraction"
    assert payload["generators_enabled"] == []
    assert payload["parametric_variants"] is False


def test_bank_counts_and_contract_files(bank):
    assert bank["index"]["papers"] == 20
    assert bank["index"]["questions"] == 215
    assert bank["index"]["assets"] == 96
    assert bank["index"]["questions_with_assets"] == 67
    assert (BANK / "questions_index.json").is_file()
    assert (BANK / "assets_index.json").is_file()
    assert (BANK / "corrections.json").is_file()
    assert (BANK / "approvals.json").is_file()
    assert (BANK / "unsure.json").is_file()
    assert (BANK / "unsure.md").is_file()


def test_every_asset_belongs_to_its_question(bank):
    assets = {row["id"]: row for row in bank["assets"]}
    for row in bank["questions"]:
        for aid in row.get("assets") or []:
            asset = assets[aid]
            assert asset["source_paper"] == row["source_paper"]
            assert row["id"] in asset["question_ids"]


def test_reference_integrity_is_explicit(bank):
    assets = {row["id"]: row for row in bank["assets"]}
    unresolved = [item for item in bank["unsure"]
                  if item["code"] == "unresolved_reference"]
    assert len(unresolved) == 8
    for item in unresolved:
        assert item["path"]
        assert item["pages"]
    for row in bank["questions"]:
        labels = {assets[aid]["label"].lower() for aid in row.get("assets") or []}
        for ref in row.get("refs") or []:
            if ref.lower() in labels:
                continue
            if re.match(r"^(Figure|Table)\s+\d+$", ref, re.I):
                assert any(item["question_id"] == row["id"]
                           for item in unresolved), row["id"]


def test_rejected_registry_never_matches_new_assets(bank):
    registry = _load(REGISTRY)
    rejected = set(registry["assets"])
    assert registry["counts"]["assets"] > 0
    for asset in bank["assets"]:
        assert asset["sha256"] not in rejected


def test_review_sheets_exist_for_all_papers(bank):
    review = BANK / "review"
    assert (review / "index.html").is_file()
    assert len(list(review.glob("CSC429-*.html"))) == 20
    assert len(bank["questions"]) == 215
    assert (BANK / "review_index.json").is_file()


def test_bank_rebuild_is_idempotent_and_keeps_approvals(bank):
    from src.subjects.csc429 import pure_bank
    before = hashlib.sha256(
        "\n".join(
            f"{path.name}:{path.read_text(encoding='utf-8')}"
            for path in sorted((BANK / "questions").glob("*.json"))
        ).encode("utf-8")
    ).hexdigest()
    summary = pure_bank.build()
    after = hashlib.sha256(
        "\n".join(
            f"{path.name}:{path.read_text(encoding='utf-8')}"
            for path in sorted((BANK / "questions").glob("*.json"))
        ).encode("utf-8")
    ).hexdigest()
    assert summary["questions"] == 215
    assert summary["assets"] == 96
    assert before == after
    assert summary["cost_usd"] == 0.0
