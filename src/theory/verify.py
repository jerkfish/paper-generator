"""Verification of LLM-drafted theory questions.

Rejections implemented here:
  * quote not a verbatim substring of the cited retrieved slide chunk;
  * quote is only a slide title, or too short to be a full supporting passage;
  * marking-point count not equal to the question marks (one point per mark);
  * no supporting passage / no retrieved chunk;
  * near-copy of any past question (fuzzy over all 35 papers);
  * near-duplicate of another generated question;
  * source overlap: the same (deck, slide) cited by another question;
  * source deck outside the slot topic's allowed deck map;
  * command word missing or wrong;
  * dependent (b) does not refer back to (a);
  * Part B scenario missing/ungrounded.

Low term-overlap between a marking point and its quote is recorded for human
review rather than silently accepted as strong evidence.
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from functools import lru_cache

import snowballstemmer

from src.planner.fingerprint_data import load_all_rows
from src.planner.tasks import DEPENDENT_RE
from src.theory.bm25 import TOPIC_DECKS
from src.theory.decks import DeckChunk
from src.theory.models import (LECTURE_LABEL, DraftQuestion, TheoryDraft,
                               VerifiedPoint, VerifiedQuestion)

NEAR_COPY_THRESHOLD = 0.80
MIN_QUOTE_CHARS = 8
MIN_QUOTE_WORDS = 2
MAX_QUESTION_WORDS = 130
MIN_SCENARIO_WORDS = 15
MAX_SCENARIO_WORDS = 100
MIN_SCENARIO_GROUNDING = 0.20
_STOP = {
    "a", "an", "the", "of", "to", "in", "on", "for", "and", "or", "with",
    "by", "from", "as", "at", "is", "are", "was", "were", "be", "been",
    "that", "this", "these", "those", "it", "its", "their", "your", "you",
    "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "list", "state", "explain", "describe", "discuss", "compare", "justify",
    "propose", "analyse", "analyze", "distinct", "specific", "key", "main",
    "primary", "different", "types", "type", "characteristics",
    "characteristic", "features", "feature", "aspects", "aspect",
    "components", "component", "lecture", "slides", "slide", "materials",
    "described", "presented", "discussed", "using", "how", "why", "what",
    "which", "give", "identify", "name", "briefly", "one", "each",
}


def normalize_text(text: str) -> str:
    text = str(text).replace(" ", " ").replace("’", "'")
    text = text.replace("‘", "'").replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", text).strip()


def _copy_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text)).strip().lower()


def content_tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", str(text).lower())
            if t not in _STOP and len(t) > 2}


_STEMMER = snowballstemmer.stemmer("english")


@lru_cache(maxsize=50_000)
def stem_token(token: str) -> str:
    """Snowball English stemmer; used as a light lemmatiser."""
    return _STEMMER.stemWord(token)


_STOP_STEMS = {stem_token(t) for t in _STOP}


def stemmed_content_tokens(text: str) -> set[str]:
    # Filter stopword stems too, so "identify" and "identifying" are treated
    # consistently even though only one surface form is in _STOP.
    return {s for s in (stem_token(t) for t in content_tokens(text))
            if s not in _STOP_STEMS}


def stem_overlap(point: str, quote: str) -> float:
    """Share of the point's stemmed content tokens present in the quote."""
    pt = stemmed_content_tokens(point)
    if not pt:
        return 1.0
    return len(pt & stemmed_content_tokens(quote)) / len(pt)


def is_verbatim_copy(point: str, quote: str) -> bool:
    """True when the marking point is just the quote (or a long slice of it).

    Copying the slide sentence into the point is not a marking point: it adds
    no answer guidance and rewards verbatim reproduction rather than
    understanding.  Short overlaps are allowed because technical terms are
    expected to recur.
    """
    p = re.sub(r"\s+", " ", str(point).lower()).strip(" .;:,")
    q = re.sub(r"\s+", " ", str(quote).lower()).strip(" .;:,")
    if not p or not q:
        return False
    if p == q:
        return True
    if len(p) >= 30 and p in q:
        return True
    if len(q) >= 40 and q in p:
        return True
    return False


def semantic_duplicate(a: str, b: str) -> tuple[bool, float, float]:
    """Return (is_duplicate, sequence_ratio, content_jaccard)."""
    seq = difflib.SequenceMatcher(
        None, _copy_text(a), _copy_text(b), autojunk=False).ratio()
    ta, tb = content_tokens(a), content_tokens(b)
    jac = (len(ta & tb) / len(ta | tb)) if (ta or tb) else 0.0
    return (seq >= 0.65 and jac >= 0.45), seq, jac


@dataclass
class NearCopy:
    ratio: float
    paper: str
    q: str
    text: str


@lru_cache(maxsize=1)
def _corpus() -> list[dict]:
    rows = []
    for row in load_all_rows():
        text = str(row["Original question text"])
        norm = _copy_text(text)
        if not norm:
            continue
        rows.append({
            "paper": str(row["Paper ID"]),
            "q": f"Q{row['Q no.']}{row['Sub-part'] or ''}",
            "text": text,
            "norm": norm,
            "tokens": content_tokens(text),
        })
    return rows


