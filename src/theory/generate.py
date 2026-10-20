"""Generate theory questions from lecture decks with BM25 + verifier.

Run:
  uv run python -m src.theory.generate --plan outputs/planner_revised_realistic.json
"""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path

from pydantic import ValidationError

from src import config
from src.llm import Usage, chat_json_result
from src.planner.fingerprint_data import load_modern_stats
from src.theory.bm25 import (BM25Index, Hit, TOPIC_DECKS, deck_topic,
                             topic_query)
from src.theory.decks import DeckChunk, coverage, load_chunks
from src.theory.models import (DraftQuestion, Placeholder, TheoryDraft,
                               VerifiedPoint, VerifiedQuestion)
from src.planner.tasks import DEPENDENT_RE
from src.theory.verify import (clean_chunk_id, is_verbatim_copy, near_copy,
                               normalize_text, quote_is_only_title,
                               source_key, stem_overlap, term_overlap,
                               verify_draft)

MAX_ATTEMPTS = 4  # initial + up to 3 retries


TOPIC_SUBANGLES = {
    "attacks/malware": [
        "malware types and characteristics",
        "malware attack techniques and propagation",
        "impacts on confidentiality, integrity and availability",
        "malware case study (Samy worm / XSS)",
        "attack detection and defence",
        "threat classes and countermeasures",
    ],
    "authentication/biometrics": [
        "biometric identification and authentication stages",
        "biometric mechanisms and technologies",
        "password security controls",
        "Kerberos, smartcards and SSO mechanisms",
    ],
    "access control models": [
        "formal security models (BLP, Biba, Chinese Wall)",
        "ACL, ACM and capability structures",
        "authorization goals and reference monitors",
    ],
    "risk/management (ethics)": [
        "morals, ethics and laws",
        "professional code of ethics and conduct",
        "ethical impacts of technology",
        "privacy and organizational responsibility",
    ],
    "software/OS security": [
        "software insecurity and buffer overflows",
        "Windows security mechanisms",
        "Linux/UNIX security",
    ],
    "network security": [
        "NIDS architecture and sensor placement",
        "preventive network mechanisms (firewalls/VPN)",
        "network attacks and detection",
    ],
    "trusted computing/blockchain": [
        "TPM and chain of trust",
        "NGSCB/Nexus components",
        "blockchain and cryptocurrency",
    ],
    "classical ciphers": [
        "substitution ciphers",
        "transposition ciphers",
        "cipher properties and cryptanalysis",
    ],
}

SUBANGLE_KEYWORDS = {
    "malware types and characteristics": ["malware", "type", "characteristic",
                                          "trojan", "worm", "virus", "spyware",
                                          "ransomware", "rootkit", "adware"],
    "malware attack techniques and propagation": ["technique", "propagat",
                                                  "spread", "mechanism",
                                                  "replicat", "infect"],
    "impacts on confidentiality, integrity and availability": [
        "confidentiality", "integrity", "availability", "impact", "harm",
        "damage",
    ],
    "threat classes and countermeasures": ["threat", "class", "countermeasure",
                                           "defence", "defense", "control",
                                           "service"],
    "attack detection and defence": ["detect", "defence", "defense",
                                     "monitor", "prevent", "mitigat"],
    "malware case study (Samy worm / XSS)": [
        "samy", "worm", "case", "example", "javascript", "xss",
        "incident", "malware",
    ],
    "biometric identification and authentication stages": ["biometric",
                                                            "identification",
                                                            "authentication",
                                                            "fingerprint", "iris",
                                                            "stage"],
    "biometric mechanisms and technologies": ["biometric", "fingerprint",
                                               "iris", "mechanism",
                                               "technology", "scan"],
    "password security controls": ["password", "control", "hash", "lockout",
                                   "salt", "authentication"],
    "Kerberos, smartcards and SSO mechanisms": ["kerberos", "smartcard",
                                                "smart card", "sso",
                                                "single sign-on", "ticket",
                                                "token"],
    "formal security models (BLP, Biba, Chinese Wall)": ["model", "bell",
                                                        "biba", "chinese",
                                                        "formal", "security"],
    "ACL, ACM and capability structures": ["acl", "acm", "capability",
                                           "access control list",
                                           "matrix"],
    "authorization goals and reference monitors": ["authorization", "goal",
                                                   "reference monitor",
                                                   "access"],
    "morals, ethics and laws": ["moral", "ethic", "law"],
    "professional code of ethics and conduct": ["code", "professional",
                                                "conduct", "acm"],
    "ethical impacts of technology": ["ethic", "impact", "harm", "privacy",
                                      "society"],
    "privacy and organizational responsibility": ["privacy", "organization",
                                                  "organisation",
                                                  "responsibility", "conduct"],
    "software insecurity and buffer overflows": ["software", "insecurity",
                                                 "buffer", "overflow"],
    "Windows security mechanisms": ["windows", "security", "mechanism"],
    "Linux/UNIX security": ["linux", "unix", "security"],
    "NIDS architecture and sensor placement": ["nids", "sensor",
                                               "architecture", "placement",
                                               "ids"],
    "preventive network mechanisms (firewalls/VPN)": ["firewall", "vpn",
                                                      "preventive", "network",
                                                      "proxy"],
    "network attacks and detection": ["attack", "detect", "network",
                                      "intrusion", "monitor"],
    "TPM and chain of trust": ["tpm", "chain", "trust", "platform"],
    "NGSCB/Nexus components": ["ngscb", "nexus", "nca", "component"],
    "blockchain and cryptocurrency": ["blockchain", "cryptocurrency",
                                      "bitcoin", "ledger", "smart contract"],
    "substitution ciphers": ["substitution", "caesar", "playfair",
                             "monoalphabetic"],
    "transposition ciphers": ["transposition", "columnar", "rail",
                              "fence"],
    "cipher properties and cryptanalysis": ["cipher", "cryptanalysis",
                                            "frequency", "key", "security"],
}

