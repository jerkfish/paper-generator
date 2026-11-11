"""Hard guards for Type D seed assembly."""
from __future__ import annotations

from pathlib import Path

from src import config
from src.subjects.csc429 import pure_gate
from src.bank.store import BankStore, load_json
from src.bank.validators import validate_seed_plan

TRACKING = config.TRACKING_DIR / "csc429"
BANK = TRACKING / "bank"
REJECTED = TRACKING / "rejected_registry.json"


def _load(path: Path, default):
    return load_json(path, default)


def _rejected_hashes() -> set[str]:
    return BankStore(BANK).rejected_hashes(REJECTED)


def validate_plan(plan: dict) -> None:
    pure_gate.require_gate()
    validate_seed_plan(
        plan,
        BankStore(BANK),
        expected_slots=11,
        expected_marks=100,
        rejected_hashes=_rejected_hashes(),
        require_assets=True,
        require_content_hash=True,
        check_part=True,
    )


def validate_plan_file(path: Path) -> dict:
    plan = _load(path, {})
    validate_plan(plan)
    return plan
