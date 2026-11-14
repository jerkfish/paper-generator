"""Shared MinerU extraction wrapper for recycle subjects.

The wrapper enforces the subject's papers/cloud-processing permissions and
reuses the existing MinerU client and normalizer.  It never logs the API key.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.subjects.parsers import mineru_client, mineru_normalize
from src.subjects.registry import get_subject


class ExtractionPermissionError(RuntimeError):
    pass


def subject_permissions(codes: str) -> dict:
    subject = get_subject(codes)
    return dict(subject.permissions or {})


def require_extraction_permission(codes: str) -> dict:
    permissions = subject_permissions(codes)
    papers = (permissions.get("papers") or {})
    cloud = (permissions.get("cloud_processing") or {})
    if not papers.get("allowed"):
        raise ExtractionPermissionError(
            f"{codes}: papers permission is not allowed")
    if not cloud.get("allowed"):
        raise ExtractionPermissionError(
            f"{codes}: cloud_processing permission is not allowed")
    return {"papers": papers, "cloud_processing": cloud}


def extract_paper(
    *,
    subject_code: str,
    paper_path: Path,
    paper_id: str,
    page_count: int,
    tracking: Path,
    model: str = "vlm",
    options: mineru_client.MineruOptions | None = None,
) -> dict:
    """Extract one PDF with MinerU and normalize its review dossier."""
    require_extraction_permission(subject_code)
    configured = mineru_client.load_config()
    chosen = options or mineru_client.MineruOptions(
        model_version=model,
        language=configured.options.language,
        timeout_seconds=configured.options.timeout_seconds,
        poll_interval=configured.options.poll_interval,
        retries=configured.options.retries,
        concurrency=configured.options.concurrency,
    )
    chosen.model_version = model
    config_data = mineru_client.MineruConfig(
        api_key=configured.api_key,
        page_budget=configured.page_budget,
        request_timeout=configured.request_timeout,
        options=chosen,
    )
    with mineru_client.MineruClient(config_data) as client:
        manifest = client.parse(
            code=subject_code,
            paper_path=Path(paper_path),
            paper_id=paper_id,
            page_count=int(page_count),
            options=chosen,
            tracking=Path(tracking),
        )
    cache_dir = Path(manifest["zip"]).parent
    normalized = mineru_normalize.normalize(
        paper_id=paper_id,
        pdf_path=Path(paper_path),
        cache_dir=cache_dir,
        model=model,
        out_dir=cache_dir / "review",
    )
    result = {
        "subject": subject_code,
        "paper_id": paper_id,
        "model": model,
        "cache_dir": str(cache_dir),
        "manifest": manifest,
        "normalized": normalized,
        "permissions": require_extraction_permission(subject_code),
    }
    (cache_dir / "extraction_result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    return result