TOPIC_ANGLE_HINTS = {
    "network security": "NIDS architecture, sensor placement, packet "
                        "analysis, evidence preservation, firewalls/VPN and "
                        "network security mechanisms.",
    "classical ciphers": "classical cipher families, substitution, "
                         "transposition, Vigenere, columnar and rail fence.",
    "software/OS security": "software insecurity, buffer overflows, Windows/"
                            "Linux security and mitigation techniques.",
    "attacks/malware": "malware types, threat classes, attack techniques and "
                       "their impacts; avoid authentication controls and "
                       "biometrics unless the evidence is attack-specific.",
    "authentication/biometrics": "passwords, password security controls, "
                                 "biometrics, smartcards, Kerberos and SSO; "
                                 "use a different aspect from the sibling "
                                 "question.",
    "access control models": "formal access-control models, ACL/ACM, "
                             "capabilities, Chinese Wall, BLP and Biba.",
    "trusted computing/blockchain": "TPM, chain of trust, NGSCB/Nexus, "
                                    "blockchain and cryptocurrency.",
    "risk/management (ethics)": "morals, ethics, laws, ACM code, privacy, "
                                "professional conduct and ethical impacts of "
                                "technology.",
}


@dataclass
class GroupResult:
    question: str
    slots: list[str]
    topic: str
    tasks: list[str]
    dependent: bool
    attempts: int = 0  # max draft attempts for any slot in the group (<=4)
    total_draft_attempts: int = 0
    point_retry_calls: int = 0  # entailment + point regeneration calls
    entailment_calls: int = 0
    point_regeneration_calls: int = 0
    initial_entailment_counts: dict = field(default_factory=dict)
    scenario_sampled: bool = False
    accepted: bool = False
    errors: list[list[str]] = field(default_factory=list)
    retrieved: list[dict] = field(default_factory=list)
    fallback_retrieval: bool = False
    overlap_allowed: bool = False
    last_draft: dict = field(default_factory=dict)
    usage: dict = field(default_factory=dict)


def _theory_slots(plan: dict) -> list[dict]:
    return [s for s in plan["slots"] if s["kind"] == "theory"]


def _groups(slots: list[dict]) -> list[list[dict]]:
    by_q: dict[str, list[dict]] = defaultdict(list)
    order: list[str] = []
    for s in slots:
        if s["question"] not in by_q:
            order.append(s["question"])
        by_q[s["question"]].append(s)
    groups: list[list[dict]] = []
    for q in order:
        qslots = by_q[q]
        if len(qslots) > 1:
            # (a)/(b) share a topic.  Generate them together so the pair has
            # distinct angles; dependent pairs additionally make (b) build on
            # (a).
            groups.append(qslots)
        else:
            groups.append(qslots)
    return groups


def _body_chars(chunk) -> int:
    lines = [ln.strip() for ln in str(chunk.text).splitlines() if ln.strip()]
    if not lines:
        return 0
    return len(" ".join(lines[1:]))


def _retrieve_for_slot(index: BM25Index, slot: dict, topic: str,
                       used_sources: set[tuple[str, int]],
                       subangle: str = "") -> tuple[list, bool, bool]:
    """Retrieve evidence for one slot, excluding already-used slides."""
    extra_parts = [str(slot["task"]), TOPIC_ANGLE_HINTS.get(topic, ""), subangle]
    for ex in slot.get("style_examples", [])[:2]:
        extra_parts.append(str(ex.get("text", ""))[:220])
    query = topic_query(topic, " ".join(extra_parts))
    allowed = TOPIC_DECKS.get(topic)
    hits = index.search(query, k=30, max_per_deck=6,
                        allowed_prefixes=allowed)
    fallback = False
    if len(hits) < 3:
        fallback = True
        hits = index.search(query, k=30, max_per_deck=6)
    body = [h for h in hits if _body_chars(h.chunk) >= 80]
    if len(body) >= 3:
        hits = body
    fresh = [h for h in hits
             if (h.chunk.deck, h.chunk.slide) not in used_sources]
    if len(fresh) < 3 and allowed:
        # Small decks (notably 071 Ethics) can produce fewer than three BM25
        # hits.  Fill from unused chunks in the allowed decks before allowing
        # any source overlap.
        have = {h.chunk.chunk_id for h in fresh}
        for c in index.chunks:
            if not c.deck.startswith(allowed):
                continue
            if (c.deck, c.slide) in used_sources or c.chunk_id in have:
                continue
            fresh.append(Hit(0.0, c))
            have.add(c.chunk_id)
            if len(fresh) >= 3:
                break
    overlap_allowed = False
    if len(fresh) >= 3:
        hits = fresh
    else:
        overlap_allowed = True
    return hits, fallback, overlap_allowed


def _retrieve_for_group(index: BM25Index, group: list[dict],
                        used_sources: set[tuple[str, int]]
                        ) -> tuple[dict[str, list], list, bool, bool]:
    """Retrieve, giving each slot in a pair its own disjoint slide pool.

    Slot (a) reserves its slides first; slot (b) then retrieves fresh slides.
    If (b) has fewer than three fresh chunks, it falls back to overlapping
    evidence and the caller records that case.
    """
    topic = group[0]["topic"]
    evidence: dict[str, list] = {}
    all_hits: list = []
    seen_chunks: set[str] = set()
    reserved = set(used_sources)
    fallback = False
    overlap_allowed = False
    # Give the higher-mark slot first choice of slides (e.g. 6-mark (b)
    # before 2-mark (a)); the lower-mark slot then uses fresh alternatives.
    ordered = sorted(group, key=lambda s: (-int(s["marks"]),
                                           group.index(s)))
    for slot in ordered:
        hits, fb, ov = _retrieve_for_slot(index, slot, topic, reserved)
        fallback = fallback or fb
        overlap_allowed = overlap_allowed or ov
        evidence[slot["slot"]] = hits
        for h in hits:
            if h.chunk.chunk_id not in seen_chunks:
                all_hits.append(h)
                seen_chunks.add(h.chunk.chunk_id)
            reserved.add((h.chunk.deck, h.chunk.slide))
    return evidence, all_hits, fallback, overlap_allowed


def _style_examples(group: list[dict], limit: int = 5) -> list[dict]:
    out: list[dict] = []
    seen = set()
    for s in group:
        for ex in s.get("style_examples", []):
            key = (ex.get("paper"), ex.get("q"))
            if key in seen:
                continue
            seen.add(key)
            out.append(ex)
            if len(out) >= limit:
                return out
    return out


