"""Public bundle subject filtering and paper-count text."""
from __future__ import annotations

import json

from src.subjects.registry import Subject


def test_mat133_library_is_twenty_seeds():
    from src.subjects.mat133.plugin import library_seeds

    assert library_seeds() == list(range(1, 21))


def test_public_subjects_excludes_unpublished(monkeypatch):
    from scripts import build_public_bundle as bundle

    published = Subject(
        code="PUB", title="Published", status="available",
        permissions={"publication": {"allowed": True}})
    unpublished = Subject(
        code="PRIV", title="Private", status="available",
        permissions={"publication": {"allowed": False}})
    stub = Subject(code="STUB", title="Stub", status="coming_soon")
    monkeypatch.setattr(bundle, "load_subjects", lambda: {
        "PUB": published, "PRIV": unpublished, "STUB": stub})

    assert [s.code for s in bundle._public_subjects()] == ["PUB", "STUB"]


def test_bundle_count_reads_existing_manifest(tmp_path):
    from scripts import build_public_bundle as bundle

    manifest = tmp_path / "library" / "MAT133" / "manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"count": 20}), encoding="utf-8")

    assert bundle._bundle_count(tmp_path, "MAT133", 0) == 20
    assert bundle._bundle_count(tmp_path, "MAT133", 7) == 7
    assert bundle._bundle_count(tmp_path, "CSC662", 0) == 0
