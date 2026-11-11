"""Duplicate-cluster helpers for recycled question banks.

Exact text normalisation catches the common “same question, new year” cases
without inventing a similarity threshold.  Eras and years are deliberately not
part of the key.
"""
from __future__ import annotations

import hashlib

from src.bank.schema import normalize_text


def duplicate_key(question: dict) -> str:
    blocks = question.get("native_text_blocks") or []
    text = "\n".join(str(block.get("normalised") or block.get("text") or "")
                     for block in blocks if isinstance(block, dict))
    return hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()


def cluster_duplicates(questions: list[dict]) -> list[dict]:
    """Group questions by normalised text.

    Returns one cluster per duplicate key with a canonical id (the first
    approved record, otherwise the first record) and all member ids.
    """
    groups: dict[str, list[dict]] = {}
    for question in questions:
        if not question.get("id"):
            continue
        groups.setdefault(duplicate_key(question), []).append(question)
    clusters = []
    for key, members in sorted(groups.items()):
        ordered = sorted(
            members,
            key=lambda row: (row.get("status") == "approved",
                             str(row.get("source_paper") or ""),
                             str(row.get("id") or "")),
            reverse=True)
        canonical = ordered[0]
        clusters.append({
            "key": key,
            "canonical_id": canonical.get("id"),
            "ids": [str(row.get("id")) for row in ordered],
            "count": len(ordered),
            "source_papers": sorted({str(row.get("source_paper") or "")
                                     for row in ordered}),
        })
    return clusters


def duplicate_map(questions: list[dict]) -> dict[str, str]:
    """Return ``question_id -> canonical_id`` for every duplicate cluster."""
    mapping: dict[str, str] = {}
    for cluster in cluster_duplicates(questions):
        canonical = str(cluster["canonical_id"])
        for qid in cluster["ids"]:
            mapping[qid] = canonical
    return mapping