def _prompt(group: list[dict], evidence: dict[str, list],
            errors: list[str] | None, sibling_text: str = "",
            shared_scenario: str = "", dependent: bool = False,
            scenario_required: bool = False,
            same_topic_questions: list[str] | None = None,
            subangle: str = "") -> str:
    topic = group[0]["topic"]
    specs = []
    for s in group:
        specs.append({
            "slot": s["slot"],
            "marks": s["marks"],
            "topic": s["topic"],
            "command": s["task"],
            "part": s["part"],
            "dependent": bool(s.get("dependent")),
            "dependent_on": s.get("dependent_on", ""),
            "angle_hint": TOPIC_ANGLE_HINTS.get(s["topic"], ""),
            "sub_angle": subangle,
        })
    examples = _style_examples(group)
    example_text = "\n".join(
        f"- {e['paper']} {e['q']} ({e['marks']} marks): {e['text']}"
        for e in examples) or "(none available)"
    evidence_text = ""
    for s in group:
        ev = evidence.get(s["slot"], [])
        evidence_text += (
            f"\nEVIDENCE FOR {s['slot']} (use only these chunk ids)\n"
            + "\n\n".join(
                f"[{h.chunk.chunk_id}] {h.chunk.deck} | slide "
                f"{h.chunk.slide}\n{h.chunk.text}" for h in ev)
            + "\n")
    angle = TOPIC_ANGLE_HINTS.get(topic, "")
    pair = len(group) > 1
    scenario_rule = ""
    if scenario_required:
        scenario_rule = (
            "\nPART B SCENARIO: write one short scenario of 20-70 words that "
            "is grounded only in the evidence. Put it in the top-level "
            "\"scenario\" field; do not put marks, numbering, or questions in "
            "it. Do not introduce facts that are not in the evidence. The "
            "sibling question will reuse this scenario.\n")
    elif shared_scenario:
        scenario_rule = (
            "\nSHARED PART B SCENARIO (already written by (a)):\n"
            f"{shared_scenario}\n"
            "Your question must refer to this scenario (use 'the scenario' or "
            "a term from it). Leave the output \"scenario\" field empty.\n")
    if dependent:
        pair_rule = (
            "\nDEPENDENT (b): this question follows (a). Begin with 'Refer to "
            "your answer in (a)' or 'Based on the scenario in (a)' and build "
            "on (a); do not merely repeat it.\n")
    elif sibling_text:
        pair_rule = (
            "\nSIBLING CONTEXT: the earlier question in the same paper is:\n"
            f"{sibling_text}\n"
            "Do not duplicate its angle or marking points; choose a different "
            "aspect of the topic.\n")
    elif pair:
        pair_rule = (
            "\nSIBLING PAIR: both questions share one topic but must test "
            "different aspects. Do not duplicate each other's question angle "
            "or marking points; the verifier rejects a near-duplicate pair. "
            "Each question has its own mark count and points.\n")
    else:
        pair_rule = ""
    same_topic_text = "\n".join(
        f"- {q[:240]}" for q in (same_topic_questions or [])[-5:])
    retry = ""
    if errors:
        retry = (
            "\nPREVIOUS ATTEMPT FAILED. Fix every listed error and return a "
            "new draft; do not reuse the same question wording:\n"
            + "\n".join(f"- {e}" for e in errors) + "\n")
    schema = {
        "scenario": "shared Part B scenario (empty for Part A)",
        "questions": [{
            "slot": "A1a",
            "question": "Explain ...",
            "marking_points": [{
                "point": "one mark point",
                "quote": "verbatim contiguous text from the cited chunk",
                "chunk_id": "exact chunk id from the evidence list",
            }],
        }],
    }
    schema = json.dumps(schema, indent=2)
    return f"""Draft original CSC662 Computer Security exam questions.

SLOTS
{json.dumps(specs, indent=2)}

ANGLE HINT (follow this; it prevents repeating another question)
{angle or '(none)'}

SUB-ANGLE FOR THIS SLOT (must be the focus)
{subangle or '(none)'}

RULES
- Use ONLY the lecture evidence below. Do not use outside facts.
- Do NOT duplicate any already accepted question on this topic:
{same_topic_text or '(none yet)'}
- The question must start with the specified command word ({', '.join(s['task'] for s in group)}) and be answerable from the evidence.
- One marking point per mark: exactly the number of points shown in "marks". Each point is worth 1 mark. Phrase the question so it naturally requires that many distinct points (e.g. "Describe six ..." for 6 marks); do not ask for only two items and then pad.
- Every marking point must cite one chunk_id from the evidence list and include a quote copied character-for-character from that chunk. The quote must be a contiguous passage of at least 25 characters and 5 words (a full clause or sentence, not a slide title, single word, or bare heading); no ellipses (never write "..." or "…"), no paraphrase, no line-break changes.
- The point must be an answer requirement in your own words, not a copy of
  the quote; a point that is a verbatim copy of its quote is rejected.
- Prefer quotes that clearly entail the point; the verifier uses stemmed
  content-term overlap as the first gate.
- If a bullet is only a heading (for example "Operating System Independence"), do not use it as a quote; either find a full sentence elsewhere on the slide or omit that point and use another evidence bullet.
- Do not split one fact into several points. For 5/6-mark questions, use at least two different slides and give distinct, non-overlapping points.
- No (deck, slide) may be cited by both questions in a pair: question (a) and question (b) must use different slides. Earlier paper questions have already reserved some slides; the evidence list is filtered, so do not reuse one slide for both parts.
- The question and marking points must stay on the slot topic and its allowed decks.
- Do NOT copy a style example or any past paper question. Use the style examples only for length and tone. Change the scenario and wording.
- Do not repeat a question angle already used in the paper; the verifier rejects near-duplicates of accepted slots.
- Do not print marks, numbering, "(a)/(b)", or a marking scheme in the question text.
- Question length: about 12-70 words.
- Return one JSON object only, with exactly {len(group)} question(s), matching the slot ids, and the scenario field (empty for Part A).
{pair_rule}{scenario_rule}{retry}
STYLE EXAMPLES (real past questions; style only, never copy)
{example_text}

LECTURE EVIDENCE (authoritative; cite chunk_id and quote verbatim)
Each slot may cite only the evidence listed under its own slot id.
{evidence_text}

OUTPUT JSON (this shape)
{schema}
"""


