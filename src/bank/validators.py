"""Approved-only plan validation for recycled papers."""
from __future__ import annotations

from src.bank.schema import validate_asset, validate_question
from src.bank.store import BankStore, load_json


class GateNotApproved(RuntimeError):
    """Raised when a seed is requested before its bank gate is approved."""


def validate_seed_plan(
    plan: dict,
    store: BankStore,
    *,
    expected_slots: int | None = None,
    expected_marks: int | None = None,
    rejected_hashes: set[str] | None = None,
    require_assets: bool = True,
    require_content_hash: bool = True,
    check_part: bool = True,
) -> None:
    """Validate a seed plan against the bank contract.

    The plan must contain no duplicate question, every question must be
    approved, marks must fit the slot, assets must belong to the question and
    references must resolve to linked asset labels.
    """
    slots = plan.get("slots") or []
    if expected_slots is not None and len(slots) != expected_slots:
        raise ValueError(f"seed plan must have {expected_slots} slots")
    if expected_marks is not None:
        total = sum(int(slot.get("marks") or 0) for slot in slots)
        if total != expected_marks:
            raise ValueError(
                f"seed plan marks must total {expected_marks}")
    ids = [str(slot.get("question_id") or "") for slot in slots]
    if len(ids) != len(set(ids)):
        raise ValueError("seed plan reuses a question inside one seed")
    rejected = set(rejected_hashes or set())

    for slot in slots:
        qid = str(slot.get("question_id") or "")
        question = store.load_question(qid)
        if not question:
            raise ValueError(f"question missing: {qid}")
        if question.get("status") != "approved":
            raise ValueError(
                f"question {qid} is {question.get('status')}, not approved")
        if int(question.get("marks") or 0) != int(slot.get("marks") or 0):
            raise ValueError(f"mark mismatch for {qid}")
        if check_part and slot.get("part") is not None:
            if question.get("part") != slot.get("part"):
                raise ValueError(f"part mismatch for {qid}")
        if require_content_hash:
            expected_hash = question.get("content_hash")
            if not expected_hash:
                raise ValueError(f"content hash missing for {qid}")
            if expected_hash != slot.get("content_hash"):
                raise ValueError(f"content hash changed for {qid}")
        errors = validate_question(question, require_hash=False)
        if errors:
            raise ValueError(f"question {qid}: " + "; ".join(errors))

        linked: list[dict] = []
        for aid in question.get("assets") or []:
            asset = store.load_asset(str(aid))
            if not asset:
                raise ValueError(f"asset missing: {aid}")
            if asset.get("source_paper") != question.get("source_paper"):
                raise ValueError(
                    f"asset {aid} belongs to {asset.get('source_paper')}, "
                    f"not {question.get('source_paper')}")
            if str(aid) not in {str(value) for value in
                                question.get("assets") or []}:
                raise ValueError(f"asset {aid} is not linked to its question")
            if require_assets and asset.get("verdict") != "approved":
                raise ValueError(f"asset {aid} is not approved")
            if asset.get("sha256") in rejected:
                raise ValueError(f"asset {aid} is in the rejected registry")
            errors = validate_asset(asset)
            if errors:
                raise ValueError(f"asset {aid}: " + "; ".join(errors))
            linked.append(asset)

        labels = {str(asset.get("label", "")).lower() for asset in linked}
        for ref in question.get("refs") or []:
            if str(ref).lower() not in labels:
                raise ValueError(
                    f"question {qid} has an unresolved reference: {ref}")


def validate_plan_file(path, store: BankStore, **kwargs) -> dict:
    plan = load_json(path, {})
    validate_seed_plan(plan, store, **kwargs)
    return plan
