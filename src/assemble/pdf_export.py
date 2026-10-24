"""PDF export with Word COM (Windows) or LibreOffice (Linux/container).

The local Windows workflow keeps Microsoft Word COM.  The live container
sets ``MOCKGEN_PDF_ENGINE=libreoffice`` (or runs on a non-Windows host) and
uses the LibreOffice headless converter already used by the scheme QA module.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from pypdf import PdfReader

from src.assemble.scheme_qa import find_soffice, libreoffice_pdf


def pdf_engine() -> str:
    value = os.environ.get("MOCKGEN_PDF_ENGINE", "").strip().lower()
    if value in {"word", "libreoffice"}:
        return value
    return "word" if os.name == "nt" else "libreoffice"


def _word_export(docx_path: Path, pdf_path: Path) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False,
                                     encoding="utf-8") as fh:
        fh.write(f"""
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$doc = $word.Documents.Open("{docx_path}", $false, $true)
$doc.SaveAs([ref]"{pdf_path}", [ref]17)
$doc.Close([ref]$false)
$word.Quit([ref]$false)
""")
        ps1 = Path(fh.name)
    try:
        subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy",
                        "Bypass", "-File", str(ps1)], capture_output=True,
                       timeout=300)
    finally:
        ps1.unlink(missing_ok=True)


def _libreoffice_export(docx_path: Path, pdf_path: Path) -> None:
    if find_soffice() is None:
        raise RuntimeError(
            "LibreOffice is not installed; set MOCKGEN_PDF_ENGINE=word on "
            "Windows or install libreoffice in the container")
    converted = libreoffice_pdf(docx_path, pdf_path.parent)
    if converted is None:
        raise RuntimeError("LibreOffice PDF export failed")
    if converted.resolve() != pdf_path.resolve():
        shutil.move(str(converted), str(pdf_path))


def export_pdf(docx_path: Path, pdf_path: Path) -> int:
    """Export ``docx_path`` to ``pdf_path`` and return the page count."""
    docx_path = Path(docx_path).resolve()
    pdf_path = Path(pdf_path).resolve()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.unlink(missing_ok=True)
    if pdf_engine() == "libreoffice":
        _libreoffice_export(docx_path, pdf_path)
    else:
        _word_export(docx_path, pdf_path)
    if not pdf_path.exists():
        raise RuntimeError(
            f"{pdf_engine()} PDF export failed for {docx_path.name}")
    return len(PdfReader(str(pdf_path)).pages)
