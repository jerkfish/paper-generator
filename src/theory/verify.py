"""Verification of LLM-drafted theory questions.

Rejections implemented here:
  * quote not a verbatim substring of the cited retrieved slide chunk;
  * marking-point count not equal to the question marks (one point per mark);
  * no supporting passage / no retrieved chunk;
  * near-copy of any past question (fuzzy over all 35 papers);
  * command word missing or wrong;
  * dependent (b) does not refer back to (a).
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass

from src.planner.fingerprint_data import load_all_rows
from src.planner.tasks import DEPENDENT_RE
from src.theory.decks import DeckChunk
from src.theory.models import (DraftQuestion, TheoryDraft, VerifiedPoint,
                               VerifiedQuestion)

NEAR_COPY_THRESHOLD = 0.80
MIN_QUOTE_CHARS = 15
MAX_QUESTION_WORDS = 130
_STOP = {
    "a", "an", "the", "of", "to", "in", "on", "for", "and", "or", "with",
    "by", "from", "as", "at", "is", "are", "was", "were", "be", "been",
    "that", "this", "these", "those", "it", "its", "their", "your", "you",
    "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "list", "state", "explain", "describe", "discuss", "compare", "justify",
    "distinct", "specific", "key", "main", "primary", "different", "types",
    "type", "characteristics", "characteristic", "features", "feature",
    "aspects", "aspect", "components", "component", "lecture", "slides",
    "slide", "materials", "described", "presented", "discussed", "using",
    "how", "why", "what", "which", "give", "identify", "name", "briefly",
}


def content_tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", str(text).lower())
            if t not in _STOP and len(t) > 2}


def semantic_duplicate(a: str, b: str) -> tuple[bool, float, float]:
    """Return (is_duplicate, sequence_ratio, content_jaccard)."""
    seq = difflib.SequenceMatcher(
        None, _copy_text(a), _copy_text(b), autojunk=False).ratio()
    ta, tb = content_tokens(a), content_tokens(b)
    jac = (len(ta & tb) / len(ta | tb)) if (ta or tb) else 0.0
    return (seq >= 0.65 and jac >= 0.45), seq, jac


def normalize_text(text: str) -> str:
    text = str(text).replace(" ", " ").replace("’", "'")
    text = text.replace("‘", "'").replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", text).strip()


def _copy_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text)).strip().lower()


@dataclass
class NearCopy:
    ratio: float
    paper: str
    q: str
    text: str


def near_copy(question: str) -> NearCopy:
    target = _copy_text(question)
    best = NearCopy(0.0, "", "", "")
    for row in load_all_rows():
        candidate = _copy_text(row["Original question text"])
        if not candidate:
            continue
        ratio = difflib.SequenceMatcher(
            None, target, candidate, autojunk=False).ratio()
        if ratio > best.ratio:
            best = NearCopy(ratio, str(row["Paper ID"]),
                            f"Q{row['Q no.']}{row['Sub-part'] or ''}",
                            str(row["Original question text"]))
    return best


def _chunk_map(chunks: list[DeckChunk]) -> dict[str, DeckChunk]:
    return {c.chunk_id: c for c in chunks}


def clean_chunk_id(raw: str) -> str:
    """LLMs often wrap the id in [] or copy the evidence header after it."""
    s = str(raw).strip()
    if "[" in s and "]" in s:
        s = s[s.find("[") + 1:s.find("]")].strip()
    if " | " in s:
        s = s.split(" | ", 1)[0].strip()
    return s.strip().strip("[]").strip()


def verify_draft(draft: TheoryDraft, expected_slots: list[dict],
                 chunks: list[DeckChunk],
                 prior: list[dict] | None = None
                 ) -> tuple[list[VerifiedQuestion], list[str]]:
    errors: list[str] = []
    prior = prior or []
    by_id = _chunk_map(chunks)
    if not chunks:
        return [], ["no supporting passage: retrieval returned no chunks"]
    if len(draft.questions) != len(expected_slots):
        errors.append(f"expected {len(expected_slots)} question(s), got "
                      f"{len(draft.questions)}")
    expected_by_slot = {s["slot"]: s for s in expected_slots}
    got_by_slot = {q.slot: q for q in draft.questions}
    if set(got_by_slot) != set(expected_by_slot):
        errors.append(f"slot ids do not match: expected "
                      f"{sorted(expected_by_slot)}, got {sorted(got_by_slot)}")
        return [], errors

    verified: list[VerifiedQuestion] = []
    for slot_id, exp in expected_by_slot.items():
        slot_errors: list[str] = []
        q = got_by_slot[slot_id]
        task = str(exp["task"])
        marks = int(exp["marks"])
        question = q.question.strip()
        if task.lower() not in question.lower():
            slot_errors.append(f"{slot_id}: command word '{task}' missing from "
                               "question")
        required = exp.get("angle_required") or []
        forbidden = exp.get("angle_forbidden") or []
        ql = question.lower()
        if required and not any(k.lower() in ql for k in required):
            slot_errors.append(
                f"{slot_id}: angle hint not followed; include one of "
                f"{required}")
        for k in forbidden:
            if k.lower() in ql:
                slot_errors.append(
                    f"{slot_id}: forbidden angle {k!r} repeats another "
                    "question")
        words = len(question.split())
        if words < 8:
            slot_errors.append(f"{slot_id}: question too short ({words} words)")
        if words > MAX_QUESTION_WORDS:
            slot_errors.append(f"{slot_id}: question too long ({words} words)")
        if exp.get("dependent") and slot_id.endswith("b"):
            if not DEPENDENT_RE.search(question):
                slot_errors.append(
                    f"{slot_id}: dependent (b) does not refer back to (a) / "
                    "the above / the scenario")
        nc = near_copy(question)
        if nc.ratio >= NEAR_COPY_THRESHOLD:
            slot_errors.append(
                f"{slot_id}: near-copy {nc.ratio:.2f} of {nc.paper} {nc.q}; "
                "rephrase the scenario and wording")
        # Cross-generated duplicate check.  The two halves of a dependent pair
        # are allowed to be related, so only compare against earlier groups.
        current_slots = {s["slot"] for s in expected_slots}
        for old in prior:
            if old.get("slot") in current_slots:
                continue
            old_text = str(old.get("question", ""))
            if not old_text:
                continue
            dup, ratio, jac = semantic_duplicate(question, old_text)
            if dup:
                slot_errors.append(
                    f"{slot_id}: near-duplicate (seq {ratio:.2f}, content "
                    f"{jac:.2f}) of accepted {old.get('slot')}: "
                    f"{old_text[:140]!r}; choose a different question angle")
        if len(q.marking_points) != marks:
            slot_errors.append(
                f"{slot_id}: {len(q.marking_points)} marking points for "
                f"{marks} marks (need exactly {marks})")
        points: list[VerifiedPoint] = []
        citations: list[str] = []
        for i, p in enumerate(q.marking_points, 1):
            if "..." in p.quote or "…" in p.quote:
                slot_errors.append(
                    f"{slot_id} point {i}: ellipsis in quote; copy a "
                    "contiguous passage without skipping words")
                continue
            cid = clean_chunk_id(p.chunk_id)
            chunk = by_id.get(cid)
            if chunk is None:
                slot_errors.append(
                    f"{slot_id} point {i}: chunk_id {p.chunk_id!r} was not in "
                    "the retrieved evidence")
                continue
            nq = normalize_text(p.quote)
            nt = normalize_text(chunk.text)
            if len(nq) < MIN_QUOTE_CHARS:
                slot_errors.append(
                    f"{slot_id} point {i}: quote too short to verify")
                continue
            if nq not in nt:
                slot_errors.append(
                    f"{slot_id} point {i}: quote is not verbatim in "
                    f"{chunk.deck} slide {chunk.slide}")
                continue
            source = f"{chunk.deck}, slide {chunk.slide}"
            citations.append(source)
            points.append(VerifiedPoint(
                point=p.point.strip(), marks=1, quote=nq,
                source_file=chunk.deck, source_slide=chunk.slide,
                source_deck=chunk.deck, chunk_id=chunk.chunk_id))
        errors.extend(slot_errors)
        if len(points) == marks and not slot_errors:
            verified.append(VerifiedQuestion(
                slot=slot_id, question=question, marks=marks,
                topic=str(exp["topic"]), task=task,
                marking_points=points, confidence="sourced",
                citations=sorted(set(citations)),
                style_examples=exp.get("style_examples", []),
                style_mode=exp.get("style_mode", ""),
                low_style_confidence=bool(exp.get("low_style_confidence"))))

    # Sibling (a)/(b) checks: non-dependent pairs must not duplicate each
    # other; dependent pairs must build rather than repeat.
    qs = draft.questions
    if len(qs) == 2:
        dup, ratio, jac = semantic_duplicate(qs[0].question, qs[1].question)
        dep = any(s.get("dependent") for s in expected_slots)
        if not dep and dup:
            errors.append(
                f"sibling pair near-duplicate (seq {ratio:.2f}, content "
                f"{jac:.2f}); choose two different aspects of the topic")
        if dep and ratio >= 0.85:
            errors.append(
                f"dependent (b) repeats (a) too closely ({ratio:.2f}); "
                "build on (a) instead of restating it")
    return verified, errors