@lru_cache(maxsize=5000)
def near_copy(question: str) -> NearCopy:
    target = _copy_text(question)
    target_tokens = content_tokens(question)
    # Cheap token prefilter: exact high-sequence matches almost always rank
    # near the top by content-token Jaccard.  Compare only the best 60.
    scored = []
    for row in _corpus():
        a, b = target_tokens, row["tokens"]
        union = len(a | b)
        jac = len(a & b) / union if union else 0.0
        scored.append((jac, row))
    scored.sort(key=lambda x: -x[0])
    best = NearCopy(0.0, "", "", "")
    for _, row in scored[:60]:
        ratio = difflib.SequenceMatcher(
            None, target, row["norm"], autojunk=False).ratio()
        if ratio > best.ratio:
            best = NearCopy(ratio, row["paper"], row["q"], row["text"])
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


def source_key(chunk: DeckChunk) -> str:
    return f"{chunk.deck}::s{chunk.slide}"


def _slide_title(chunk: DeckChunk) -> str:
    for line in str(chunk.text).splitlines():
        line = normalize_text(line)
        if line:
            return line
    return ""


def quote_is_only_title(quote: str, chunk: DeckChunk) -> bool:
    q = normalize_text(quote)
    title = _slide_title(chunk)
    if not q or not title:
        return False
    if q == title:
        return True
    if q in title and len(q) >= max(3, int(len(title) * 0.6)):
        return True
    return False


def _repair_quote(quote: str, chunk: DeckChunk, point: str = "") -> str:
    """Find the closest exact sentence/line when the model paraphrased.

    This never invents text: the returned string is copied from the chunk.
    Only a very close match (>=0.86) is accepted.
    """
    q = normalize_text(quote)
    text = str(chunk.text)
    candidates: list[str] = []
    for line in text.splitlines():
        line = normalize_text(line)
        if line:
            candidates.append(line)
    for sent in re.split(r"(?<=[.!?])\s+", normalize_text(text)):
        sent = sent.strip()
        if sent and sent not in candidates:
            candidates.append(sent)
    best = ""
    best_ratio = 0.0
    for cand in candidates:
        ratio = difflib.SequenceMatcher(
            None, q.lower(), cand.lower(), autojunk=False).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best = cand
    if best_ratio >= 0.86 and not quote_is_only_title(best, chunk):
        return best
    # If the model joined several neighbouring lines, accept one complete
    # line that is present in the quote and shares a key term with the point.
    if point:
        qwords = q.lower()
        line_hits = []
        for cand in candidates:
            if cand.lower() in qwords and stem_overlap(point, cand) > 0:
                if not quote_is_only_title(cand, chunk):
                    line_hits.append(cand)
        if line_hits:
            return max(line_hits, key=len)
    return ""


def term_overlap(point: str, quote: str) -> float:
    pt = content_tokens(point)
    if not pt:
        return 1.0
    return len(pt & content_tokens(quote)) / len(pt)


def _topic_decks_ok(topic: str, deck: str) -> bool:
    allowed = TOPIC_DECKS.get(topic)
    if not allowed:
        return True
    return deck.startswith(allowed)


