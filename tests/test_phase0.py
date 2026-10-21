"""Phase 0 safety: secret scan, public quote omission, path guards, bundle."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.app import jobs, safety
from src.assemble.build_docx_scheme_04 import quote_for_scheme
from scripts.public_bundle import build_manifest, errors


def test_secret_scan_detects_key_in_tracked_file(monkeypatch, tmp_path):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "super-secret-key-123")
    src = tmp_path / "src"
    src.mkdir()
    (src / "leak.py").write_text("KEY = 'super-secret-key-123'\n",
                                encoding="utf-8")
    with pytest.raises(safety.SecretLeakError) as exc:
        safety.assert_no_secret_leaks(tmp_path)
    assert "DEEPSEEK_API_KEY" in str(exc.value)
    assert "super-secret-key-123" not in str(exc.value)


def test_secret_scan_ignores_env_and_nontext(monkeypatch, tmp_path):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "super-secret-key-123")
    (tmp_path / ".env").write_text("DEEPSEEK_API_KEY=super-secret-key-123\n",
                                   encoding="utf-8")
    (tmp_path / "README.md").write_text("no keys here\n", encoding="utf-8")
    safety.assert_no_secret_leaks(tmp_path)


def test_public_scheme_omits_verbatim_quote():
    pt = {"quote": "This is a verbatim slide passage.",
          "point": "A point.", "stem_overlap": 0.8}
    assert "verbatim slide passage" not in quote_for_scheme(pt, public=True)
    assert "verbatim slide passage" in quote_for_scheme(pt, public=False)


def test_reference_paths_are_not_servable(tmp_path, monkeypatch):
    ref = tmp_path / "reference" / "crest.png"
    ref.parent.mkdir()
    ref.write_bytes(b"crest")
    allowed = tmp_path / "cache"
    allowed.mkdir()
    ok = allowed / "paper.pdf"
    ok.write_bytes(b"pdf")
    monkeypatch.setattr(safety.config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(safety.config, "WEB_CACHE_DIR", allowed)
    monkeypatch.setattr(safety.config, "WEB_RUNS_DIR", tmp_path / "runs")
    assert safety.is_forbidden_path(ref)
    assert not safety.is_servable_path(ref)
    assert safety.is_servable_path(ok)
    with pytest.raises(safety.ForbiddenPathError):
        safety.ensure_servable(ref)


def test_public_bundle_has_no_forbidden_paths():
    entries = build_manifest()
    assert entries
    assert errors(entries) == []
    assert not any("data/reference" in e["path"] for e in entries)
    assert any(e["path"].startswith("library/schemes/") for e in entries)


def test_job_download_refuses_reference_file(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    from src.app import main
    from src.app.jobs import Job, manager

    ref = tmp_path / "reference" / "template.docx"
    ref.parent.mkdir()
    ref.write_bytes(b"template")
    monkeypatch.setattr(safety.config, "DATA_DIR", tmp_path)
    job = Job(id="phase0test", mode="realistic", seed=1, computed_marks=None)
    job.files = {"paper_docx": str(ref)}
    manager._jobs[job.id] = job
    try:
        client = TestClient(main.app)
        resp = client.get("/downloads/phase0test/paper_docx")
    finally:
        manager._jobs.pop(job.id, None)
    assert resp.status_code == 403


def test_public_build_disables_library(monkeypatch):
    monkeypatch.setattr(jobs.config, "PUBLIC_BUILD", True)
    assert jobs.library_items() == []
    assert jobs.library_file(1, "paper_pdf") is None
    assert jobs.library_file(1, "scheme_docx") is None