SYSTEM = (
    "You are a university examiner for CSC662 Computer Security. You write "
    "original, grounded exam questions. You never copy past questions. Every "
    "factual marking point is supported by a verbatim quote from the supplied "
    "lecture-slide chunks. Return JSON only."
)


def _slot_record(s: dict, subangle: str = "") -> dict:
    qid = s.get("question", "")
    return {
        "slot": s["slot"],
        "marks": s["marks"],
        "topic": s["topic"],
        "task": s["task"],
        "part": s["part"],
        "dependent": bool(s.get("dependent")),
        "dependent_on": s.get("dependent_on", ""),
        "style_examples": s.get("style_examples", []),
        "style_mode": s.get("style_mode", ""),
        "low_style_confidence": bool(s.get("low_style_confidence")),
        "subangle_required": SUBANGLE_KEYWORDS.get(subangle, []),
    }


def _entailment_check(question: str, point: str, quote: str, model: str,
                      usage: Usage) -> tuple[str, str]:
    """Ask the model whether the quote supports the marking point.

    Returns (verdict, reason) where verdict is yes / partly / no, or
    "error" when the checker call itself failed.
    """
    user = f"""Does the quoted lecture-slide passage support the marking point?

QUESTION: {question}
MARKING POINT: {point}
QUOTE: {quote}

Return one verdict:
- "yes": the quote directly states the fact(s) needed to earn the point;
- "partly": the quote supports part of the point or is ambiguous;
- "no": the quote does not support the point.

Return JSON only: {{"verdict": "yes|partly|no", "reason": "one short sentence"}}"""
    try:
        llm = chat_json_result(
            "You are a strict exam-answer verifier. Check entailment between "
            "a marking point and a quoted slide passage. Return JSON only.",
            user, model=model, temperature=0.0, usage=usage)
        verdict = str(llm.data.get("verdict", "")).strip().lower()
        reason = str(llm.data.get("reason", "")).strip()[:300]
        if verdict not in {"yes", "partly", "no"}:
            verdict = "partly"
        return verdict, reason
    except Exception as e:
        return "error", str(e)[:200]


def _resolve_low_stem_points(q: VerifiedQuestion, hits: list,
                             used_sources: set[tuple[str, int]],
                             usage: Usage, model: str,
                             threshold: float,
                             max_retries: int = 2) -> dict:
    """Entailment-gate low stem-overlap points; regenerate only on "no".

    A point whose stemmed overlap is below the threshold is checked by the
    LLM.  "yes" and "partly" are kept and recorded; only "no" triggers up to
    two point-level rewrites.  A rewrite with high stem overlap passes the
    first gate; a rewrite with low stem overlap is entailment-checked too.
    If no rewrite succeeds, the original point remains flagged.
    """
    by_id = {h.chunk.chunk_id: h.chunk for h in hits}
    stats = {"calls": 0, "entailment_calls": 0, "initial_verdicts": {}}
    regen_calls = 0
    for idx, pt in enumerate(list(q.marking_points)):
        if not pt.low_stem_overlap:
            continue
        verdict, reason = _entailment_check(q.question, pt.point, pt.quote,
                                            model, usage)
        stats["calls"] += 1
        stats["entailment_calls"] += 1
        stats["initial_verdicts"][verdict] = (
            stats["initial_verdicts"].get(verdict, 0) + 1)
        pt.entailment = verdict
        pt.entailment_reason = reason
        if verdict != "no":
            continue
        replacement: VerifiedPoint | None = None
        for _ in range(max_retries):
            evidence = "\n\n".join(
                f"[{h.chunk.chunk_id}] {h.chunk.deck} | slide "
                f"{h.chunk.slide}\n{h.chunk.text}" for h in hits)
            user = f"""Rewrite ONLY one marking point for this exam question.

Question ({q.slot}): {q.question}

The current point was rejected by an entailment check:
  point: {pt.point}
  quote: {pt.quote}
  verdict: {pt.entailment} ({pt.entailment_reason})

Return JSON:
{{"point": "one clear marking point", "quote": "verbatim contiguous text from the evidence", "chunk_id": "exact chunk id"}}

Rules:
- The point must be an answer requirement in your own words. Do NOT copy
  the quote into the point; a point that is a verbatim copy of its quote is
  rejected.
- The quote must be copied exactly from one evidence chunk; no ellipses.
- The quote must not be a slide title or bare heading.
- The point is worth one mark.
- Use only the evidence below.
- Prefer evidence that clearly entails the point; aim for stemmed content
  overlap >= {threshold:.2f}.

Evidence:
{evidence}
"""
            try:
                llm = chat_json_result(
                    "You repair one marking point in a university exam "
                    "answer. Return JSON only.", user, model=model,
                    temperature=0.1, usage=usage)
                stats["calls"] += 1
                regen_calls += 1
                data = llm.data
                point = str(data.get("point", "")).strip()
                quote = normalize_text(data.get("quote", ""))
                cid = clean_chunk_id(str(data.get("chunk_id", "")))
                chunk = by_id.get(cid)
                if not point or not quote or chunk is None:
                    continue
                if "..." in quote or "…" in quote:
                    continue
                if quote_is_only_title(quote, chunk):
                    continue
                if len(quote) < 8 or len(quote.split()) < 2:
                    continue
                if quote not in normalize_text(chunk.text):
                    continue
                key = (chunk.deck, chunk.slide)
                if key in used_sources:
                    continue
                if is_verbatim_copy(point, quote):
                    continue
                tover = stem_overlap(point, quote)
                new_pt = VerifiedPoint(
                    point=point, marks=1, quote=quote,
                    source_file=chunk.deck, source_slide=chunk.slide,
                    source_deck=chunk.deck, chunk_id=chunk.chunk_id,
                    source_key=source_key(chunk),
                    term_overlap=round(term_overlap(point, quote), 3),
                    low_term_overlap=tover < threshold,
                    stem_overlap=round(tover, 3),
                    low_stem_overlap=tover < threshold,
                    short_quote=len(quote.split()) < 5,
                    quote_repaired=False)
                if tover >= threshold:
                    replacement = new_pt
                    break
                verdict, reason = _entailment_check(
                    q.question, point, quote, model, usage)
                stats["calls"] += 1
                stats["entailment_calls"] += 1
                new_pt.entailment = verdict
                new_pt.entailment_reason = reason
                if verdict in {"yes", "partly"}:
                    replacement = new_pt
                    break
                # "no" (or checker error): try another rewrite.
            except Exception:
                stats["calls"] += 1
                regen_calls += 1
                continue
        if replacement is not None:
            q.marking_points[idx] = replacement
    q.source_keys = sorted({p.source_key for p in q.marking_points})
    q.citations = sorted({f"{p.source_file}, slide {p.source_slide}"
                          for p in q.marking_points})
    stats["regeneration_calls"] = regen_calls
    return stats


