"""MAT406 V6 Library cache and manifest guards."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "outputs" / "web_cache" / "MAT406"
MANIFEST = CACHE / "manifest.json"


def _load(path: Path):
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def test_library_manifest_has_twelve_complete_seeds():
    manifest = _load(MANIFEST)
    if not manifest:
        pytest.skip("MAT406 Library is not built")
    assert manifest["counts"]["seeds"] == 12
    assert manifest["counts"]["qa_problems"] == 0
    assert manifest["counts"]["max_question_reuse"] <= 4
    assert manifest["seed_cap"] == 12
    for row in manifest["seeds"]:
        assert row["total_marks"] == 100
        assert len(row["questions"]) == 8
        assert not row["qa"]
        assert 6 <= row["distinct_papers"] <= 8
        assert row["paper_pages"] > 0 and row["scheme_pages"] > 0
        for key in ("paper_pdf", "scheme_pdf"):
            assert Path(row[key]).is_file()


def test_library_meta_uses_numeric_creation_time():
    manifest = _load(MANIFEST)
    if not manifest:
        pytest.skip("MAT406 Library is not built")
    for row in manifest["seeds"]:
        meta = _load(Path(row["path"]) / "meta.json")
        assert meta["subject"] == "MAT406"
        assert isinstance(meta["created"], (int, float))
        assert meta["year"] == 2026
        assert meta["files"]["paper_pdf"] == row["paper_pdf"]
        assert "2" in meta["document_versions"]


def test_library_plugin_cap_and_seed_list():
    from src.subjects.mat406.plugin import library_seeds, seed_cap
    assert seed_cap() == 12
    assert library_seeds() == list(range(1, 13))
