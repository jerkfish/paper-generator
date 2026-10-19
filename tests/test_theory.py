"""Deck chunking, BM25 retrieval and theory-verifier invariants."""
from __future__ import annotations

from src.planner.fingerprint_data import load_all_rows
from src.theory.bm25 import BM25Index, topic_query
from src.theory.decks import load_chunks
from src.theory.models import DraftQuestion, MarkingPoint, TheoryDraft
from src.theory.verify import (clean_chunk_id, near_copy, normalize_text,
                               verify_draft)


def _chunks():
    return load_chunks()


def _first_quote(chunk, n=80):
    text = normalize_text(chunk.text)
    return text[:n].strip()


def test_decks_load_read_only_and_ethics_coverage():
    chunks = _chunks()
    assert len(chunks) > 300
    ethics = [c for c in chunks if c.deck.startswith("071")]
    assert ethics
    assert all(c.slide >= 1 for c in ethics)


def test_chunk_id_cleanup_handles_brackets_and_evidence_suffix():
    assert clean_chunk_id("[071 - Ethics::s05::1]") == "071 - Ethics::s05::1"
    assert clean_chunk_id(
        "[071 - Ethics::s05::1] 071 - Ethics | slide 5") == \
        "071 - Ethics::s05::1"


def test_bm25_ethics_retrieval_stays_in_deck_071():
    chunks = _chunks()
    idx = BM25Index(chunks)
    hits = idx.search(topic_query("risk/management (ethics)"), k=5,
                      allowed_prefixes=("071",))
    assert hits
    assert all(h.chunk.deck.startswith("071") for h in hits)


def _draft(slot, question, points):
    return TheoryDraft(questions=[DraftQuestion(
        slot=slot, question=question,
        marking_points=[MarkingPoint(**p) for p in points])])


def test_verbatim_quote_passes_and_altered_quote_fails():
    chunk = next(c for c in _chunks() if c.deck.startswith("071")
                 and len(c.text) > 100)
    quote = _first_quote(chunk)
    exp = [{"slot": "A1a", "marks": 1, "topic": "risk/management (ethics)",
            "task": "Explain", "dependent": False}]
    good = _draft("A1a", "Explain the ethical basis of professional conduct in computing.",
                  [{"point": "Ethics is a documented set of acceptable "
                            "behaviours.", "quote": quote,
                    "chunk_id": chunk.chunk_id}])
    verified, errors = verify_draft(good, exp, [chunk])
    assert not errors
    assert verified[0].confidence == "sourced"
    assert verified[0].citations
    bad = _draft("A1a", "Explain the ethical basis of professional conduct in computing.",
                 [{"point": "Ethics is a documented set of acceptable "
                           "behaviours.", "quote": quote + " NOT IN SLIDE",
                   "chunk_id": chunk.chunk_id}])
    _, errors = verify_draft(bad, exp, [chunk])
    assert any("not verbatim" in e for e in errors)


def test_point_count_mismatch_is_rejected():
    chunk = next(c for c in _chunks() if c.deck.startswith("071")
                 and len(c.text) > 100)
    quote = _first_quote(chunk)
    exp = [{"slot": "A1a", "marks": 2, "topic": "risk/management (ethics)",
            "task": "Explain", "dependent": False}]
    draft = _draft("A1a", "Explain two ethical principles in computing.",
                   [{"point": "One point.", "quote": quote,
                     "chunk_id": chunk.chunk_id}])
    _, errors = verify_draft(draft, exp, [chunk])
    assert any("marking points" in e for e in errors)


def test_near_copy_of_real_question_is_detected():
    row = next(r for r in load_all_rows()
               if str(r["Original question text"]).strip())
    nc = near_copy(str(row["Original question text"]))
    assert nc.ratio >= 0.99


def test_cross_generated_near_duplicate_is_rejected():
    chunk = next(c for c in _chunks() if c.deck.startswith("071")
                 and len(c.text) > 100)
    quote = _first_quote(chunk)
    exp = [{"slot": "A2a", "marks": 1, "topic": "risk/management (ethics)",
            "task": "Explain", "dependent": False}]
    draft = _draft("A2a",
                   "Explain the ethical basis of professional conduct in computing.",
                   [{"point": "One point.", "quote": quote,
                     "chunk_id": chunk.chunk_id}])
    prior = [{"slot": "A1a",
              "question": "Explain the ethical basis of professional conduct in computing."}]
    _, errors = verify_draft(draft, exp, [chunk], prior)
    assert any("near-duplicate" in e for e in errors)


def test_angle_hint_required_and_forbidden():
    chunk = next(c for c in _chunks() if c.deck.startswith("071")
                 and len(c.text) > 100)
    quote = _first_quote(chunk)
    exp = [{"slot": "A9a", "marks": 1,
            "topic": "risk/management (ethics)", "task": "Explain",
            "dependent": False, "angle_required": ["password"],
            "angle_forbidden": ["biometric"]}]
    draft = _draft("A9a", "Explain two biometric controls for authentication.",
                   [{"point": "One.", "quote": quote,
                     "chunk_id": chunk.chunk_id}])
    _, errors = verify_draft(draft, exp, [chunk])
    assert any("angle hint not followed" in e for e in errors)
    assert any("forbidden angle" in e for e in errors)


def test_sibling_pair_must_use_different_angles():
    chunk = next(c for c in _chunks() if c.deck.startswith("071")
                 and len(c.text) > 200)
    quote = _first_quote(chunk)
    exp = [
        {"slot": "A1a", "marks": 1, "topic": "risk/management (ethics)",
         "task": "Explain", "dependent": False},
        {"slot": "A1b", "marks": 1, "topic": "risk/management (ethics)",
         "task": "Explain", "dependent": False},
    ]
    text = "Explain the ethical basis of professional conduct in computing."
    draft = TheoryDraft.model_validate({"questions": [
        {"slot": "A1a", "question": text,
         "marking_points": [{"point": "One.", "quote": quote,
                             "chunk_id": chunk.chunk_id}]},
        {"slot": "A1b", "question": text,
         "marking_points": [{"point": "Two.", "quote": quote,
                             "chunk_id": chunk.chunk_id}]},
    ]})
    _, errors = verify_draft(draft, exp, [chunk])
    assert any("sibling pair near-duplicate" in e for e in errors)


def test_dependent_b_must_refer_to_a():
    chunks = [c for c in _chunks() if c.deck.startswith("071")]
    chunk = next(c for c in chunks if len(c.text) > 200)
    quote = _first_quote(chunk)
    exp = [
        {"slot": "A1a", "marks": 1, "topic": "risk/management (ethics)",
         "task": "Explain", "dependent": True},
        {"slot": "A1b", "marks": 1, "topic": "risk/management (ethics)",
         "task": "Justify", "dependent": True},
    ]
    a = {"slot": "A1a", "question": "Explain one ethical principle.",
         "marking_points": [{"point": "Point a.", "quote": quote,
                             "chunk_id": chunk.chunk_id}]}
    b = {"slot": "A1b", "question": "Justify the principle in your answer.",
         "marking_points": [{"point": "Point b.", "quote": quote,
                             "chunk_id": chunk.chunk_id}]}
    draft = TheoryDraft.model_validate({"questions": [a, b]})
    _, errors = verify_draft(draft, exp, chunks)
    assert any("does not refer back" in e for e in errors)
