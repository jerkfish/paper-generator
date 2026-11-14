"""Subject-agnostic question-bank schema helpers.

A bank record describes one real past-paper question.  The shared schema keeps
the fields the assembler and review workflow need, without assuming a subject's
mark structure.  Subject-specific extraction may add fields; validators only
check the shared contract.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

QUESTION_STATUSES = {"extracted", "needs_fix", "approved", "rejected"}
ASSET_KINDS = {
    "picture", "figure", "diagram", "table", "equation", "page_crop",
}
ANSWER_PROVENANCE = {
    "official", "solver_verified", "model_unofficial", "human_checked",
}
_WS_RE = re.compile(r"\s+")


def normalize_text(value: Any) -> str:
    """Collapse whitespace for hashing and duplicate detection."""
    return _WS_RE.sub(" ", str(value or "")).strip()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def question_content_hash(question: dict) -> str:
    """Stable hash of the fields that determine a question's identity.

    Asset identities are included when the bank records their SHA-256 values.
    Re-extracting the same question must not change this hash; cosmetic fields
    such as status, review flags and quality score are deliberately excluded.
    """
    blocks = question.get("native_text_blocks") or []
    text = "\n".join(str(block.get("normalised") or block.get("text") or "")
                     for block in blocks if isinstance(block, dict))
    payload = {
        "text": normalize_text(text),
        "marks": question.get("marks"),
        "subpart_marks": [
            {"label": part.get("label"),
             "marks": part.get("marks")}
            for part in question.get("subpart_marks") or []
        ],
        "refs": sorted(str(ref) for ref in question.get("refs") or []),
        "asset_ids": sorted(str(value) for value in question.get("assets") or []),
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return sha256_bytes(blob.encode("utf-8"))


def _subpart_marks(question: dict) -> list[dict]:
    return [part for part in question.get("subpart_marks") or []
            if isinstance(part, dict)]


def validate_question(question: dict, *, require_hash: bool = False) -> list[str]:
    """Return contract errors for one question record."""
    errors: list[str] = []
    if not question.get("id"):
        errors.append("question id is missing")
    if not question.get("source_paper"):
        errors.append("source_paper is missing")
    status = str(question.get("status") or "")
    if status not in QUESTION_STATUSES:
        errors.append(f"invalid question status: {status!r}")
    marks = question.get("marks")
    if not isinstance(marks, int) or marks <= 0:
        errors.append("marks must be a positive integer")
    parts = _subpart_marks(question)
    if parts:
        total = sum(int(part.get("marks") or 0) for part in parts)
        if total != marks:
            errors.append(
                f"subpart marks {total} do not match question marks {marks}")
    if not normalize_text(
            (question.get("native_text_blocks") or [{}])[0].get("text", "")):
        errors.append("native question text is empty")
    if require_hash:
        expected = question.get("content_hash")
        if not expected:
            errors.append("content_hash is missing")
        elif expected != question_content_hash(question):
            errors.append("content_hash does not match the question content")
    return errors


def validate_asset(asset: dict) -> list[str]:
    errors: list[str] = []
    if not asset.get("id"):
        errors.append("asset id is missing")
    if str(asset.get("kind") or "") not in ASSET_KINDS:
        errors.append(f"invalid asset kind: {asset.get('kind')!r}")
    if not asset.get("source_paper"):
        errors.append("asset source_paper is missing")
    if str(asset.get("verdict") or "") not in {"pending", "approved", "rejected"}:
        errors.append(f"invalid asset verdict: {asset.get('verdict')!r}")
    return errors


def validate_answer(answer: dict) -> list[str]:
    errors: list[str] = []
    if not answer.get("question_id"):
        errors.append("answer question_id is missing")
    if not str(answer.get("answer") or "").strip():
        errors.append("answer text is empty")
    if str(answer.get("provenance") or "") not in ANSWER_PROVENANCE:
        errors.append(
            f"invalid answer provenance: {answer.get('provenance')!r}")
    return errors
