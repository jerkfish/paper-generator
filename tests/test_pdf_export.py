"""PDF engine selection for local (Word) and container (LibreOffice) builds."""
from __future__ import annotations

from src.assemble.pdf_export import pdf_engine


def test_explicit_pdf_engine(monkeypatch):
    monkeypatch.setenv("MOCKGEN_PDF_ENGINE", "libreoffice")
    assert pdf_engine() == "libreoffice"
    monkeypatch.setenv("MOCKGEN_PDF_ENGINE", "word")
    assert pdf_engine() == "word"


def test_auto_pdf_engine(monkeypatch):
    monkeypatch.delenv("MOCKGEN_PDF_ENGINE", raising=False)
    assert pdf_engine() in {"word", "libreoffice"}
