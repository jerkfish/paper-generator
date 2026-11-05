"""CSC429 page capture and layout tests on synthetic papers."""
from __future__ import annotations

import hashlib
import json

import pymupdf

from src.subjects.csc429 import capture, layout


def _make_pdf(path):
    document = pymupdf.open()
    page = document.new_page(width=595, height=842)
    page.insert_text((72, 90), "QUESTION 1", fontsize=14)
    page.insert_text((72, 140), "Figure 1: Test diagram.", fontsize=11)
    page2 = document.new_page(width=595, height=842)
    page2.insert_text((72, 90), "QUESTION 2", fontsize=14)
    document.save(str(path))
    document.close()


def _register(path, rows):
    path.write_text(json.dumps(rows), encoding="utf-8")


def test_capture_renders_unique_pages_and_skips_duplicates(tmp_path, monkeypatch):
    papers = tmp_path / "papers"
    papers.mkdir()
    _make_pdf(papers / "paper.pdf")
    _make_pdf(papers / "duplicate.pdf")
    before = hashlib.sha256((papers / "paper.pdf").read_bytes()).hexdigest()
    register = tmp_path / "papers_register.json"
    _register(register, [
        {"source": "paper.pdf", "month": "JANUARY", "year": 2024,
         "source_kind": "text", "duplicate_of": ""},
        {"source": "duplicate.pdf", "month": "JANUARY", "year": 2024,
         "source_kind": "text", "duplicate_of": "paper.pdf"},
    ])
    monkeypatch.setattr(capture, "PAPERS", papers)
    monkeypatch.setattr(capture, "REGISTER", register)
    monkeypatch.setattr(capture, "PAGES_DIR", tmp_path / "pages")
    monkeypatch.setattr(capture, "MANIFEST", tmp_path / "pages_manifest.json")
    monkeypatch.setattr(capture.config, "PROJECT_ROOT", tmp_path)
    summary = capture.capture_pages(dpi=100, force=True)
    assert summary["papers"] == 1
    assert summary["pages"] == 2
    manifest = json.loads(
        (tmp_path / "pages" / "CSC429-2024-01" / "manifest.json")
        .read_text(encoding="utf-8"))
    assert manifest["page_count"] == 2
    assert len(list((tmp_path / "pages" / "CSC429-2024-01").glob("*.jpg"))) == 2
    after = hashlib.sha256((papers / "paper.pdf").read_bytes()).hexdigest()
    assert before == after


def test_layout_keeps_text_boxes_and_captions(tmp_path, monkeypatch):
    papers = tmp_path / "papers"
    papers.mkdir()
    _make_pdf(papers / "paper.pdf")
    register = tmp_path / "papers_register.json"
    _register(register, [
        {"source": "paper.pdf", "month": "JANUARY", "year": 2024,
         "source_kind": "text", "duplicate_of": ""},
    ])
    monkeypatch.setattr(capture, "PAPERS", papers)
    monkeypatch.setattr(capture, "REGISTER", register)
    monkeypatch.setattr(capture, "PAGES_DIR", tmp_path / "pages")
    monkeypatch.setattr(capture, "MANIFEST", tmp_path / "pages_manifest.json")
    monkeypatch.setattr(capture.config, "PROJECT_ROOT", tmp_path)
    capture.capture_pages(dpi=100, force=True)
    monkeypatch.setattr(layout, "PAPERS", papers)
    monkeypatch.setattr(layout, "REGISTER", register)
    monkeypatch.setattr(layout, "PAGES", tmp_path / "pages")
    monkeypatch.setattr(layout, "LAYOUT", tmp_path / "layout")
    monkeypatch.setattr(layout, "TRACKING", tmp_path)
    monkeypatch.setattr(layout.config, "PROJECT_ROOT", tmp_path)
    summary = layout.build_layout(force=True)
    assert summary["papers"] == 1
    assert summary["pages"] == 2
    assert summary["lines"] >= 2
    payload = json.loads(
        (tmp_path / "layout" / "CSC429-2024-01.json")
        .read_text(encoding="utf-8"))
    texts = [line["text"] for page in payload["pages"]
             for line in page["lines"]]
    assert any("QUESTION 1" in text for text in texts)
    assert any("Figure 1" in text for text in texts)
    assert payload["caption_lines"] >= 1
    for page in payload["pages"]:
        for line in page["lines"]:
            x0, y0, x1, y1 = line["bbox"]
            assert 0 <= x0 < x1 <= page["width"]
            assert 0 <= y0 < y1 <= page["height"]
