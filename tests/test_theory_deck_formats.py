"""Lecture decks can be PPTX, PDF or Markdown."""
from __future__ import annotations

import pymupdf

from src.theory.decks import extract_chunks

TEXT = ("Database design and development covers conceptual design, "
        "entity relationship diagrams, normalization and SQL.")


def test_extract_chunks_from_pdf(tmp_path):
    path = tmp_path / "database.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((40, 80), TEXT)
    doc.save(str(path))
    doc.close()
    chunks = extract_chunks(tmp_path)
    assert chunks
    assert chunks[0].deck == "database"
    assert chunks[0].slide == 1
    assert "Database design" in chunks[0].text


def test_extract_chunks_from_markdown(tmp_path):
    path = tmp_path / "database.md"
    path.write_text("# Database\n\n## Slide one\n" + TEXT,
                    encoding="utf-8")
    chunks = extract_chunks(tmp_path)
    assert chunks
    assert chunks[0].deck == "database"
    assert chunks[0].slide >= 1
    assert "Database design" in chunks[0].text


def test_markdown_is_skipped_when_pdf_with_same_stem_exists(tmp_path):
    pdf = tmp_path / "database.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((40, 80), TEXT)
    doc.save(str(pdf))
    doc.close()
    (tmp_path / "database.md").write_text("# Different copy\n" + TEXT,
                                          encoding="utf-8")
    chunks = extract_chunks(tmp_path)
    assert chunks
    assert all("Different copy" not in chunk.text for chunk in chunks)
