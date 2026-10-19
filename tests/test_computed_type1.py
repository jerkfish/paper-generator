"""Computed type #1 generator tests: key parsing, answer/ciphertext roles,
verifier rules (no LLM calls involved)."""
from __future__ import annotations

import pytest

from src.generators.computed_type1 import (DraftQuestion, answer, ciphertext,
                                           render_question, verify)


def _q(**kw) -> DraftQuestion:
    defaults = {"cipher": "caesar", "plaintext": "TRUSTED", "key": "shift=4",
                "task": "encrypt", "marks": 2}
    defaults.update(kw)
    return DraftQuestion(**defaults)


def test_decrypt_question_shows_ciphertext_and_readable_answer():
    q = _q(task="decrypt")
    assert ciphertext(q) != q.plaintext
    assert answer(q) == "TRUSTED"
    assert ciphertext(q) in render_question(q)
    assert q.plaintext not in render_question(q)


def test_encrypt_question_answer_is_ciphertext():
    q = _q()
    assert answer(q) == ciphertext(q)


def test_verifier_rejects_bad_marks():
    assert verify(_q(marks=3), [])[0].startswith("marks")


def test_verifier_rejects_non_coprime_affine():
    assert verify(_q(cipher="affine", key="(2,5)"), [])[0].startswith("affine key")


def test_verifier_rejects_meaningless_plaintext():
    q = _q(plaintext="X ZQK LPDK")
    assert any("meaningful" in p for p in verify(q, []))


def test_verifier_rejects_near_copy():
    q = _q()
    pool = ["TRUSTEDX"]  # near-identical plaintext content used before
    assert any("near-copy" in p or "already used" in p for p in verify(q, pool))


def test_verifier_allows_same_template_different_content():
    # the template stems are identical by design - only content must differ
    q = _q(plaintext="THIS IS SECRET")
    pool = ["USINGCAESARCIPHERTECHNIQUEENCRYPTTHEFOLLOWINGPLAINTEXTWITH"
            "SHIFT7SOMEOLDTEXT"]
    assert verify(q, pool) == []


def test_verifier_allows_partial_overlap():
    # "TRUSTED" sharing a prefix with an old "TRUSTEDSHIFT" is not a near-copy
    q = _q(plaintext="TRUSTED CORE")
    assert verify(q, ["TRUSTEDSHIFTOLDTOKEN"]) == []


def test_verifier_accepts_good_question():
    assert verify(_q(plaintext="THIS IS SECRET"), []) == []


def test_vernam_short_key_rejected():
    q = _q(cipher="vernam", key="3 6 12")
    assert any("vernam" in p for p in verify(q, []))
