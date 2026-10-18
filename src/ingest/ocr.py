"""OCR helpers for scanned pages via the Windows built-in OCR engine (WinRT).

The engine is invoked through PowerShell - no extra packages or installs.
Only used when a PDF has no usable text layer.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys
import tempfile
from collections.abc import Sequence

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
if ($null -eq $engine) { Write-Output "OCR_ENGINE_UNAVAILABLE"; exit 1 }
$file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($ImagePath)) ([Windows.Storage.StorageFile])
$stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
$decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
$bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
$result = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
Write-Output $result.Text
"""


def win_ocr(image_path: str) -> str:
    """OCR one image file. Returns "" if the engine is unavailable or fails."""
    if not sys.platform.startswith("win"):
        return ""
    with tempfile.TemporaryDirectory() as td:
        ps1 = pathlib.Path(td) / "ocr.ps1"
        ps1.write_text(WIN_OCR_PS1, encoding="utf-8")
        try:
            proc = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", str(ps1), image_path],
                capture_output=True, timeout=120,
            )
        except Exception:
            return ""
        # PowerShell console output is not UTF-8 - decode leniently.
        return proc.stdout.decode("utf-8", errors="replace").strip().lstrip("﻿")


def page_images(page) -> list:
    """All embedded images on a PDF page, decoded with Pillow."""
    return [im.image for im in page.images if im.image is not None]


def stitch_images(imgs) -> "object | None":
    """Stitch same-width images vertically (strip-scanned pages). None if not
    applicable. Only strip-shaped images qualify - portrait page images are
    often duplicated in the PDF (color + mask), and stitching those would
    duplicate the content."""
    from PIL import Image

    if len(imgs) < 2 or len({im.width for im in imgs}) > 2:
        return None
    if not all(im.height < im.width for im in imgs):  # not strip-shaped
        return None
    width = max(im.width for im in imgs)
    height = sum(im.height for im in imgs)
    canvas = Image.new("RGB", (width, height), "white")
    y = 0
    for im in imgs:
        canvas.paste(im.convert("RGB"), (0, y))
        y += im.height
    return canvas


def score_text(text: str, markers: Sequence[re.Pattern]) -> int:
    """Prefer long text that contains expected markers (right way up)."""
    if not text:
        return 0
    s = len(text)
    for marker in markers:
        if marker.search(text):
            s += 300
    return s


def ocr_page(page, markers: Sequence[re.Pattern]) -> str:
    """OCR a PDF page, trying rotations and stitched strips. Best-scoring text."""
    from PIL import Image

    imgs = page_images(page)
    if not imgs:
        return ""
    variants: list = list(imgs)
    stitched = stitch_images(imgs)
    if stitched is not None:
        variants.append(stitched)

    best_text, best_score = "", 0
    with tempfile.TemporaryDirectory() as td:
        for i, im in enumerate(variants):
            base = pathlib.Path(td) / f"v{i}.png"
            im.convert("RGB").save(base)
            text = win_ocr(str(base))
            s = score_text(text, markers)
            if s > best_score:
                best_text, best_score = text, s
            if s < 400:  # weak signal - page may be stored rotated
                for angle in (90, 180, 270):
                    rp = pathlib.Path(td) / f"v{i}-r{angle}.png"
                    Image.open(base).rotate(angle, expand=True).save(rp)
                    text = win_ocr(str(rp))
                    s = score_text(text, markers)
                    if s > best_score:
                        best_text, best_score = text, s
    return best_text


def ocr_pdf(path: pathlib.Path, markers: Sequence[re.Pattern],
            cache_path: pathlib.Path | None = None,
            log=print) -> str:
    """OCR every page of a scanned PDF; optionally cache the result."""
    from pypdf import PdfReader

    if cache_path and cache_path.exists():
        log(f"    (using OCR cache {cache_path.name})")
        return cache_path.read_text(encoding="utf-8")

    reader = PdfReader(str(path))
    parts = []
    for i, page in enumerate(reader.pages):
        log(f"    OCR page {i + 1}/{len(reader.pages)}")
        parts.append(f"===== PAGE {i + 1} =====\n" + ocr_page(page, markers))
    text = "\n".join(parts)
    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(text, encoding="utf-8")
    return text
