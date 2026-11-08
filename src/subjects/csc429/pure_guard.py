"""Hard guards for Type D seed assembly."""
from __future__ import annotations

import json
from pathlib import Path

from src import config
from src.subjects.csc429 import pure_gate

TRACKING = config.TRACKING_DIR / "csc429"
BANK = TRACKING / "bank"
QUESTIONS = BANK / "questions"
ASSETS = BANK / "assets"
REJECTED = TRACKING / "rejected_registry.json"


def _load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _rejected_hashes() -> set[str]:
    payload = _load(REJECTED, {})
    return set(payload.get("assets", {})) | set(payload.get("files", {}))


def validate_plan(plan: dict) -> None:
    pure_gate.require_gate()
    slots = plan.get("slots") or []
    if len(slots) != 11:
        raise ValueError("seed plan must have 11 slots")
    if sum(int(slot["marks"]) for slot in slots) != 100:
        raise ValueError("seed plan marks must total 100")
    ids = [slot["question_id"] for slot in slots]
    if len(ids) != len(set(ids)):
        raise ValueError("seed plan reuses a question inside one seed")
    rejected = _rejected_hashes()
    for slot in slots:
        question = _load(QUESTIONS / f"{slot['question_id']}.json", {})
        if not question:
            raise ValueError(f"question missing: {slot['question_id']}")
        if question.get("status") != "approved":
            raise ValueError(
                f"question {slot['question_id']} is {question.get('status')}, "
                "not approved")
        if int(question["marks"]) != int(slot["marks"]):
            raise ValueError(f"mark mismatch for {slot['question_id']}")
        if question.get("part") != slot["part"]:
            raise ValueError(f"part mismatch for {slot['question_id']}")
        if question.get("content_hash") != slot.get("content_hash"):
            raise ValueError(f"content hash changed for {slot['question_id']}")
        assets = []
        for aid in question.get("assets") or []:
            asset = _load(ASSETS / f"{aid}.json", {})
            if not asset:
                raise ValueError(f"asset missing: {aid}")
            if asset.get("source_paper") != question.get("source_paper"):
                raise ValueError(
                    f"asset {aid} belongs to {asset.get('source_paper')}, "
                    f"not {question.get('source_paper')}")
            if aid not in (question.get("assets") or []):
                raise ValueError(f"asset {aid} is not linked to its question")
            if asset.get("verdict") != "approved":
                raise ValueError(f"asset {aid} is not approved")
            if asset.get("sha256") in rejected:
                raise ValueError(f"asset {aid} is in the rejected registry")
            assets.append(asset)
        labels = {str(asset.get("label", "")).lower() for asset in assets}
        for ref in question.get("refs") or []:
            if ref.lower() not in labels:
                raise ValueError(
                    f"question {question['id']} has an unresolved reference: {ref}")


def validate_plan_file(path: Path) -> dict:
    plan = _load(path, {})
    validate_plan(plan)
    return plan
