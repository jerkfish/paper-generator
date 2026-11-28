#!/usr/bin/env python3
"""PERMATA (UiTM) exam-paper downloader.

Flow per subject code:
  1. Log in to permata.uitm.edu.my with an iStudent account.
  2. Page through the EXAM PAPER search results and keep records whose
     catalogue title contains the exact code, e.g. "(ICT502)".
  3. Read each record page, extract the "Muat Turun" POST form.
  4. POST it to digitallibrary.uitm.edu.my, which streams the PDF.
  5. OCR the first page (Windows built-in OCR) and rename the file to
     "<CODE> <MONTH> <YEAR>.pdf" (e.g. ICT502 JUNE 2018.pdf).

Usage:
  python permata_downloader.py ICT502 ICT552 --out .
  python permata_downloader.py ICT502 --dry-run
  python permata_downloader.py --subjects-file subjects.txt
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlencode

import requests
from bs4 import BeautifulSoup

BASE = "https://permata.uitm.edu.my"
SEARCH_URL = f"{BASE}/page/page.php"
LOGIN_URL = f"{BASE}/login_istudent.php"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36"
)

MONTHS = {
    "JANUARY": "JANUARY", "JANUARI": "JANUARY", "JAN": "JANUARY",
    "FEBRUARY": "FEBRUARY", "FEBRUARI": "FEBRUARY", "FEB": "FEBRUARY",
    "MARCH": "MARCH", "MAC": "MARCH", "MAR": "MARCH",
    "APRIL": "APRIL", "APR": "APRIL",
    "MAY": "MAY", "MEI": "MAY",
    "JUNE": "JUNE", "JUN": "JUNE",
    "JULY": "JULY", "JULAI": "JULY", "JUL": "JULY",
    "AUGUST": "AUGUST", "OGOS": "AUGUST", "AUG": "AUGUST",
    "SEPTEMBER": "SEPTEMBER", "SEPT": "SEPTEMBER", "SEP": "SEPTEMBER",
    "OCTOBER": "OCTOBER", "OKTOBER": "OCTOBER", "OCT": "OCTOBER",
    "NOVEMBER": "NOVEMBER", "NOV": "NOVEMBER",
    "DECEMBER": "DECEMBER", "DISEMBER": "DECEMBER", "DEC": "DECEMBER",
}
_MONTH_RE = re.compile(
    r"\b(" + "|".join(sorted(MONTHS, key=len, reverse=True)) + r")\b"
    r"[\s.,/\-]*([0-9OIl]{4})\b",
    re.I,
)

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


@dataclass
class Hit:
    recordno: str
    title: str
    url: str


@dataclass
class Record:
    hit: Hit
    meta: dict[str, str] = field(default_factory=dict)
    action: str = ""
    form_data: dict[str, str] = field(default_factory=dict)


@dataclass
class Outcome:
    code: str
    recordno: str
    title: str
    status: str
    source: str = ""
    saved_as: str = ""
    sha256: str = ""
    note: str = ""


def log(msg: str) -> None:
    print(msg, flush=True)


def collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        values[key.strip()] = val.strip().strip('"').strip("'")
    return values


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": UA,
        "Accept-Language": "en-US,en;q=0.9,ms;q=0.8",
    })
    return s


def login(session: requests.Session, username: str, password: str) -> None:
    r = session.post(
        f"{LOGIN_URL}?lang=ms",
        data={"username": username, "password": password},
        timeout=60,
    )
    r.raise_for_status()
    if "Login berjaya" not in r.text:
        if "gagal" in r.text.lower() or "salah" in r.text.lower():
            raise RuntimeError("Login failed: wrong username/password.")
        raise RuntimeError("Login failed: unexpected response from login_istudent.php.")
    log(f"Logged in as {username}.")


def fetch(session: requests.Session, url: str, *, params=None, tries: int = 3) -> requests.Response:
    last: Exception | None = None
    for attempt in range(1, tries + 1):
        try:
            r = session.get(url, params=params, timeout=90)
            r.raise_for_status()
            return r
        except Exception as exc:  # network hiccups / transient 5xx
            last = exc
            if attempt < tries:
                time.sleep(1.5 * attempt)
    raise RuntimeError(f"GET {url} failed after {tries} tries: {last}")


def search_hits(session: requests.Session, code: str, delay: float,
                max_pages: int) -> list[Hit]:
    """Return every search hit for a code, filtered to the exact catalogue code."""
    base_params = {
        "lang": "ms",
        "p": "02",
        "query": code,
        "type": "ad",
        "searchby": "1",
        "category": "1",
        "f[cat][0]": "EXAM PAPER",
    }
    hits: list[Hit] = []
    seen: set[str] = set()
    page = 1
    last_page = 1
    while page <= last_page and page <= max_pages:
        r = fetch(session, SEARCH_URL, params={**base_params, "page": page})
        soup = BeautifulSoup(r.text, "html.parser")
        if page == 1:
            nav = soup.select_one('nav[aria-label="Pagination"]')
            if nav:
                nums = [
                    int(m.group(1))
                    for a in nav.select("a[href]")
                    if (m := re.search(r"[?&]page=(\d+)", a.get("href", "")))
                ]
                if nums:
                    last_page = max(nums)
        for a in soup.select('a.title-link[href*="recordno="]'):
            href = a.get("href", "")
            m = re.search(r"recordno=(\d+)", href)
            if not m or m.group(1) in seen:
                continue
            seen.add(m.group(1))
            hits.append(Hit(
                recordno=m.group(1),
                title=collapse(a.get_text(" ")),
                url=urljoin(f"{BASE}/page/", href),
            ))
        page += 1
        if page <= last_page:
            time.sleep(delay)
    exact = [h for h in hits if re.search(
        r"\(\s*" + re.escape(code) + r"\s*\)", h.title, re.I)]
    if exact:
        return exact
    # Fallback: catalogue title may not carry the queried code (e.g. ITS571 is
    # inside the file name only). Return all hits so metadata can be checked.
    return hits


def parse_record(session: requests.Session, hit: Hit) -> Record:
    r = fetch(session, hit.url)
    soup = BeautifulSoup(r.text, "html.parser")
    rec = Record(hit=hit)
    for kdiv in soup.select("div.kv > div.k"):
        vdiv = kdiv.find_next_sibling("div")
        if vdiv:
            rec.meta[collapse(kdiv.get_text())] = collapse(vdiv.get_text())
    form = soup.find("form", id=re.compile(r"myformdownloadexam"))
    if form:
        rec.action = urljoin(hit.url, form.get("action", ""))
        rec.form_data = {
            inp.get("name"): inp.get("value", "")
            for inp in form.find_all("input")
            if inp.get("name")
        }
    return rec


def record_matches(rec: Record, code: str) -> bool:
    kod = rec.meta.get("Kod Kursus", "").upper()
    doc = rec.meta.get("Keterangan Dokumen", "").upper()
    if kod == code.upper():
        return True
    return code.upper() in doc


def download_pdf(session: requests.Session, rec: Record) -> bytes:
    if not rec.action or not rec.form_data:
        raise RuntimeError("no download form (login required or file missing)")
    r = session.post(
        rec.action,
        data=rec.form_data,
        headers={"Referer": rec.hit.url},
        timeout=180,
    )
    r.raise_for_status()
    if not r.content.startswith(b"%PDF"):
        raise RuntimeError(
            f"server returned {r.headers.get('Content-Type', 'unknown')} "
            f"({len(r.content)} bytes), not a PDF"
        )
    return r.content


def pdf_cover_text(pdf_bytes: bytes) -> str:
    text = ""
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(pdf_bytes))
        if reader.pages:
            text = reader.pages[0].extract_text() or ""
    except Exception:
        text = ""
    if len(re.findall(r"[A-Za-z]{3,}", text)) >= 10:
        return text
    return ocr_pdf_cover(pdf_bytes)


def ocr_pdf_cover(pdf_bytes: bytes) -> str:
    import pymupdf  # imported lazily; only needed for scanned covers

    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    try:
        if not doc:
            return ""
        pix = doc[0].get_pixmap(dpi=220, alpha=False)
        with tempfile.TemporaryDirectory(prefix="permata_ocr_") as td:
            png = Path(td) / "cover.png"
            pix.save(str(png))
            return win_ocr(png)
    finally:
        doc.close()


def win_ocr(image_path: Path) -> str:
    fd, script_name = tempfile.mkstemp(prefix="win_ocr_", suffix=".ps1")
    import os
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
                time.sleep(0.1)


def month_year_from_text(text: str) -> str | None:
    text = collapse(text.replace("\u0000", " "))
    for m in _MONTH_RE.finditer(text):
        month = MONTHS[m.group(1).upper()]
        year = (m.group(2).upper()
                .replace("O", "0").replace("I", "1").replace("L", "1"))
        if year.isdigit() and 1990 <= int(year) <= 2035:
            return f"{month} {year}"
    return None


def fallback_name(code: str, meta: dict[str, str]) -> str | None:
    year = meta.get("Tahun", "").strip()
    session = meta.get("Sesi", "").strip()
    if not year:
        return None
    m = re.search(r"SESSION\s*(\d)", session, re.I)
    if m:
        return f"{code} {year} SESSION {m.group(1)}"
    return f"{code} {year}"


def safe_stem(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]+', " ", name)
    return collapse(name).strip(" .")


def unique_path(folder: Path, stem: str) -> Path:
    path = folder / f"{stem}.pdf"
    n = 2
    while path.exists():
        path = folder / f"{stem} ({n}).pdf"
        n += 1
    return path


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    if not path.exists():
        return {}
    try:
        with path.open(encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))
    except (OSError, csv.Error):
        return {}
    return {(r.get("subject", ""), r.get("recordno", "")): r for r in rows}


def process_subject(session: requests.Session, code: str, out_root: Path,
                    delay: float, max_pages: int, dry_run: bool,
                    do_ocr: bool,
                    known: dict[tuple[str, str], dict[str, str]] | None = None
                    ) -> list[Outcome]:
    outcomes: list[Outcome] = []
    log(f"\n=== {code}: searching ===")
    hits = search_hits(session, code, delay, max_pages)
    log(f"{code}: {len(hits)} candidate record(s).")
    if not hits:
        return [Outcome(code, "", "", "no_results")]

    folder = out_root / code
    folder.mkdir(parents=True, exist_ok=True)
    known_hashes: dict[str, Path] = {}
    for p in folder.glob("*.pdf"):
        try:
            known_hashes[hash_file(p)] = p
        except OSError:
            pass

    total = len(hits)
    for idx, hit in enumerate(hits, 1):
        prefix = f"[{idx}/{total}] {hit.recordno}"
        prev = (known or {}).get((code, hit.recordno))
        if prev and prev.get("saved_as"):
            saved = folder / prev["saved_as"]
            if saved.exists():
                log(f"{prefix}: already downloaded ({saved.name})")
                outcomes.append(Outcome(
                    code, hit.recordno, hit.title, "existing",
                    source=prev.get("source_file", ""),
                    saved_as=saved.name, sha256=prev.get("sha256", "")))
                continue
        try:
            rec = parse_record(session, hit)
        except Exception as exc:
            log(f"{prefix}: record page failed: {exc}")
            outcomes.append(Outcome(code, hit.recordno, hit.title,
                                    "failed_record", note=str(exc)))
            time.sleep(delay)
            continue

        if not record_matches(rec, code):
            log(f"{prefix}: skipped (catalogue code "
                f"{rec.meta.get('Kod Kursus', '?')})")
            outcomes.append(Outcome(code, hit.recordno, hit.title,
                                    "skipped_mismatch",
                                    note=rec.meta.get("Kod Kursus", "")))
            time.sleep(delay)
            continue

        if dry_run:
            log(f"{prefix}: DRY {hit.title}")
            outcomes.append(Outcome(code, hit.recordno, hit.title, "dry_run"))
            continue

        try:
            pdf = download_pdf(session, rec)
        except Exception as exc:
            log(f"{prefix}: download failed: {exc}")
            outcomes.append(Outcome(code, hit.recordno, hit.title,
                                    "failed_download", note=str(exc)))
            time.sleep(delay)
            continue

        digest = hashlib.sha256(pdf).hexdigest()
        if digest in known_hashes:
            log(f"{prefix}: duplicate of {known_hashes[digest].name}")
            outcomes.append(Outcome(
                code, hit.recordno, hit.title, "duplicate",
                source=rec.meta.get("Keterangan Dokumen", ""),
                saved_as=known_hashes[digest].name, sha256=digest))
            time.sleep(delay)
            continue

        source = rec.meta.get("Keterangan Dokumen", f"{hit.recordno}.PDF")
        month_year = None
        note = ""
        if do_ocr:
            try:
                month_year = month_year_from_text(pdf_cover_text(pdf))
            except Exception as exc:
                note = f"ocr failed: {exc}"
        if month_year:
            stem = safe_stem(f"{code} {month_year}")
            status = "downloaded"
        else:
            fallback = fallback_name(code, rec.meta)
            stem = safe_stem(fallback) if fallback else safe_stem(Path(source).stem)
            status = "downloaded_fallback"
            note = note or "month not found on cover"

        path = unique_path(folder, stem)
        path.write_bytes(pdf)
        known_hashes[digest] = path
        log(f"{prefix}: {path.name}  <- {source}")
        outcomes.append(Outcome(
            code, hit.recordno, hit.title, status, source=source,
            saved_as=path.name, sha256=digest, note=note))
        time.sleep(delay)

    return outcomes


def write_manifest(outcomes: list[Outcome], path: Path,
                   previous: dict[tuple[str, str], dict[str, str]] | None = None
                   ) -> None:
    """Merge this run's outcomes into the manifest.

    A resumed record reports status "existing"; its earlier downloaded/duplicate
    status is kept so the manifest stays a truthful history.
    """
    rows: dict[tuple[str, str], dict[str, str]] = dict(previous or {})
    for o in outcomes:
        if not o.recordno:
            continue
        key = (o.code, o.recordno)
        if o.status == "existing" and key in rows:
            if o.saved_as:
                rows[key]["saved_as"] = o.saved_as
            continue
        rows[key] = {
            "subject": o.code, "recordno": o.recordno, "title": o.title,
            "status": o.status, "source_file": o.source,
            "saved_as": o.saved_as, "sha256": o.sha256, "note": o.note,
        }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        cols = ["subject", "recordno", "title", "status", "source_file",
                "saved_as", "sha256", "note"]
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for key in sorted(rows):
            w.writerow({c: rows[key].get(c, "") for c in cols})


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Download UiTM PERMATA exam papers for subject codes.")
    ap.add_argument("subjects", nargs="*", help="subject codes, e.g. ICT502")
    ap.add_argument("--subjects-file", type=Path,
                    help="text file with one subject code per line")
    ap.add_argument("--out", type=Path, default=Path.cwd(),
                    help="output root (default: current directory)")
    ap.add_argument("--env", type=Path,
                    default=Path(__file__).with_name(".env"),
                    help="credentials file (default: .env beside script)")
    ap.add_argument("--delay", type=float, default=0.6,
                    help="seconds between requests (default 0.6)")
    ap.add_argument("--max-pages", type=int, default=50,
                    help="search pagination safety cap (default 50)")
    ap.add_argument("--dry-run", action="store_true",
                    help="list matching records without downloading")
    ap.add_argument("--no-ocr", action="store_true",
                    help="skip cover OCR; use metadata-based names")
    ap.add_argument("--no-resume", action="store_true",
                    help="re-download records already listed in the manifest")
    ap.add_argument("--manifest", type=Path,
                    default=Path(__file__).with_name("manifest.csv"),
                    help="CSV log path")
    args = ap.parse_args()

    codes = [c.strip().upper() for c in args.subjects if c.strip()]
    if args.subjects_file:
        codes += [ln.strip().upper()
                  for ln in args.subjects_file.read_text(encoding="utf-8-sig").splitlines()
                  if ln.strip() and not ln.strip().startswith("#")]
    codes = list(dict.fromkeys(codes))
    if not codes:
        ap.error("give at least one subject code or --subjects-file")

    env = load_env(args.env)
    username = env.get("PERMATA_USER", "")
    password = env.get("PERMATA_PASS", "")
    if not username or not password:
        ap.error(f"PERMATA_USER / PERMATA_PASS missing in {args.env}")

    out_root = args.out.resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    session = make_session()
    login(session, username, password)

    all_outcomes: list[Outcome] = []
    prev_rows = load_manifest(args.manifest)
    known = {} if args.no_resume else prev_rows
    started = datetime.now()
    try:
        for code in codes:
            all_outcomes += process_subject(
                session, code, out_root, args.delay, args.max_pages,
                args.dry_run, not args.no_ocr, known)
    finally:
        write_manifest(all_outcomes, args.manifest, prev_rows)

    log("\n=== SUMMARY ===")
    for code in codes:
        rows = [o for o in all_outcomes if o.code == code]
        counts: dict[str, int] = {}
        for o in rows:
            counts[o.status] = counts.get(o.status, 0) + 1
        log(f"{code}: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    log(f"Elapsed: {datetime.now() - started}")
    log(f"Manifest: {args.manifest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