def verify_draft(draft: TheoryDraft, expected_slots: list[dict],
                 chunks: list[DeckChunk],
                 prior: list[dict] | None = None,
                 used_sources: set[tuple[str, int]] | None = None,
                 allow_overlap: bool = False,
                 scenario_required: bool = False,
                 shared_scenario: str = "",
                 slot_chunk_ids: dict[str, set[str]] | None = None,
                 near_copy_threshold: float = NEAR_COPY_THRESHOLD,
                 stem_overlap_threshold: float = 0.5
                 ) -> tuple[list[VerifiedQuestion], list[str]]:
    errors: list[str] = []
    prior = prior or []
    used_sources = used_sources or set()
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

    # (deck, slide) -> slots citing it in this draft
    draft_sources: dict[tuple[str, int], set[str]] = {}
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
        sub_req = exp.get("subangle_required") or []
        if sub_req and not any(k.lower() in ql for k in sub_req):
            slot_errors.append(
                f"{slot_id}: sub-angle not followed; use one of {sub_req}")
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
        if nc.ratio >= near_copy_threshold:
            slot_errors.append(
                f"{slot_id}: near-copy {nc.ratio:.2f} of {nc.paper} {nc.q}; "
                "rephrase the scenario and wording")
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
        slot_sources: list[str] = []
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
            if slot_chunk_ids is not None and cid not in slot_chunk_ids.get(
                    slot_id, set()):
                slot_errors.append(
                    f"{slot_id} point {i}: chunk_id {p.chunk_id!r} belongs to "
                    "the other slot's evidence pool")
                continue
            if not _topic_decks_ok(str(exp["topic"]), chunk.deck):
                slot_errors.append(
                    f"{slot_id} point {i}: cited deck {chunk.deck!r} is "
                    f"outside the allowed decks for topic {exp['topic']!r}")
                continue
            if quote_is_only_title(p.quote, chunk):
                slot_errors.append(
                    f"{slot_id} point {i}: quote is a slide title/short "
                    "heading, not a supporting passage")
                continue
            nq = normalize_text(p.quote)
            nt = normalize_text(chunk.text)
            if len(nq) < MIN_QUOTE_CHARS or len(nq.split()) < MIN_QUOTE_WORDS:
                slot_errors.append(
                    f"{slot_id} point {i}: quote too short to verify "
                    f"({len(nq.split())} words); prefer a full sentence")
                continue
            repaired = False
            if nq not in nt:
                fixed = _repair_quote(nq, chunk, p.point)
                if fixed:
                    nq = normalize_text(fixed)
                    repaired = True
            if nq not in nt:
                slot_errors.append(
                    f"{slot_id} point {i}: quote is not verbatim in "
                    f"{chunk.deck} slide {chunk.slide}")
                continue
            key = (chunk.deck, chunk.slide)
            overlap_hit = False
            if key in used_sources:
                overlap_hit = True
            if key in draft_sources and slot_id not in draft_sources[key]:
                overlap_hit = True
            if overlap_hit:
                if not allow_overlap:
                    slot_errors.append(
                        f"{slot_id} point {i}: source overlap "
                        f"({chunk.deck} slide {chunk.slide}) with another "
                        "question; use an unused slide")
                    continue
            draft_sources.setdefault(key, set()).add(slot_id)
            slot_sources.append(f"{chunk.deck}::s{chunk.slide}")
            if is_verbatim_copy(p.point, nq):
                slot_errors.append(
                    f"{slot_id} point {i}: marking point is a verbatim copy "
                    "of its quote; phrase the point as an answer requirement, "
                    "not as copied slide text")
                continue
            raw_overlap = term_overlap(p.point, nq)
            tover = stem_overlap(p.point, nq)
            source = f"{chunk.deck}, slide {chunk.slide}"
            citations.append(source)
            points.append(VerifiedPoint(
                point=p.point.strip(), marks=1, quote=nq,
                source_file=chunk.deck, source_slide=chunk.slide,
                source_deck=chunk.deck, chunk_id=chunk.chunk_id,
                source_key=f"{chunk.deck}::s{chunk.slide}",
                term_overlap=round(raw_overlap, 3),
                low_term_overlap=tover < stem_overlap_threshold,
                stem_overlap=round(tover, 3),
                low_stem_overlap=tover < stem_overlap_threshold,
                short_quote=len(nq.split()) < 5,
                quote_repaired=repaired))
        errors.extend(slot_errors)
        if len(points) == marks and not slot_errors:
            verified.append(VerifiedQuestion(
                slot=slot_id, question=question, marks=marks,
                topic=str(exp["topic"]), task=task,
                marking_points=points, confidence=LECTURE_LABEL,
                citations=sorted(set(citations)),
                source_keys=sorted(set(slot_sources)),
                style_examples=exp.get("style_examples", []),
                style_mode=exp.get("style_mode", ""),
                low_style_confidence=bool(exp.get("low_style_confidence")),
                overlap_allowed=allow_overlap))

    # Part B scenario: one shared, grounded scenario for B1a/B1b (and B2a/B2b).
    scenario = normalize_text(draft.scenario)
    if scenario_required:
        sw = len(scenario.split())
        if not scenario:
            errors.append("Part B scenario missing")
        elif not (MIN_SCENARIO_WORDS <= sw <= MAX_SCENARIO_WORDS):
            errors.append(
                f"Part B scenario length {sw} words; need "
                f"{MIN_SCENARIO_WORDS}-{MAX_SCENARIO_WORDS}")
        else:
            ev = set()
            for c in chunks:
                ev |= content_tokens(c.text)
            st = content_tokens(scenario)
            grounding = (len(st & ev) / len(st)) if st else 0.0
            if grounding < MIN_SCENARIO_GROUNDING:
                errors.append(
                    f"Part B scenario is not grounded in the evidence "
                    f"(term coverage {grounding:.2f})")
            scenario_terms = content_tokens(scenario)
            for q in draft.questions:
                ql = q.question.lower()
                refers = bool(re.search(r"\b(scenario|above|case|situation)\b",
                                        ql))
                refers = refers or any(t in ql for t in scenario_terms)
                if not refers:
                    errors.append(
                        f"{q.slot}: Part B question must refer to the shared "
                        "scenario")
            for v in verified:
                v.scenario = scenario
                v.scenario_grounding = round(grounding, 3)
    elif shared_scenario:
        shared = normalize_text(shared_scenario)
        st = content_tokens(shared)
        for q in draft.questions:
            ql = q.question.lower()
            refers = bool(re.search(r"\b(scenario|above|case|situation)\b",
                                    ql))
            refers = refers or any(t in ql for t in st)
            if not refers:
                errors.append(
                    f"{q.slot}: Part B question must refer to the shared "
                    "scenario")
        for v in verified:
            v.scenario = shared
            v.scenario_grounding = 1.0

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
