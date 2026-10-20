"""Deck chunking, BM25 retrieval and theory-verifier invariants."""
from __future__ import annotations

from src.planner.fingerprint_data import load_all_rows
from src.theory.bm25 import BM25Index, topic_query
from src.theory.decks import load_chunks
from src.theory.models import (DraftQuestion, MarkingPoint, TheoryDraft,
                               VerifiedPoint, VerifiedQuestion)
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
                 and "Ethics is a suite" in c.text)
    text = normalize_text(chunk.text)
    quote = text[text.index("Ethics is a suite"):
                 text.index("Ethics is a suite") + 140]
    exp = [{"slot": "A1a", "marks": 1, "topic": "risk/management (ethics)",
            "task": "Explain", "dependent": False}]
    point = "Ethics is a set of guiding beliefs and standards."
    good = _draft("A1a", "Explain the ethical basis of professional conduct in computing.",
                  [{"point": point, "quote": quote,
                    "chunk_id": chunk.chunk_id}])
    verified, errors = verify_draft(good, exp, [chunk])
    assert not errors
    assert verified[0].confidence.startswith("supported by lecture slides")
    assert verified[0].citations
    bad = _draft("A1a", "Explain the ethical basis of professional conduct in computing.",
                 [{"point": point, "quote": quote + " NOT IN SLIDE",
                   "chunk_id": chunk.chunk_id}])
    verified_bad, errors = verify_draft(bad, exp, [chunk])
    if errors:
        assert any("not verbatim" in e for e in errors)
    else:
        assert verified_bad[0].marking_points[0].quote_repaired is True


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


def test_source_overlap_across_slots_is_rejected():
    chunk = next(c for c in _chunks() if c.deck.startswith("071")
                 and "Ethics is a suite" in c.text)
    text = normalize_text(chunk.text)
    quote = text[text.index("Ethics is a suite"):
                 text.index("Ethics is a suite") + 120]
    exp = [
        {"slot": "A1a", "marks": 1, "topic": "risk/management (ethics)",
         "task": "Explain", "dependent": False},
        {"slot": "A1b", "marks": 1, "topic": "risk/management (ethics)",
         "task": "Explain", "dependent": False},
    ]
    draft = TheoryDraft.model_validate({"questions": [
        {"slot": "A1a", "question": "Explain the ethical basis of conduct.",
         "marking_points": [{"point": "Ethics is a set of guiding beliefs.",
                             "quote": quote, "chunk_id": chunk.chunk_id}]},
        {"slot": "A1b", "question": "Explain how ethical standards guide people.",
         "marking_points": [{"point": "Ethics is a set of guiding beliefs.",
                             "quote": quote, "chunk_id": chunk.chunk_id}]},
    ]})
    _, errors = verify_draft(draft, exp, [chunk])
    assert any("source overlap" in e for e in errors)


def test_quote_title_is_rejected():
    chunk = next(c for c in _chunks() if c.deck.startswith("071")
                 and len(c.text.splitlines()) > 1)
    title = normalize_text(chunk.text.splitlines()[0])
    exp = [{"slot": "A1a", "marks": 1, "topic": "risk/management (ethics)",
            "task": "Explain", "dependent": False}]
    draft = _draft("A1a", "Explain the ethical basis of professional conduct.",
                   [{"point": "Ethics is a set of guiding beliefs.",
                     "quote": title, "chunk_id": chunk.chunk_id}])
    _, errors = verify_draft(draft, exp, [chunk])
    assert any("slide title" in e for e in errors)


def test_topic_source_must_match_allowed_decks():
    chunk = next(c for c in _chunks() if c.deck.startswith("051"))
    text = normalize_text(chunk.text)
    quote = text[:100]
    exp = [{"slot": "A1a", "marks": 1, "topic": "network security",
            "task": "Explain", "dependent": False}]
    draft = _draft("A1a", "Explain how network mechanisms protect systems.",
                   [{"point": "A network mechanism protects the system.",
                     "quote": quote, "chunk_id": chunk.chunk_id}])
    _, errors = verify_draft(draft, exp, [chunk])
    assert any("outside the allowed decks" in e for e in errors)


def test_part_b_scenario_is_required():
    chunks = [c for c in _chunks() if c.deck.startswith("071")][:2]
    text = normalize_text(chunks[0].text)
    quote = text[:100]
    exp = [
        {"slot": "B1a", "marks": 1, "topic": "risk/management (ethics)",
         "task": "Explain", "dependent": False, "part": "B"},
        {"slot": "B1b", "marks": 1, "topic": "risk/management (ethics)",
         "task": "Explain", "dependent": False, "part": "B"},
    ]
    draft = TheoryDraft.model_validate({"questions": [
        {"slot": "B1a", "question": "Explain the scenario's ethical issue.",
         "marking_points": [{"point": "Ethics is a set of guiding beliefs.",
                             "quote": quote, "chunk_id": chunks[0].chunk_id}]},
        {"slot": "B1b", "question": "Explain the scenario's legal issue.",
         "marking_points": [{"point": "Ethics is a set of guiding beliefs.",
                             "quote": quote, "chunk_id": chunks[1].chunk_id}]},
    ]})
    _, errors = verify_draft(draft, exp, chunks, scenario_required=True)
    assert any("scenario missing" in e for e in errors)