def _source_overlap(accepted: list[VerifiedQuestion]) -> dict:
    by_key: dict[str, set[str]] = defaultdict(set)
    for q in accepted:
        for pt in q.marking_points:
            by_key[pt.source_key].add(q.slot)
    overlaps = {k: sorted(v) for k, v in by_key.items() if len(v) > 1}
    distinct = len(by_key)
    return {
        "distinct_source_keys": distinct,
        "overlap_keys": overlaps,
        "overlap_key_count": len(overlaps),
        "overlap_slot_count": len({s for v in overlaps.values() for s in v}),
        "overlap_rate": round(len(overlaps) / distinct, 4) if distinct else 0.0,
    }


def _actual_topic_mix(accepted: list[VerifiedQuestion]) -> dict[str, int]:
    """Accepted marks by the planner's slot topic."""
    out: Counter = Counter()
    for q in accepted:
        out[q.topic] += q.marks
    return dict(out)


def _cited_deck_topic_mix(accepted: list[VerifiedQuestion]) -> dict[str, int]:
    """Diagnostic: majority deck-topic per accepted question (not primary)."""
    out: Counter = Counter()
    for q in accepted:
        counts = Counter(deck_topic(pt.source_deck)
                         for pt in q.marking_points)
        if counts:
            top = counts.most_common()
            topic = (q.topic if len(top) > 1 and top[0][1] == top[1][1]
                     else top[0][0])
        else:
            topic = q.topic
        out[topic] += q.marks
    return dict(out)


def _deck_topic_violations(accepted: list[VerifiedQuestion]) -> list[dict]:
    bad = []
    for q in accepted:
        allowed = TOPIC_DECKS.get(q.topic)
        if not allowed:
            continue
        for pt in q.marking_points:
            if not pt.source_deck.startswith(allowed):
                bad.append({"slot": q.slot, "topic": q.topic,
                            "deck": pt.source_deck})
    return bad


