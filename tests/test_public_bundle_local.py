"""Local-only public bundle builds do not change publication permission."""
from __future__ import annotations

from src.subjects.registry import get_subject
from scripts.build_public_bundle import _public_subjects


def test_local_only_includes_available_but_unpublished_subject():
    assert get_subject("CSC429").available
    assert "CSC429" not in {s.code for s in _public_subjects(local_only=False)}
    assert "CSC429" in {s.code for s in _public_subjects(local_only=True)}