def test_entailment_no_triggers_point_regeneration(monkeypatch):
    from types import SimpleNamespace
    from src.theory.bm25 import Hit
    from src.theory.generate import _resolve_low_stem_points
    from src.llm import Usage

    chunk = next(c for c in _chunks() if c.deck.startswith("071")
                 and "Ethics is a suite" in c.text)
    text = normalize_text(chunk.text)
    quote = text[text.index("Ethics is a suite"):
                 text.index("Ethics is a suite") + 140]
    old = VerifiedQuestion(
        slot="A1a", question="Explain the ethical basis of conduct in computing.",
        marks=1, topic="risk/management (ethics)", task="Explain",
        marking_points=[VerifiedPoint(
            point="Unrelated point about networks.", marks=1, quote="unrelated",
            source_file=chunk.deck, source_slide=chunk.slide,
            source_deck=chunk.deck, chunk_id=chunk.chunk_id,
            source_key="x", term_overlap=0.0, low_term_overlap=True,
            stem_overlap=0.0, low_stem_overlap=True)],
        citations=[])
    replies = iter([
        SimpleNamespace(data={"verdict": "no", "reason": "no support"}),
        SimpleNamespace(data={
            "point": "Ethics is a set of guiding beliefs and standards.",
            "quote": quote,
            "chunk_id": chunk.chunk_id,
        }),
    ])
    monkeypatch.setattr(
        "src.theory.generate.chat_json_result",
        lambda *a, **k: next(replies))
    stats = _resolve_low_stem_points(
        old, [Hit(1.0, chunk)], set(), Usage(), "fake", 0.5)
    assert stats["entailment_calls"] == 1
    assert stats["regeneration_calls"] == 1
    assert old.marking_points[0].stem_overlap >= 0.5
    assert old.marking_points[0].low_stem_overlap is False


def test_entailment_partly_keeps_point_without_regeneration(monkeypatch):
    from types import SimpleNamespace
    from src.theory.bm25 import Hit
    from src.theory.generate import _resolve_low_stem_points
    from src.llm import Usage

    chunk = next(c for c in _chunks() if c.deck.startswith("071")
                 and "Ethics is a suite" in c.text)
    text = normalize_text(chunk.text)
    quote = text[text.index("Ethics is a suite"):
                 text.index("Ethics is a suite") + 140]
    old = VerifiedQuestion(
        slot="A1a", question="Explain the ethical basis of conduct in computing.",
        marks=1, topic="risk/management (ethics)", task="Explain",
        marking_points=[VerifiedPoint(
            point="Unrelated point about networks.", marks=1, quote=quote,
            source_file=chunk.deck, source_slide=chunk.slide,
            source_deck=chunk.deck, chunk_id=chunk.chunk_id,
            source_key="x", term_overlap=0.0, low_term_overlap=True,
            stem_overlap=0.0, low_stem_overlap=True)],
        citations=[])
    monkeypatch.setattr(
        "src.theory.generate.chat_json_result",
        lambda *a, **k: SimpleNamespace(
            data={"verdict": "partly", "reason": "some support"}))
    stats = _resolve_low_stem_points(
        old, [Hit(1.0, chunk)], set(), Usage(), "fake", 0.5)
    assert stats["entailment_calls"] == 1
    assert stats["regeneration_calls"] == 0
    assert old.marking_points[0].entailment == "partly"


def test_stem_overlap_handles_inflections():
    from src.theory.verify import stem_overlap
    assert stem_overlap("identifying attacks and stopping processes",
                        "identify attack stop process") >= 0.99


def test_verbatim_copy_point_is_rejected():
    from src.theory.verify import is_verbatim_copy
    quote = ("Ethics is a suite of guiding beliefs, standards, or ideals "
             "that pervades an individual or a group.")
    assert is_verbatim_copy(quote, quote)
    assert is_verbatim_copy("guiding beliefs, standards, or ideals", quote)
    assert not is_verbatim_copy("Ethics guides professional conduct.", quote)


def test_verifier_rejects_point_copied_from_quote():
    chunk = next(c for c in _chunks() if c.deck.startswith("071")
                 and "Ethics is a suite" in c.text)
    text = normalize_text(chunk.text)
    quote = text[text.index("Ethics is a suite"):
                 text.index("Ethics is a suite") + 140]
    exp = [{"slot": "A1a", "marks": 1, "topic": "risk/management (ethics)",
            "task": "Explain", "dependent": False}]
    draft = _draft("A1a", "Explain the ethical basis of professional conduct.",
                   [{"point": quote, "quote": quote,
                     "chunk_id": chunk.chunk_id}])
    _, errors = verify_draft(draft, exp, [chunk])
    assert any("verbatim copy" in e for e in errors)
