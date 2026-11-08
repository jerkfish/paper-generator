"""MinerU client and normalizer tests (no network calls)."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import httpx
import pymupdf
import pytest

from src.subjects.parsers import mineru_client, mineru_normalize


def _options(model="pipeline"):
    return mineru_client.MineruOptions(model_version=model)


def test_cache_hit_makes_no_call(tmp_path, monkeypatch):
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    tracking = tmp_path / "tracking"
    options = _options()
    digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
    cache = tracking / "mineru" / "PAPER" / f"pipeline_{options.fingerprint()}"
    cache.mkdir(parents=True)
    (cache / "result.zip").write_bytes(b"zip")
    (cache / "manifest.json").write_text(json.dumps({
        "sha256": digest, "model_version": "pipeline", "zip": str(cache / "result.zip")
    }), encoding="utf-8")
    client = mineru_client.MineruClient(
        mineru_client.MineruConfig(api_key="test-key"))
    monkeypatch.setattr(client, "_request", lambda *a, **k: pytest.fail("network call"))
    result = client.parse(code="CSC413", paper_path=pdf, paper_id="PAPER",
                          page_count=1, options=options, tracking=tracking)
    assert result["cached"] is True
    client.close()


def test_safe_extract_keeps_full_tree(tmp_path):
    archive = tmp_path / "result.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("full.md", "# full")
        zf.writestr("content_list.json", "[]")
        zf.writestr("layout/middle.json", "{}")
        zf.writestr("images/figure.png", b"png")
    names = mineru_client._safe_extract(archive, tmp_path / "out")
    assert "full.md" in names
    assert "images/figure.png" in names
    assert (tmp_path / "out" / "layout" / "middle.json").is_file()


def test_auth_and_quota_errors_are_clear(monkeypatch):
    client = mineru_client.MineruClient(
        mineru_client.MineruConfig(api_key="test-key"))
    def fake_401(*args, **kwargs):
        return httpx.Response(401, request=httpx.Request("GET", "https://x"))
    monkeypatch.setattr(client._client, "request", fake_401)
    with pytest.raises(mineru_client.MineruAuthError):
        client._request("GET", "https://x")
    def fake_429(*args, **kwargs):
        return httpx.Response(429, request=httpx.Request("GET", "https://x"))
    monkeypatch.setattr(client._client, "request", fake_429)
    with pytest.raises(mineru_client.MineruQuotaError):
        client._request("GET", "https://x")
    client.close()


def _pdf(path: Path):
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((40, 80), "QUESTION 1")
    page.insert_text((40, 120), "Explain the figure. (5 marks)")
    doc.save(str(path))
    doc.close()


def test_normalizer_links_figure_by_caption(tmp_path):
    pdf = tmp_path / "paper.pdf"
    _pdf(pdf)
    cache = tmp_path / "cache"
    cache.mkdir()
    blocks = [
        {"type": "text", "page_idx": 0, "bbox": [10, 10, 500, 30],
         "text": "QUESTION 1 Explain the figure. (5 marks)"},
        {"type": "text", "page_idx": 0, "bbox": [10, 40, 500, 60],
         "text": "Refer to Figure 2."},
        {"type": "image", "page_idx": 0, "bbox": [10, 100, 300, 300],
         "img_path": "images/f2.png", "image_caption": ["Figure 2: test"]},
    ]
    (cache / "content_list.json").write_text(json.dumps(blocks), encoding="utf-8")
    # MinerU also writes a per-page V2 list; the normalizer must use V1.
    (cache / "paper_content_list_v2.json").write_text(
        json.dumps([[{"type": "text", "page_idx": 0}]]), encoding="utf-8")
    out = cache / "review"
    result = mineru_normalize.normalize(
        paper_id="CSC413-TEST", pdf_path=pdf, cache_dir=cache,
        model="pipeline", out_dir=out)
    assert result["counts"]["questions"] == 1
    assert result["counts"]["figures"] == 1
    assert result["counts"]["resolved_references"] == 1
    assert result["counts"]["fallback_assets"] == 0
    assert result["questions"][0]["assets"]


def test_fallback_triggers_for_missing_asset_and_preserves_files(tmp_path):
    pdf = tmp_path / "paper.pdf"
    _pdf(pdf)
    cache = tmp_path / "cache"
    cache.mkdir()
    blocks = [
        {"type": "text", "page_idx": 0, "bbox": [10, 10, 500, 30],
         "text": "QUESTION 1 See Figure 3. (5 marks)"},
    ]
    (cache / "content_list.json").write_text(json.dumps(blocks), encoding="utf-8")
    out = cache / "review"
    out.mkdir()
    corrections = out / "corrections.json"
    approvals = out / "approvals.json"
    corrections.write_text('{"sentinel": true}', encoding="utf-8")
    approvals.write_text('{"sentinel": true}', encoding="utf-8")
    result = mineru_normalize.normalize(
        paper_id="CSC413-TEST", pdf_path=pdf, cache_dir=cache,
        model="pipeline", out_dir=out)
    assert result["counts"]["fallback_assets"] == 1
    assert corrections.read_text(encoding="utf-8") == '{"sentinel": true}'
    assert approvals.read_text(encoding="utf-8") == '{"sentinel": true}'


def test_upload_uses_client_without_api_auth_header(monkeypatch):
    client = mineru_client.MineruClient(
        mineru_client.MineruConfig(api_key="test-key"))
    assert "authorization" not in {
        key.lower() for key in client._upload_client.headers}
    calls = []

    def fake_upload(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return httpx.Response(200, request=httpx.Request(method, url))

    def fail_api(*args, **kwargs):
        pytest.fail("upload must not use the authenticated API client")

    monkeypatch.setattr(client._upload_client, "request", fake_upload)
    monkeypatch.setattr(client._client, "request", fail_api)
    client._request("PUT", "https://oss.example/upload", with_auth=False,
                    content=b"pdf")
    assert calls and calls[0][0] == "PUT"
    assert "headers" not in calls[0][2]
    client.close()


def test_upload_403_is_not_reported_as_api_key_error(monkeypatch):
    client = mineru_client.MineruClient(
        mineru_client.MineruConfig(api_key="test-key"))

    def fake_upload(method, url, **kwargs):
        return httpx.Response(403, request=httpx.Request(method, url),
                              text="SignatureDoesNotMatch")

    monkeypatch.setattr(client._upload_client, "request", fake_upload)
    with pytest.raises(mineru_client.MineruError) as caught:
        client._request("PUT", "https://oss.example/upload", with_auth=False,
                        content=b"pdf")
    assert not isinstance(caught.value, mineru_client.MineruAuthError)
    assert "upload" in str(caught.value).lower()
    client.close()


def test_permission_denied_never_calls_api(tmp_path, monkeypatch):
    from src.subjects.parsers import mineru_pilot
    monkeypatch.setattr(mineru_pilot, "REPORT", tmp_path / "pilot_report.json")
    monkeypatch.setattr(mineru_pilot, "REPORT_MD", tmp_path / "PILOT_REPORT.md")
    monkeypatch.setattr(mineru_pilot, "_permission",
                        lambda: (False, {}, [{"source": "x.pdf"}]))
    result = mineru_pilot.run()
    assert result["status"] == "blocked_permission"
    assert result["excluded_files"]
    assert (tmp_path / "pilot_report.json").is_file()
