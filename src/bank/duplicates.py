"""Duplicate-cluster helpers for recycled question banks.

Exact text normalisation catches the common “same question, new year” cases
without inventing a similarity threshold.  Eras and years are deliberately not
part of the key.
"""
from __future__ import annotations

import hashlib
import re

from src.bank.schema import normalize_text

TOKEN_RE = re.compile(r"[a-z0-9]+")


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


def _token_set(question: dict) -> set[str]:
    text = normalize_text(
        (question.get("native_text_blocks") or [{}])[0].get("text", ""))
    return {token for token in TOKEN_RE.findall(text.lower())
            if len(token) > 2}


def near_duplicate_pairs(questions: list[dict],
                         threshold: float = 0.70) -> list[dict]:
    """Return potential same-question pairs across years.

    This is a review aid only: pairs are reported, never merged.  Exact
    duplicates are handled by :func:`cluster_duplicates`.
    """
    rows = [(str(row.get("id")), _token_set(row)) for row in questions
            if row.get("id")]
    pairs = []
    for index in range(len(rows)):
        left_id, left = rows[index]
        for right_index in range(index + 1, len(rows)):
            right_id, right = rows[right_index]
            if not left or not right:
                continue
            score = len(left & right) / len(left | right)
            if score >= threshold:
                pairs.append({
                    "left": left_id,
                    "right": right_id,
                    "score": round(score, 3),
                })
    return sorted(pairs, key=lambda item: (-item["score"],
                                           item["left"], item["right"]))