def generate(plan_path: Path, limit: int = 0, model: str | None = None,
             refresh_decks: bool = False,
             previous: dict | None = None,
             near_copy_threshold: float = config.THEORY_NEAR_COPY_THRESHOLD
             ) -> dict:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    slots = _theory_slots(plan)
    groups = _groups(slots)
    subangles: dict[str, str] = {}
    topic_counts: Counter = Counter()
    for _s in slots:
        _t = _s["topic"]
        _i = topic_counts[_t]
        topic_counts[_t] += 1
        _list = TOPIC_SUBANGLES.get(_t, [""])
        subangles[_s["slot"]] = _list[_i % len(_list)]
    accepted: list[VerifiedQuestion] = []
    placeholders: list[Placeholder] = []
    previous_groups: list[dict] = []
    usage = Usage()
    if previous:
        accepted = [VerifiedQuestion.model_validate(q)
                    for q in previous.get("accepted", [])]
        placeholders = [Placeholder.model_validate(p)
                        for p in previous.get("placeholders", [])]
        retry_slots = {p.slot for p in placeholders}
        # Keep a group if any of its slots is a placeholder.
        groups = [g for g in groups
                  if any(s["slot"] in retry_slots for s in g)]
        retry_slots_all = {s["slot"] for g in groups for s in g}
        accepted = [q for q in accepted if q.slot not in retry_slots_all]
        placeholders = [p for p in placeholders
                        if p.slot not in retry_slots_all]
        retry_questions = {g[0]["question"] for g in groups}
        previous_groups = [g for g in previous.get("groups", [])
                           if g.get("question") not in retry_questions]
        # Carry the earlier token spend into the final cost report.
        u = previous.get("usage", {})
        usage = Usage(
            prompt_tokens=int(u.get("prompt_tokens", 0)),
            completion_tokens=int(u.get("completion_tokens", 0)),
            total_tokens=int(u.get("total_tokens", 0)),
            calls=int(u.get("calls", 0)),
            model=u.get("model", ""))
    if limit:
        groups = groups[:limit]
    chunks = load_chunks(refresh=refresh_decks)
    index = BM25Index(chunks)
    used_sources: set[tuple[str, int]] = set()
    for q in accepted:
        for pt in q.marking_points:
            used_sources.add((pt.source_file, pt.source_slide))
    results: list[GroupResult] = []
    accepted_by_slot = {q.slot: q for q in accepted}
    for gi, group in enumerate(groups, 1):
        topic = group[0]["topic"]
        qid = group[0]["question"]
        result = GroupResult(
            question=qid, slots=[s["slot"] for s in group], topic=topic,
            tasks=[s["task"] for s in group],
            dependent=bool(group[0].get("dependent")))
        plan_seed = plan.get("seed", 0)
        scenario_flags: dict[str, bool] = {}
        for _s in group:
            _sid = _s["slot"]
            if _s.get("part") == "B" and _sid.endswith("a"):
                _rng = random.Random(f"{plan_seed}:{qid}:scenario")
                scenario_flags[_sid] = _rng.random() < config.THEORY_SCENARIO_RATE
        result.scenario_sampled = any(scenario_flags.values())
        group_accepted = 0
        for slot in group:
            sid = slot["slot"]
            # A dependent (b) cannot be generated if (a) is unresolved.
            if slot.get("dependent") and sid.endswith("b"):
                a_id = qid + "a"
                if a_id not in accepted_by_slot:
                    reason = f"{sid}: dependent (a) is unresolved"
                    placeholders.append(Placeholder(
                        slot=sid, marks=slot["marks"], topic=slot["topic"],
                        task=slot["task"], reason=reason, attempts=0,
                        low_style_confidence=bool(
                            slot.get("low_style_confidence"))))
                    result.errors.append([reason])
                    continue
            # Part B (b) needs the scenario generated by (a).
            shared_scenario = ""
            if (slot.get("part") == "B" and sid.endswith("b")):
                a_id = qid + "a"
                if a_id not in accepted_by_slot:
                    reason = f"{sid}: Part B (a) is unresolved"
                    placeholders.append(Placeholder(
                        slot=sid, marks=slot["marks"], topic=slot["topic"],
                        task=slot["task"], reason=reason, attempts=0,
                        low_style_confidence=bool(
                            slot.get("low_style_confidence"))))
                    result.errors.append([reason])
                    continue
                shared_scenario = accepted_by_slot[a_id].scenario
            subangle = subangles.get(sid, "")
            hits, fallback, overlap_allowed = _retrieve_for_slot(
                index, slot, topic, used_sources, subangle)
            result.fallback_retrieval = result.fallback_retrieval or fallback
            result.overlap_allowed = result.overlap_allowed or overlap_allowed
            evidence = {sid: hits}
            slot_chunk_ids = {
                sid: {h.chunk.chunk_id for h in hits}
            }
            result.retrieved.extend([{
                "slot": sid,
                "chunk_id": h.chunk.chunk_id, "deck": h.chunk.deck,
                "slide": h.chunk.slide, "score": round(h.score, 2),
                "chars": h.chunk.chars,
            } for h in hits])
            sibling_text = ""
            if sid.endswith("b"):
                a_id = qid + "a"
                if a_id in accepted_by_slot:
                    sibling_text = accepted_by_slot[a_id].question
            scenario_required = (slot.get("part") == "B"
                                 and sid.endswith("a")
                                 and scenario_flags.get(sid, False))
            before_calls, before_tokens = usage.calls, usage.total_tokens
            errors: list[str] = []
            verified: list[VerifiedQuestion] = []
            slot_attempts = 0
            for attempt in range(1, MAX_ATTEMPTS + 1):
                slot_attempts += 1
                result.total_draft_attempts += 1
                user = _prompt(
                    [slot], evidence, errors if attempt > 1 else None,
                    sibling_text=sibling_text,
                    shared_scenario=shared_scenario,
                    dependent=bool(slot.get("dependent")),
                    scenario_required=scenario_required,
                    same_topic_questions=[
                        q.question for q in accepted
                        if q.topic == slot["topic"]][-5:],
                    subangle=subangle)
                try:
                    llm = chat_json_result(
                        SYSTEM, user, model=model or config.MOCKGEN_MODEL,
                        temperature=0.15, usage=usage)
                except Exception as e:
                    errors = [f"LLM/API error: {e}"]
                    result.errors.append(errors)
                    continue
                result.last_draft = llm.data
                try:
                    draft = TheoryDraft.model_validate(llm.data)
                except ValidationError as e:
                    errors = [f"JSON schema error: {e.errors()[:4]}"]
                    result.errors.append(errors)
                    continue
                verified, errors = verify_draft(
                    draft, [_slot_record(slot, subangle)],
                    [h.chunk for h in hits],
                    [q.model_dump() for q in accepted],
                    used_sources=used_sources,
                    allow_overlap=overlap_allowed,
                    scenario_required=scenario_required,
                    shared_scenario=shared_scenario,
                    slot_chunk_ids=slot_chunk_ids,
                    near_copy_threshold=near_copy_threshold,
                    stem_overlap_threshold=config.THEORY_STEM_OVERLAP_THRESHOLD)
                # Deterministic wording repair: if the only failure is a
                # missing (a)-reference or scenario reference, prepend the
                # required phrase and verify again.  This does not change any
                # marking point or quote.
                if errors and slot.get("dependent") and sid.endswith("b") \
                        and all("does not refer back" in e for e in errors):
                    q0 = draft.questions[0]
                    draft2 = TheoryDraft(
                        scenario=draft.scenario,
                        questions=[DraftQuestion(
                            slot=q0.slot,
                            question="Refer to your answer in (a). "
                                     + q0.question,
                            marking_points=q0.marking_points)])
                    verified2, errors2 = verify_draft(
                        draft2, [_slot_record(slot, subangle)],
                        [h.chunk for h in hits],
                        [q.model_dump() for q in accepted],
                        used_sources=used_sources,
                        allow_overlap=overlap_allowed,
                        scenario_required=scenario_required,
                        shared_scenario=shared_scenario,
                        slot_chunk_ids=slot_chunk_ids,
                        near_copy_threshold=near_copy_threshold,
                        stem_overlap_threshold=config.THEORY_STEM_OVERLAP_THRESHOLD)
                    if not errors2 and verified2:
                        verified, errors = verified2, errors2
                        result.last_draft = draft2.model_dump()
                if errors and shared_scenario and all(
                        "must refer to the shared scenario" in e for e in errors):
                    q0 = draft.questions[0]
                    draft2 = TheoryDraft(
                        scenario=draft.scenario,
                        questions=[DraftQuestion(
                            slot=q0.slot,
                            question="Based on the scenario, " + q0.question,
                            marking_points=q0.marking_points)])
                    verified2, errors2 = verify_draft(
                        draft2, [_slot_record(slot, subangle)],
                        [h.chunk for h in hits],
                        [q.model_dump() for q in accepted],
                        used_sources=used_sources,
                        allow_overlap=overlap_allowed,
                        scenario_required=scenario_required,
                        shared_scenario=shared_scenario,
                        slot_chunk_ids=slot_chunk_ids,
                        near_copy_threshold=near_copy_threshold,
                        stem_overlap_threshold=config.THEORY_STEM_OVERLAP_THRESHOLD)
                    if not errors2 and verified2:
                        verified, errors = verified2, errors2
                        result.last_draft = draft2.model_dump()
                result.errors.append(errors)
                if not errors and verified:
                    break
            result.attempts = max(result.attempts, slot_attempts)
            result.usage["calls"] = (result.usage.get("calls", 0)
                                     + usage.calls - before_calls)
            result.usage["tokens"] = (result.usage.get("tokens", 0)
                                      + usage.total_tokens - before_tokens)
            if not errors and verified:
                if shared_scenario:
                    a_q = accepted_by_slot.get(qid + "a")
                    if a_q is not None:
                        for q in verified:
                            q.scenario_grounding = a_q.scenario_grounding
                point_before_tokens = usage.total_tokens
                point_stats = {"calls": 0, "entailment_calls": 0,
                               "regeneration_calls": 0}
                initial_counts: Counter = Counter()
                for q in verified:
                    st = _resolve_low_stem_points(
                        q, hits, used_sources, usage,
                        model or config.MOCKGEN_MODEL,
                        config.THEORY_STEM_OVERLAP_THRESHOLD)
                    for k in point_stats:
                        point_stats[k] += int(st.get(k, 0))
                    initial_counts.update(st.get("initial_verdicts", {}))
                result.point_retry_calls += point_stats["calls"]
                result.entailment_calls += point_stats["entailment_calls"]
                result.point_regeneration_calls += point_stats[
                    "regeneration_calls"]
                merged_initial = Counter(result.initial_entailment_counts)
                merged_initial.update(initial_counts)
                result.initial_entailment_counts = dict(merged_initial)
                result.usage["calls"] = (result.usage.get("calls", 0)
                                         + point_stats["calls"])
                result.usage["tokens"] = (result.usage.get("tokens", 0)
                                          + usage.total_tokens
                                          - point_before_tokens)
                accepted.extend(verified)
                for q in verified:
                    accepted_by_slot[q.slot] = q
                    for pt in q.marking_points:
                        used_sources.add((pt.source_file, pt.source_slide))
                group_accepted += 1
                print(f"[{gi}/{len(groups)}] {sid} accepted "
                      f"(attempt {result.attempts} cumulative)", flush=True)
            else:
                reason = "; ".join(errors[-8:]) if errors else "unknown error"
                placeholders.append(Placeholder(
                    slot=sid, marks=slot["marks"], topic=slot["topic"],
                    task=slot["task"], reason=reason[:1500],
                    attempts=result.attempts,
                    low_style_confidence=bool(
                        slot.get("low_style_confidence"))))
                print(f"[{gi}/{len(groups)}] {sid} PLACEHOLDER after "
                      f"{result.attempts} cumulative attempts: "
                      f"{reason[:160]}", flush=True)
        result.accepted = group_accepted == len(group)
        results.append(result)

    accepted.sort(key=lambda q: q.slot)
    placeholders.sort(key=lambda p: p.slot)
    total_usage = usage.as_dict()
    cost = total_usage["cost_usd"]
    accepted_count = len(accepted)
    all_points = [pt for q in accepted for pt in q.marking_points]
    low_points = [pt for pt in all_points if pt.low_stem_overlap]
    entailment_counts = Counter(pt.entailment for pt in low_points
                                if pt.entailment)
    initial_entailment_counts = Counter()
    for g in results:
        initial_entailment_counts.update(
            g.initial_entailment_counts or {})
    verbatim_rejections = sum(
        1 for g in results for attempt in g.errors for e in attempt
        if "verbatim copy" in e)
    payload = {
        "model": model or config.MOCKGEN_MODEL,
        "plan": str(plan_path),
        "attempt_limit": MAX_ATTEMPTS,
        "max_attempts_per_slot": MAX_ATTEMPTS,
        "near_copy_threshold": near_copy_threshold,
        "stem_overlap_threshold": config.THEORY_STEM_OVERLAP_THRESHOLD,
        "scenario_rate": config.THEORY_SCENARIO_RATE,
        "accepted": [q.model_dump() for q in accepted],
        "placeholders": [p.model_dump() for p in placeholders],
        "groups": sorted(previous_groups + [asdict(r) for r in results],
                         key=lambda g: g.get("question", "")),
        "usage": total_usage,
        "accepted_count": accepted_count,
        "placeholder_count": len(placeholders),
        "cost_per_accepted_question_usd": round(
            cost / accepted_count, 6) if accepted_count else None,
        "source_overlap": _source_overlap(accepted),
        "planned_topic_mix": plan.get("assigned_theory_topic_marks", {}),
        "actual_topic_mix": _actual_topic_mix(accepted),
        "cited_deck_topic_mix": _cited_deck_topic_mix(accepted),
        "deck_topic_violations": _deck_topic_violations(accepted),
        "topic_deck_map": {k: list(v) for k, v in TOPIC_DECKS.items()},
        "points_total": len(all_points),
        "low_stem_overlap_points": [
            {"slot": q.slot, "point": pt.point,
             "stem_overlap": pt.stem_overlap,
             "raw_term_overlap": pt.term_overlap,
             "entailment": pt.entailment,
             "entailment_reason": pt.entailment_reason}
            for q in accepted for pt in q.marking_points
            if pt.low_stem_overlap
        ],
        "high_stem_overlap_points": len(all_points) - len(low_points),
        "entailment_counts": dict(entailment_counts),
        "initial_entailment_counts": dict(initial_entailment_counts),
        "entailment_checked_points": sum(entailment_counts.values()),
        "verbatim_copy_rejections": verbatim_rejections,
        "entailment_calls": sum(g.entailment_calls for g in results),
        "point_regeneration_calls": sum(g.point_regeneration_calls
                                        for g in results),
        # Legacy key kept for older reporting scripts.
        "low_term_overlap_points": [
            {"slot": q.slot, "point": pt.point, "overlap": pt.stem_overlap}
            for q in accepted for pt in q.marking_points
            if pt.low_stem_overlap
        ],
        "short_quote_points": [
            {"slot": q.slot, "point": pt.point, "quote": pt.quote}
            for q in accepted for pt in q.marking_points
            if pt.short_quote
        ],
        "repaired_quote_count": sum(
            1 for q in accepted for pt in q.marking_points
            if pt.quote_repaired),
        "scenario_questions": [
            {"slot": q.slot, "scenario": q.scenario,
             "grounding": q.scenario_grounding}
            for q in accepted if q.scenario
        ],
        "deck_coverage": coverage(chunks),
        "eth_deck_coverage": coverage(
            [c for c in chunks if c.deck.startswith("071")]),
    }
    return payload


