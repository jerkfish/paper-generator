"""Question quality scoring shared by recycle subjects."""
from __future__ import annotations

from src.bank.schema import normalize_text


def quality_score(question: dict,
                  assets: dict[str, dict] | None = None) -> float:
    """Return a 0.0–1.0 completeness score for a bank question."""
    assets = assets or {}
    status = str(question.get("status") or "extracted")
    status_points = {
        "approved": 0.30,
        "extracted": 0.18,
        "needs_fix": 0.05,
        "rejected": 0.0,
    }.get(status, 0.0)

    text = normalize_text(
        (question.get("native_text_blocks") or [{}])[0].get("text", ""))
    text_points = 0.15 if len(text) >= 80 else 0.08 if text else 0.0

    marks = question.get("marks")
    parts = question.get("subpart_marks") or []
    part_total = sum(int(part.get("marks") or 0) for part in parts)
    marks_points = 0.15 if (isinstance(marks, int) and marks > 0
                            and (not parts or part_total == marks)) else 0.0

    hash_points = 0.10 if question.get("content_hash") else 0.0

    refs = [str(ref).lower() for ref in question.get("refs") or []]
    linked = [assets.get(aid) for aid in question.get("assets") or []]
    labels = {str(asset.get("label", "")).lower()
              for asset in linked if asset}
    refs_points = 0.15 if all(ref in labels for ref in refs) else 0.0

    if linked:
        asset_points = 0.15 if all(
            asset and asset.get("verdict") == "approved" for asset in linked
        ) else 0.0
    else:
        asset_points = 0.15

    total = (status_points + text_points + marks_points + hash_points
             + refs_points + asset_points)
    return round(min(1.0, max(0.0, total)), 3)


def quality_band(score: float) -> str:
    if score >= 0.85:
        return "high"
    if score >= 0.60:
        return "medium"
    return "low"
