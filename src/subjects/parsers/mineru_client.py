"""MinerU Cloud API v4 client for local PDFs.

Flow: request batch upload URLs -> PUT the PDF -> poll the batch -> download
the full result ZIP.  The entire ZIP tree is extracted and kept under
``data/tracking/<code>/mineru/<paper_id>/<model>_<options-hash>/``.

The API key is read from ``MINERU_API_KEY`` only and is never logged.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

BASE_URL = "https://mineru.net/api/v4"
TERMINAL_OK = {"done", "success", "finished", "completed"}
TERMINAL_FAIL = {"failed", "error", "cancelled", "canceled"}


class MineruError(RuntimeError):
    pass


class MineruAuthError(MineruError):
    pass


class MineruQuotaError(MineruError):
    pass


class MineruTimeout(MineruError):
    pass


@dataclass
class MineruOptions:
    model_version: str = "pipeline"
    language: str = "en"
    page_ranges: str = ""
    enable_formula: bool = True
    enable_table: bool = True
    timeout_seconds: int = 900
    poll_interval: float = 3.0
    retries: int = 3
    concurrency: int = 2

    def as_dict(self) -> dict:
        return {
            "model_version": self.model_version,
            "language": self.language,
            "page_ranges": self.page_ranges,
            "enable_formula": self.enable_formula,
            "enable_table": self.enable_table,
        }

    def fingerprint(self) -> str:
        blob = json.dumps(self.as_dict(), sort_keys=True).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()[:10]


@dataclass
class MineruConfig:
    api_key: str = ""
    base_url: str = BASE_URL
    page_budget: int = 200
    request_timeout: int = 300
    options: MineruOptions = field(default_factory=MineruOptions)


def load_config() -> MineruConfig:
    key = os.environ.get("MINERU_API_KEY", "").strip()
    model = os.environ.get("MINERU_MODEL_VERSION", "pipeline").strip()
    language = os.environ.get("MINERU_LANGUAGE", "en").strip()
    budget = int(os.environ.get("MINERU_PAGE_BUDGET", "200"))
    return MineruConfig(
        api_key=key,
        page_budget=budget,
        options=MineruOptions(model_version=model or "pipeline",
                              language=language or "en"),
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_extract(zip_path: Path, target: Path) -> list[str]:
    target.mkdir(parents=True, exist_ok=True)
    root = target.resolve()
    names = []
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            destination = (target / info.filename).resolve()
            if root != destination and root not in destination.parents:
                raise MineruError(
                    f"unsafe path in MinerU zip: {info.filename}")
            archive.extract(info, target)
            if not info.is_dir():
                names.append(info.filename)
    return names


def _data(payload: dict) -> dict:
    data = payload.get("data")
    return data if isinstance(data, dict) else payload


class MineruClient:
    def __init__(self, config: MineruConfig | None = None):
        self.config = config or load_config()
        if not self.config.api_key:
            raise MineruAuthError(
                "MINERU_API_KEY is not set; export it in the environment")
        timeout = httpx.Timeout(
            connect=30,
            read=float(self.config.request_timeout),
            write=float(self.config.request_timeout),
            pool=30)
        self._client = httpx.Client(
            timeout=timeout,
            headers={"Authorization": f"Bearer {self.config.api_key}"})
        # Presigned OSS upload URLs carry their signature in the query string.
        # Sending the API Authorization header breaks that signature, so uploads
        # must use a client without the MinerU auth header.
        self._upload_client = httpx.Client(timeout=timeout)

    def close(self) -> None:
        self._client.close()
        self._upload_client.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def _request(self, method: str, url: str, *, with_auth: bool = True,
                 **kwargs) -> httpx.Response:
        delay = 1.5
        last = None
        client = self._client if with_auth else self._upload_client
        for attempt in range(self.config.options.retries + 1):
            try:
                response = client.request(method, url, **kwargs)
            except httpx.RequestError as error:
                last = error
                if attempt >= self.config.options.retries:
                    raise MineruError(f"MinerU request failed: {error}") from error
                time.sleep(delay)
                delay *= 2
                continue
            if with_auth and response.status_code in (401, 403):
                raise MineruAuthError(
                    "MinerU key/token rejected (401/403). Check "
                    "MINERU_API_KEY and its quota.")
            if not with_auth and response.status_code == 403:
                raise MineruError(
                    "MinerU upload URL rejected the upload (403). The "
                    "presigned URL may have expired; retry the paper.")
            if not with_auth and response.status_code >= 400:
                raise MineruError(
                    f"MinerU upload HTTP {response.status_code}: "
                    f"{response.text[:300]}")
            if response.status_code == 429:
                raise MineruQuotaError(
                    "MinerU quota/rate limit reached (429). Wait for the "
                    "quota reset before retrying.")
            if response.status_code >= 500 and attempt < self.config.options.retries:
                time.sleep(delay)
                delay *= 2
                continue
            if response.status_code >= 400:
                raise MineruError(
                    f"MinerU HTTP {response.status_code}: "
                    f"{response.text[:300]}")
            return response
        raise MineruError(f"MinerU request failed: {last}")

    def _json(self, method: str, url: str, **kwargs) -> dict:
        response = self._request(method, url, **kwargs)
        try:
            payload = response.json()
        except ValueError as error:
            raise MineruError("MinerU returned non-JSON") from error
        code = payload.get("code")
        if code not in (None, 0, 200, "0", "200"):
            message = payload.get("msg") or payload.get("message") or payload
            if code in (401, 403):
                raise MineruAuthError(f"MinerU auth error: {message}")
            if code == 429:
                raise MineruQuotaError(f"MinerU quota error: {message}")
            raise MineruError(f"MinerU API error {code}: {message}")
        return _data(payload)

    def parse(self, *, code: str, paper_path: Path, paper_id: str,
              page_count: int, options: MineruOptions,
              tracking: Path) -> dict:
        """Return cached or newly parsed MinerU output.

        Cache key: file sha256 + model version + option fingerprint.
        A cache hit makes no network call.
        """
        digest = _sha256(paper_path)
        cache = (tracking / "mineru" / paper_id
                 / f"{options.model_version}_{options.fingerprint()}")
        manifest_path = cache / "manifest.json"
        if manifest_path.is_file():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if (manifest.get("sha256") == digest
                    and manifest.get("model_version") == options.model_version):
                manifest["cached"] = True
                return manifest
        cache.mkdir(parents=True, exist_ok=True)
        started = time.time()
        task_id = ""
        try:
            file_entry = {"name": paper_path.name,
                          "data_id": paper_id.replace(" ", "_")}
            if options.page_ranges:
                file_entry["page_ranges"] = options.page_ranges
            payload = {
                "files": [file_entry],
                "model_version": options.model_version,
                "enable_formula": options.enable_formula,
                "enable_table": options.enable_table,
                "language": options.language,
            }
            data = self._json("POST", f"{self.config.base_url}/file-urls/batch",
                              json=payload)
            batch_id = data.get("batch_id")
            urls = data.get("file_urls") or data.get("files") or []
            if not batch_id or not urls:
                raise MineruError(
                    "batch response missing batch_id or upload URLs")
            task_id = str(batch_id)
            # The presigned URL signs only its query string. Do not add
            # Content-Type (or the API Authorization header) here: either one
            # changes the signature and OSS returns SignatureDoesNotMatch.
            self._request("PUT", urls[0], with_auth=False,
                          content=paper_path.read_bytes())
            zip_url = self._poll(batch_id, paper_path.name, options)
        except Exception:
            raise
        zip_path = cache / "result.zip"
        response = self._request("GET", zip_url)
        zip_path.write_bytes(response.content)
        names = _safe_extract(zip_path, cache)
        manifest = {
            "schema_version": 1,
            "subject": code,
            "paper_id": paper_id,
            "source": str(paper_path),
            "sha256": digest,
            "model_version": options.model_version,
            "options": options.as_dict(),
            "batch_id": task_id,
            "page_count": int(page_count),
            "started_at": started,
            "finished_at": time.time(),
            "duration_seconds": round(time.time() - started, 2),
            "zip": str(zip_path),
            "files": names,
            "cached": False,
        }
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
        return manifest

    def _poll(self, batch_id: str, file_name: str,
              options: MineruOptions) -> str:
        deadline = time.time() + options.timeout_seconds
        last_state = ""
        while time.time() < deadline:
            data = self._json(
                "GET", f"{self.config.base_url}/extract-results/batch/{batch_id}")
            rows = (data.get("extract_result")
                    or data.get("results") or data.get("files") or [])
            if isinstance(rows, dict):
                rows = [rows]
            row = next((item for item in rows
                        if item.get("file_name") == file_name), None)
            if row is None and rows:
                row = rows[0]
            if not row:
                time.sleep(options.poll_interval)
                continue
            state = str(row.get("state") or row.get("status") or "").lower()
            if state != last_state:
                last_state = state
            if state in TERMINAL_OK:
                url = row.get("full_zip_url") or row.get("zip_url")
                if not url:
                    raise MineruError(
                        f"MinerU batch {batch_id} finished without a zip URL")
                return str(url)
            if state in TERMINAL_FAIL:
                raise MineruError(
                    f"MinerU batch {batch_id} failed: "
                    f"{row.get('err_msg') or row.get('message') or row}")
            time.sleep(options.poll_interval)
        raise MineruTimeout(
            f"MinerU batch {batch_id} timed out after "
            f"{options.timeout_seconds}s (last state: {last_state or 'unknown'})")
