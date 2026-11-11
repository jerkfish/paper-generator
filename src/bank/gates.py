"""Human-gate enforcement for recycle subjects.

The playbook has exactly three gates:

* Gate A — bank approved, required before any seed is assembled;
* Gate B — the first seeds approved, required for seed 4 and later;
* Gate C — publish approved, checked by the bundle/upload commands.

Only subjects whose ``strategy`` is ``recycle`` are checked here.  Legacy
pipelines keep their own guards; this module must not change their behaviour.
"""
from __future__ import annotations

from pathlib import Path

from src import config
from src.subjects import lifecycle
from src.subjects.registry import get_subject


class GateBlocked(RuntimeError):
    pass


def bank_root(subject_code: str) -> Path:
    return Path(config.TRACKING_DIR) / subject_code.lower() / "bank"


def state_path(subject_code: str) -> Path:
    return (Path(config.PROJECT_ROOT) / "subjects" / subject_code.upper()
            / "lifecycle_state.json")


def load_lifecycle(subject_code: str) -> dict:
    return lifecycle.load_state(
        Path(config.PROJECT_ROOT), subject_code) or {}


def _require_recycle(subject_code: str):
    subject = get_subject(subject_code)
    if subject.strategy != "recycle":
        return None
    state = load_lifecycle(subject_code)
    if not state:
        raise GateBlocked(
            f"{subject.code}: lifecycle_state.json is missing; cannot verify "
            "Gate A")
    if not lifecycle.is_v2(state):
        # A v1 state is read-only and keeps its own gate mechanism.
        return None
    return state


def gate_a_approved(subject_code: str) -> bool:
    state = load_lifecycle(subject_code)
    return lifecycle.gate_approved(state, "A") if state else False


def gate_b_approved(subject_code: str) -> bool:
    state = load_lifecycle(subject_code)
    return lifecycle.gate_approved(state, "B") if state else False


def gate_c_approved(subject_code: str) -> bool:
    state = load_lifecycle(subject_code)
    return lifecycle.gate_approved(state, "C") if state else False


def require_seed_gate(subject_code: str, seed: int = 1) -> None:
    """Refuse assembly without Gate A, and Gate B for seed 4 and later."""
    state = _require_recycle(subject_code)
    if state is None:
        return
    if not lifecycle.gate_approved(state, "A"):
        raise GateBlocked(
            f"{subject_code}: Gate A (bank approved) is not recorded; seed "
            f"{seed} assembly is blocked")
    if int(seed) >= 4 and not lifecycle.gate_approved(state, "B"):
        raise GateBlocked(
            f"{subject_code}: Gate B (first seeds approved) is not recorded; "
            f"seed {seed} assembly is blocked")
    from src.bank.store import BankStore

    approved = BankStore(bank_root(subject_code)).approved_questions()
    if not approved:
        raise GateBlocked(
            f"{subject_code}: the bank has no approved questions; Gate A "
            "cannot be honoured")


def require_publish_gate(subject_code: str) -> None:
    state = _require_recycle(subject_code)
    if state is None:
        return
    if not lifecycle.gate_approved(state, "C"):
        raise GateBlocked(
            f"{subject_code}: Gate C (publish approved) is not recorded")
