"""OCR helpers for scanned pages using the built-in Windows OCR engine.

The engine is invoked through PowerShell WinRT, so no additional packages are
needed.  Only used when a PDF page has no usable text layer.
"""
from __future__ import annotations

import os
import re
import subprocess
import tempfile
from collections.abc import Iterable
from pathlib import Path

import pymupdf

WIN_OCR_PS1 = r"""
param([string]$ImagePath)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Runtime.WindowsRuntime | Out-Null
[Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime] | Out-Null
[Windows.Storage.Streams.IRandomAccessStream,Windows.Storage.Streams,ContentType=WindowsRuntime] | Out-Null
[Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime] | Out-Null
[Windows.Media.Ocr.OcrResult,Windows.Foundation,ContentType=WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder,Windows.Foundation,ContentType=WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.SoftwareBitmap,Windows.Foundation,ContentType=WindowsRuntime] | Out-Null
[Windows.Globalization.Language,Windows.Foundation,ContentType=WindowsRuntime] | Out-Null
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
if ($null -eq $engine) {
    $lang = New-Object Windows.Globalization.Language "en-US"
    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang)
}
if ($null -eq $engine) { throw "No Windows OCR engine available" }
$file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($ImagePath)) ([Windows.Storage.StorageFile])
$stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
$decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
$bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
$result = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
$result.Text
"""


def page_images(pdf_path: Path, pages: Iterable[int] | None = None,
                dpi: int = 220) -> list[Path]:
    """Render selected pages (0-based) to temporary PNG files."""
    pdf_path = Path(pdf_path)
    doc = pymupdf.open(str(pdf_path))
    selected = list(range(len(doc))) if pages is None else list(pages)
    out: list[Path] = []
    tmpdir = Path(tempfile.mkdtemp(prefix="mat133_ocr_"))
    try:
        for index in selected:
            if index < 0 or index >= len(doc):
                continue
            page = doc[index]
            pix = page.get_pixmap(dpi=dpi, alpha=False)
            path = tmpdir / f"page_{index + 1:02d}.png"
            pix.save(str(path))
            out.append(path)
    finally:
        doc.close()
    return out


def win_ocr(image_path: Path) -> str:
    """Run Windows.Media.Ocr on one image."""
    fd, script_name = tempfile.mkstemp(prefix="win_ocr_", suffix=".ps1")
    os.close(fd)
    script = Path(script_name)
    try:
        script.write_text(WIN_OCR_PS1, encoding="utf-8")
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", str(script), str(Path(image_path).resolve())],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=120,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"Windows OCR failed: {proc.stderr.strip() or proc.stdout.strip()}")
        return proc.stdout.strip()
    finally:
        for _ in range(5):
            try:
                script.unlink(missing_ok=True)
                break
            except PermissionError:
                import time
                time.sleep(0.1)


def ocr_pdf(pdf_path: Path, pages: Iterable[int] | None = None,
            dpi: int = 220) -> str:
    """OCR selected pages and return the text in page order."""
    parts = []
    for image in page_images(pdf_path, pages=pages, dpi=dpi):
        parts.append(win_ocr(image))
        image.unlink(missing_ok=True)
    return "\n".join(parts)


_CID_OFFSET = 29


def decode_offset_text(text: str, force: bool = False) -> str:
    """Decode the +29 CID-shifted font encoding used by some UTM PDFs.

    Only applied when the raw text has many characters in the shifted range
    and almost no ordinary lowercase words; normal PDFs are returned as-is.
    """
    if not text:
        return text
    sample = text[:4000]
    letters = [c for c in sample if c.isprintable() and not c.isspace()]
    if not letters:
        return text
    shifted = sum(1 for c in letters if 32 <= ord(c) < 95) / len(letters)
    lowercase_words = len(re.findall(r"\b[a-z]{3,}\b", sample))
    if not force and (shifted < 0.8 or lowercase_words > 5):
        return text
    out = []
    for ch in text:
        code = ord(ch)
        if 32 <= code <= 94:
            out.append(chr(code + _CID_OFFSET))
        else:
            out.append(ch)
    return "".join(out)


MONTHS = ("JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE",
          "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER")


def normalize_month(value: str) -> str:
    text = value.upper().strip().replace(".", "")
    aliases = {"SEPT": "SEPTEMBER", "JUN": "JUNE", "JUL": "JULY"}
    return aliases.get(text, text)