def report(payload: dict) -> str:
    lines = [
        "# Theory module report",
        "",
        f"- model: **{payload['model']}**; attempt limit: "
        f"{payload['attempt_limit']} (initial + up to 3 retries)",
        f"- accepted theory answers: **{payload['accepted_count']}** "
        "(supported by lecture slides, not lecturer-marked); "
        f"placeholders: **{payload['placeholder_count']}**",
        f"- source overlap: **{payload.get('source_overlap', {}).get('overlap_key_count', 0)}** "
        "keys; target 0",
        f"- low stem-overlap points: **{len(payload.get('low_stem_overlap_points', []))}** "
        f"of {payload.get('points_total', 0)}; initial entailment "
        f"{payload.get('initial_entailment_counts', {})}; final accepted "
        f"entailment {payload.get('entailment_counts', {})}; verbatim-copy "
        f"rejections: **{payload.get('verbatim_copy_rejections', 0)}**; "
        f"short quotes: "
        f"**{len(payload.get('short_quote_points', []))}**; repaired quotes: "
        f"**{payload.get('repaired_quote_count', 0)}**",
        f"- tokens: {payload['usage']['prompt_tokens']} prompt + "
        f"{payload['usage']['completion_tokens']} completion = "
        f"{payload['usage']['total_tokens']} across "
        f"{payload['usage']['calls']} calls",
        f"- estimated cost: **${payload['usage']['cost_usd']:.4f}** "
        f"(model {payload['usage'].get('model', '')}; input "
        f"${payload['usage']['input_price_per_1m']}/M, output "
        f"${payload['usage']['output_price_per_1m']}/M; official list-price "
        "estimate, not an invoice)",
        f"- cost per accepted question: "
        f"**${payload['cost_per_accepted_question_usd'] or 0:.4f}**",
        "",
        "## Accepted questions",
        "",
        "| Slot | Marks | Topic | Command | Sources | Style |",
        "|---|---:|---|---|---|---|",
    ]
    for q in payload["accepted"]:
        style = q["style_mode"] + ("; LOW" if q["low_style_confidence"] else "")
        lines.append(f"| {q['slot']} | {q['marks']} | {q['topic']} | "
                     f"{q['task']} | {'; '.join(q['citations'])} | {style} |")
    lines += [
        "",
        "## Placeholders",
        "",
        "| Slot | Marks | Topic | Command | Attempts | Reason |",
        "|---|---:|---|---|---:|---|",
    ]
    for p in payload["placeholders"]:
        lines.append(f"| {p['slot']} | {p['marks']} | {p['topic']} | "
                     f"{p['task']} | {p['attempts']} | "
                     f"{p['reason'].replace('|', '/')} |")
    lines += [
        "",
        "## Group attempts and retrieval",
        "",
        "| Question | Slots | Attempts | Result | Fallback retrieval | Top sources |",
        "|---|---|---:|---|---|---|",
    ]
    for g in payload["groups"]:
        top = "; ".join(f"{r['deck']} s{r['slide']}"
                        for r in g["retrieved"][:3]) or "none"
        lines.append(f"| {g['question']} | {', '.join(g['slots'])} | "
                     f"{g['attempts']} | "
                     f"{'accepted' if g['accepted'] else 'placeholder'} | "
                     f"{'yes' if g['fallback_retrieval'] else 'no'} | {top} |")
    lines += [
        "",
        "## Deck coverage",
        "",
        f"- 071 Ethics: {payload['eth_deck_coverage']}",
        f"- total decks with text: {len(payload['deck_coverage'])}; "
        f"total chunks: {sum(v['chunks'] for v in payload['deck_coverage'].values())}",
        "",
        "## Verification rules applied",
        "",
        "- quote must be a verbatim contiguous substring of the cited retrieved "
        "chunk (whitespace-normalised); ellipses and slide-title-only quotes "
        "rejected; near-paraphrases repaired only when an exact close line exists;",
        "- exactly one marking point per mark;",
        "- near-copy rejected at fuzzy similarity >= 0.80 against all 35 papers; "
        "cross-generated near-duplicates and source overlap rejected;",
        "- cited decks must be in the slot topic's allowed deck map;",
        "- first gate is stemmed content-token overlap (Snowball English "
        "stemmer); low-overlap points are checked by an LLM entailment "
        "verifier (yes/partly/no), and only 'no' triggers regeneration;",
        "- a marking point that is a verbatim copy of its quote is rejected;",
        "- command word and topic sub-angle must appear; dependent (b) must refer "
        "back to (a); Part B (a)/(b) share a generated scenario;",
        "- no retrieval evidence => placeholder, never an unsupported answer.",
    ]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan",
                    default=str(config.OUTPUTS_DIR / "planner_revised_realistic.json"))
    ap.add_argument("--out-prefix", default="theory_drafts_realistic")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--model", default=config.MOCKGEN_MODEL)
    ap.add_argument("--refresh-decks", action="store_true")
    ap.add_argument("--near-copy-threshold", type=float,
                    default=config.THEORY_NEAR_COPY_THRESHOLD)
    ap.add_argument("--retry-placeholders", action="store_true",
                    help="keep prior accepted questions and retry only the "
                         "groups that ended as placeholders")
    args = ap.parse_args()
    if args.model.startswith("deepseek"):
        if not config.DEEPSEEK_API_KEY:
            raise SystemExit("DEEPSEEK_API_KEY is not set")
    elif not config.QWEN_API_KEY:
        raise SystemExit("QWEN_API_KEY is not set")
    prefix = args.out_prefix.split("/")[-1]
    jp = config.OUTPUTS_DIR / f"{prefix}.json"
    mp = config.OUTPUTS_DIR / f"{prefix}.md"
    previous = None
    if args.retry_placeholders:
        if not jp.exists():
            raise SystemExit(f"no previous payload at {jp}")
        previous = json.loads(jp.read_text(encoding="utf-8"))
    payload = generate(Path(args.plan), args.limit, args.model,
                       args.refresh_decks, previous,
                       near_copy_threshold=args.near_copy_threshold)
    if previous:
        payload["retried_placeholders"] = True
    jp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md = report(payload)
    mp.write_text(md, encoding="utf-8")
    print(md)
    print(f"\nwrote {jp} and {mp}")


if __name__ == "__main__":
    main()
