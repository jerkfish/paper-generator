"""Phase 1: subject registry, download names and subject-scoped pages."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.app import jobs, main
from src.app.filenames import (content_disposition, download_filename,
                               utc_year)
from src.subjects.registry import get_subject, load_subjects


def test_registry_discovers_csc662_and_stubs():
    subjects = load_subjects()
    assert list(subjects)[0] == "CSC662"
    assert subjects["CSC662"].available
    assert subjects["CSC662"].enabled_computed_generators
    assert subjects["CSC662"].topic_deck_allowlist
    for code in ("CSC580", "CSC645"):
        assert subjects[code].status == "coming_soon"
        assert subjects[code].available is False
        assert subjects[code].enabled_computed_generators == []
    assert get_subject("csc662").code == "CSC662"


def test_public_subject_dict_hides_internal_paths():
    public = get_subject("CSC662").public_dict()
    assert public["code"] == "CSC662"
    assert "template_path" not in public
    assert "deck_map" not in public
    assert "topic_deck_allowlist" not in public


def test_download_names_cover_unusual_seeds():
    assert (download_filename("CSC662", 7, 2026, "pdf")
            == "CSC662 Seed 07 2026.pdf")
    assert (download_filename("CSC662", 12345, 2026, "docx")
            == "CSC662 Seed 12345 2026.docx")
    assert (download_filename("CSC662", 7, 2026, "pdf", scheme=True)
            == "CSC662 Seed 07 2026 - Marking Scheme.pdf")
    assert (download_filename("CSC662", 7, 2026, "pdf", practice_marks=14)
            == "CSC662 Seed 07 2026 (practice 14).pdf")
    assert (download_filename("CSC662", 7, 2026, "docx", scheme=True,
                              practice_marks=0)
            == "CSC662 Seed 07 2026 - Marking Scheme (practice 0).docx")
    with pytest.raises(ValueError):
        download_filename("CSC662", 0, 2026, "pdf")
    with pytest.raises(ValueError):
        download_filename("CSC662", 7, 2026, "exe")


def test_content_disposition_has_ascii_and_rfc5987_forms():
    header = content_disposition(download_filename("CSC662", 7, 2026, "pdf"))
    assert 'filename="CSC662 Seed 07 2026.pdf"' in header
    assert "filename*=UTF-8''CSC662%20Seed%2007%202026.pdf" in header


def test_utc_year_boundary():
    assert utc_year(1767225599) == 2025  # 2025-12-31 23:59:59 UTC
    assert utc_year(1767225600) == 2026  # 2026-01-01 00:00:00 UTC


def test_cache_key_is_subject_specific(monkeypatch, tmp_path):
    monkeypatch.setattr(jobs.config, "WEB_CACHE_DIR", tmp_path / "cache")
    a = jobs.cache_path("realistic", 7, None, subject="CSC662")
    b = jobs.cache_path("realistic", 7, None, subject="CSC580")
    assert a.parent.name == "CSC662"
    assert b.parent.name == "CSC580"
    assert a.name != b.name


def test_subject_pages_and_coming_soon(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    monkeypatch.setattr(jobs.config, "WEB_CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(jobs.config, "OUTPUTS_DIR", tmp_path)
    client = TestClient(main.app)
    assert client.get("/").status_code == 200
    assert client.get("/csc662").status_code == 200
    assert client.get("/csc662/library").status_code == 200
    assert client.get("/csc662/generate").status_code == 200
    assert client.get("/csc580").status_code == 200
    assert client.get("/csc580/library").status_code == 404
    assert client.get("/missing").status_code == 404


def test_library_download_uses_pretty_name(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    monkeypatch.setattr(jobs.config, "WEB_CACHE_DIR", tmp_path / "cache")
    out = jobs.cache_path("practice", 7, 14, subject="CSC662")
    out.mkdir(parents=True)
    paper = out / "paper.pdf"
    paper.write_bytes(b"%PDF-fake")
    (out / "meta.json").write_text(json.dumps({
        "subject": "CSC662", "seed": 7, "mode": "practice",
        "computed_marks": 14, "created": 1767225600, "year": 2026,
        "accepted": 20, "placeholders": 0, "model": "fake",
        "files": {"paper_pdf": str(paper)},
        "summary": {}, "progress": [],
    }), encoding="utf-8")
    client = TestClient(main.app)
    resp = client.get("/csc662/library/7/paper_pdf")
    assert resp.status_code == 200
    header = resp.headers["content-disposition"]
    assert 'filename="CSC662 Seed 07 2026 (practice 14).pdf"' in header
    assert "practice%2014" in header


def test_library_filter_by_computed_topic_and_placeholders():
    items = [
        {"seed": 1, "mode": "realistic", "computed_display": 0,
         "topic_marks": {"attacks/malware": 24}, "topic_mix": "ATK 24",
         "placeholders": 0},
        {"seed": 2, "mode": "realistic", "computed_display": 6,
         "topic_marks": {"classical ciphers": 6}, "topic_mix": "CIP 6",
         "placeholders": 2},
    ]
    assert [i["seed"] for i in jobs.filter_library(items, computed="6")] == [2]
    assert [i["seed"] for i in jobs.filter_library(
        items, topic="attacks/malware")] == [1]
    assert [i["seed"] for i in jobs.filter_library(
        items, placeholders="1+")] == [2]
    assert [i["seed"] for i in jobs.filter_library(items, q="cip")] == [2]


def test_r2_quota_guard_and_incremental_plan(tmp_path):
    from scripts import r2_sync
    bundle = tmp_path / "bundle"
    (bundle / "library").mkdir(parents=True)
    (bundle / "index.html").write_text("home", encoding="utf-8")
    (bundle / "library" / "paper.pdf").write_bytes(b"%PDF")
    files = r2_sync.bundle_files(bundle)
    assert [f["key"] for f in files] == ["index.html", "library/paper.pdf"]
    est = r2_sync.estimate(files)
    assert est == {"objects": 2, "bytes": 8}
    assert r2_sync.quota_errors(est, r2_sync._fresh_ledger()) == []
    too_big = {"objects": r2_sync.MAX_OBJECTS + 1,
               "bytes": r2_sync.MAX_STORAGE_BYTES + 1}
    assert len(r2_sync.quota_errors(too_big, r2_sync._fresh_ledger())) == 2
    over_ledger = {"month": r2_sync._month(),
                   "class_a": r2_sync.MAX_CLASS_A + 1,
                   "class_b": r2_sync.MAX_CLASS_B + 1}
    assert len(r2_sync.quota_errors(est, over_ledger)) == 2
    state = {"objects": {files[0]["key"]: {"sha256": files[0]["sha256"]}}}
    row = r2_sync.plan(files, state, upload=True)
    assert len(row["changed"]) == 1
    assert row["unchanged"] == 1
    assert row["class_a"] == 2  # one LIST + one PUT


def test_job_download_name_and_subject_guard(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    from src.app.jobs import Job, manager

    runs = tmp_path / "runs"
    monkeypatch.setattr(jobs.config, "WEB_RUNS_DIR", runs)
    monkeypatch.setattr(jobs.config, "WEB_CACHE_DIR", tmp_path / "cache")
    path = runs / "phase1job" / "paper.pdf"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"%PDF")
    job = Job(id="phase1job", mode="practice", seed=7, computed_marks=14,
              subject="CSC662", year=2026)
    job.files = {"paper_pdf": str(path)}
    manager._jobs[job.id] = job
    try:
        client = TestClient(main.app)
        resp = client.get("/csc662/downloads/phase1job/paper_pdf")
        assert resp.status_code == 200
        assert ('filename="CSC662 Seed 07 2026 (practice 14).pdf"'
                in resp.headers["content-disposition"])
        # A job cannot be downloaded through another subject's route.
        assert client.get(
            "/csc580/downloads/phase1job/paper_pdf").status_code == 404
    finally:
        manager._jobs.pop(job.id, None)


def test_coming_soon_subject_cannot_generate(monkeypatch):
    manager = jobs.JobManager()
    with pytest.raises(ValueError, match="coming soon"):
        manager.create("realistic", 7, None, subject="CSC580")


def test_migration_copies_flat_cache(monkeypatch, tmp_path):
    from scripts.migrate_cache_subjects import migrate
    root = tmp_path / "cache"
    old = root / "oldhash"
    old.mkdir(parents=True)
    paper = old / "paper.pdf"
    paper.write_bytes(b"%PDF")
    (old / "meta.json").write_text(json.dumps({
        "seed": 7, "mode": "realistic", "computed_marks": None,
        "created": 1767225600, "accepted": 1, "placeholders": 0,
        "files": {"paper_pdf": str(paper)}, "summary": {}, "progress": [],
    }), encoding="utf-8")
    monkeypatch.setattr(jobs.config, "WEB_CACHE_DIR", root)
    monkeypatch.setattr(jobs.config, "OUTPUTS_DIR", tmp_path)
    rows = migrate(root)
    assert len(rows) == 1
    new = jobs.cache_path("realistic", 7, None, subject="CSC662")
    meta = json.loads((new / "meta.json").read_text(encoding="utf-8"))
    assert meta["subject"] == "CSC662"
    assert meta["files"]["paper_pdf"] == str(new / "paper.pdf")
    assert (new / "paper.pdf").exists()
    assert old.exists()  # copy, not move


def test_generate_route_renders_cached_job(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    monkeypatch.setattr(jobs.config, "WEB_CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(jobs.config, "WEB_RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(jobs.config, "OUTPUTS_DIR", tmp_path)
    out = jobs.cache_path("realistic", 7, None, subject="CSC662")
    out.mkdir(parents=True)
    paper = out / "paper.pdf"
    paper.write_bytes(b"%PDF")
    (out / "meta.json").write_text(json.dumps({
        "subject": "CSC662", "seed": 7, "mode": "realistic",
        "computed_marks": None, "created": 1767225600, "year": 2026,
        "accepted": 22, "placeholders": 0, "model": "fake",
        "files": {"paper_pdf": str(paper)}, "summary": {}, "progress": [],
    }), encoding="utf-8")
    client = TestClient(main.app)
    resp = client.post("/csc662/generate",
                       data={"mode": "realistic", "seed": "7",
                             "computed_marks": ""})
    assert resp.status_code == 200
    assert "DONE" in resp.text
    assert "CSC662 Seed 07 2026.pdf" in resp.text
    assert "/csc662/downloads/" in resp.text


def test_r2_remote_state_detects_missing_and_changed_objects():
    from scripts import r2_sync
    files = [{"key": "a.pdf", "size": 4, "sha256": "abc"},
             {"key": "b.pdf", "size": 4, "sha256": "def"}]
    state = {"objects": {"a.pdf": {"size": 4, "sha256": "abc",
                                   "etag": "e1"},
                         "b.pdf": {"size": 4, "sha256": "def",
                                   "etag": "old"}}}
    remote = {"a.pdf": {"size": 4, "etag": "e1"},
              "b.pdf": {"size": 4, "etag": "new"}}
    changed = r2_sync._changed_after_listing(files, state, remote)
    assert [f["key"] for f in changed] == ["b.pdf"]
    assert [f["key"] for f in r2_sync._changed_after_listing(
        files, state, {})] == ["a.pdf", "b.pdf"]
