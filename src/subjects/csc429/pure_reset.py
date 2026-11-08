"""P0 reset and lock for the CSC429 asset-first pipeline.

This module archives the rejected v1 question bank, assets and seeds, writes a
content-hash rejected registry, locks the subject to Type D and creates a
fresh lifecycle state.  It keeps only the deterministic page/layout/OCR cache
needed to avoid re-rendering the source PDFs.

    uv run python -m src.subjects.csc429.pure_reset
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from src import config

SUBJECT = "CSC429"
TRACKING = config.TRACKING_DIR / "csc429"
ARCHIVE = config.PROJECT_ROOT / "data" / "archive" / "csc429_v1_20261107"
REJECTED = TRACKING / "rejected_registry.json"
REPORT = TRACKING / "p0_reset_report.json"
SUBJECT_PATH = config.PROJECT_ROOT / "subjects" / SUBJECT / "subject.json"
LIFECYCLE_PATH = config.PROJECT_ROOT / "subjects" / SUBJECT / "lifecycle_state.json"
LIFECYCLE_ARCHIVE = (
    config.PROJECT_ROOT / "subjects" / SUBJECT / "archive"
    / "lifecycle_state_v1_20261107.json")
TEMPLATES = TRACKING / "templates"
EXPERIMENT_TEMPLATES = (
    config.PROJECT_ROOT / "outputs" / "experiments"
    / "csc429_pure_20261106" / "inputs")
ARCHIVED_EXPERIMENT_TEMPLATES = (
    ARCHIVE / "seeds" / "csc429_pure_20261106" / "inputs")

KEEP_TRACKING = {
    "pages", "layout", "paper_text", "cover_text.json",
    "pages_manifest.json", "layout_manifest.json", "papers_register.json",
}
MOVE_TRACKING = {
    "assets", "build_sample", "generator_sample_seed_01.json",
    "generator_validation.json", "model_answers.json",
    "papers_summary.json", "planner_seed_01.json", "planner_seed_02.json",
    "planner_seed_03.json", "question_bank_draft.json", "question_log.json",
    "stage1_corrections.json", "stage1_report.json", "stage8_coverage.json",
    "taxonomy.json", "taxonomy_summary.json", "template_check.json",
}
SEED_DIRS = [
    config.PROJECT_ROOT / "outputs" / "experiments" / "csc429_pure_20261106",
    config.PROJECT_ROOT / "outputs" / "experiments" / "csc429_pure_20261107",
    config.PROJECT_ROOT / "outputs" / "pilot" / SUBJECT,
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _save(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def _move(source: Path, target: Path) -> None:
    if not source.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if source.is_dir() and target.is_dir():
            children = list(source.iterdir())
            if not children:
                source.rmdir()
                return
            for child in children:
                _move(child, target / child.name)
            source.rmdir()
            return
        raise RuntimeError(f"archive target already exists: {target}")
    shutil.move(str(source), str(target))


def _asset_hashes() -> dict[str, dict]:
    rows: dict[str, dict] = {}
    manifest = TRACKING / "assets" / "manifest.json"
    if manifest.is_file():
        payload = _load(manifest, {})
        for asset in payload.get("assets", []):
            digest = str(asset.get("sha256", ""))
            if digest:
                rows[digest] = {
                    "asset_id": asset.get("asset_id", ""),
                    "paper_id": asset.get("paper_id", ""),
                    "kind": asset.get("kind", ""),
                    "label": asset.get("label", ""),
                    "archive": "tracking_v1",
                }
    for base in (
            config.PROJECT_ROOT / "outputs" / "experiments",
            config.PROJECT_ROOT / "outputs" / "archive",
            config.PROJECT_ROOT / "data" / "archive"):
        if not base.exists():
            continue
        for manifest in base.rglob("asset_manifest.json"):
            payload = _load(manifest, {})
            for asset in payload.get("assets", []):
                digest = str(asset.get("sha256", ""))
                if digest:
                    rows.setdefault(digest, {
                        "asset_id": asset.get("asset_id")
                        or asset.get("label", ""),
                        "paper_id": asset.get("paper_id")
                        or asset.get("paper_label", ""),
                        "kind": asset.get("kind", ""),
                        "label": asset.get("label", ""),
                        "archive": str(manifest.parent.relative_to(
                            config.PROJECT_ROOT)),
                    })
        for png in base.rglob("*.png"):
            if "assets" not in png.parts:
                continue
            digest = _sha256(png)
            rows.setdefault(digest, {
                "asset_id": png.stem,
                "paper_id": png.parent.name,
                "kind": "unknown",
                "label": "",
                "archive": str(png.parent.relative_to(config.PROJECT_ROOT)),
            })
    return rows


def _seed_registry() -> tuple[list[dict], dict[str, dict]]:
    seeds: list[dict] = []
    files: dict[str, dict] = {}
    for root in [
            config.PROJECT_ROOT / "outputs" / "archive",
            config.PROJECT_ROOT / "outputs" / "experiments",
            config.PROJECT_ROOT / "outputs" / "pilot",
            config.PROJECT_ROOT / "data" / "archive"]:
        if not root.exists():
            continue
        for meta in root.rglob("meta.json"):
            try:
                payload = json.loads(meta.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if str(payload.get("subject", "")).upper() != SUBJECT:
                continue
            seed = payload.get("seed")
            if seed is None:
                continue
            seed_id = f"{meta.parent.name}#seed-{seed}"
            seeds.append({
                "seed_id": seed_id,
                "seed": int(seed),
                "path": str(meta.parent.relative_to(config.PROJECT_ROOT)),
                "created": payload.get("created"),
            })
            for name in ("paper.docx", "paper.pdf", "scheme.docx",
                         "scheme.pdf"):
                path = meta.parent / name
                if path.is_file():
                    files[_sha256(path)] = {
                        "seed_id": seed_id,
                        "file": str(path.relative_to(config.PROJECT_ROOT)),
                    }
    for plan in (config.PROJECT_ROOT / "outputs" / "experiments").rglob(
            "seed_*/plan.json"):
        try:
            payload = json.loads(plan.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        seed = payload.get("seed")
        if seed is None:
            continue
        seed_id = f"{plan.parent.name}#seed-{seed}"
        if not any(row["seed_id"] == seed_id for row in seeds):
            seeds.append({
                "seed_id": seed_id,
                "seed": int(seed),
                "path": str(plan.parent.relative_to(config.PROJECT_ROOT)),
                "created": payload.get("created"),
            })
    return seeds, files


def _archive() -> None:
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    if LIFECYCLE_PATH.exists() and not LIFECYCLE_ARCHIVE.exists():
        LIFECYCLE_ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(LIFECYCLE_PATH, LIFECYCLE_ARCHIVE)
    tracking_archive = ARCHIVE / "tracking_rejected"
    tracking_archive.mkdir(parents=True, exist_ok=True)
    for name in sorted(MOVE_TRACKING):
        source = TRACKING / name
        if source.exists():
            _move(source, tracking_archive / name)
    for source in SEED_DIRS:
        if source.exists():
            _move(source, ARCHIVE / "seeds" / source.name)
    cache = config.WEB_CACHE_DIR / SUBJECT
    if cache.exists():
        _move(cache, ARCHIVE / "web_cache")
    cache.mkdir(parents=True, exist_ok=True)


def _lock_subject() -> dict:
    payload = _load(SUBJECT_PATH, {})
    payload.update({
        "type": "D",
        "status": "coming_soon",
        "strategy": "pure_extraction",
        "generators_enabled": [],
        "enabled_computed_generators": [],
        "parametric_variants": False,
        "plugins": {},
        "capabilities": {
            "subject_type": "D",
            "generation": "deterministic",
            "prebuild": "plugin",
            "public_documents": "copy_cached",
            "needs_llm": False,
            "uses_slides": False,
            "uses_past_papers": True,
            "deterministic": True,
            "practice_mode": False,
            "placeholders": False,
            "public_scheme_requires_quote_marker": False,
            "asset_first": True,
            "parametric_variants": False,
        },
    })
    payload["permissions"]["publication"]["notes"] = (
        "Type D pure-extraction reset; publication, upload and Worker "
        "deployment remain disabled.")
    _save(SUBJECT_PATH, payload)
    return payload


def _copy_templates() -> list[dict]:
    TEMPLATES.mkdir(parents=True, exist_ok=True)
    rows = []
    for name in ("paper_template.docx", "scheme_template.docx"):
        source = EXPERIMENT_TEMPLATES / name
        if not source.is_file():
            source = ARCHIVED_EXPERIMENT_TEMPLATES / name
        if not source.is_file():
            raise RuntimeError(f"approved experiment template missing: {source}")
        target = TEMPLATES / name
        shutil.copy2(source, target)
        rows.append({
            "name": name,
            "path": str(target.relative_to(config.PROJECT_ROOT)),
            "sha256": _sha256(target),
            "source": str(source.relative_to(config.PROJECT_ROOT)),
        })
    return rows


def _empty_stage(notes: str = "") -> dict:
    return {
        "status": "pending",
        "evidence": [],
        "llm_cost_usd": 0.0,
        "blockers": [],
        "human_approval": {
            "required": True, "approved": False, "by": "", "on": "",
            "note": "",
        },
        "notes": notes,
    }


def _lifecycle(templates: list[dict]) -> dict:
    stages = {
        key: _empty_stage()
        for key in (
            "0_intake", "1_preprocess", "2_scheme_slides", "3_template",
            "4_taxonomy_question_log", "5_fingerprint_planner",
            "6_generators", "7_builders_qa", "8_library_prebuild",
            "9_publish", "10_close_out")
    }
    stages["0_intake"] = {
        "status": "in_progress",
        "evidence": [
            "subjects/CSC429/subject.json",
            "data/tracking/csc429/rejected_registry.json",
            "data/tracking/csc429/p0_reset_report.json",
            "data/tracking/csc429/templates/paper_template.docx",
            "data/tracking/csc429/templates/scheme_template.docx",
        ],
        "llm_cost_usd": 0.0,
        "blockers": [],
        "human_approval": {
            "required": True, "approved": False, "by": "", "on": "",
            "note": "P0 lock; Gate 1 is after extraction and does not start yet.",
        },
        "notes": (
            "P0 reset. Type D, strategy pure_extraction, generators disabled, "
            "parametric variants disabled. Inputs confirmed: 23 PDFs, 20 "
            "unique. Templates copied from the accepted pure-extraction "
            "experiment."),
    }
    stages["2_scheme_slides"] = _empty_stage(
        "Type D uses the owner-approved templates and unofficial answers; "
        "supplied scheme/slides are not part of the source of truth.")
    stages["6_generators"] = _empty_stage(
        "Type D disables all generators and parametric variants.")
    return {
        "schema_version": 2,
        "subject": SUBJECT,
        "type": "D",
        "strategy": "pure_extraction",
        "created": _now(),
        "updated": _now(),
        "stages": stages,
        "unsure": [],
        "llm_cost": {
            "currency": "USD",
            "total_usd": 0.0,
            "by_stage": {key: 0.0 for key in stages},
        },
        "gate": "GATE 1",
        "gate_status": "not_started",
        "templates": templates,
        "rejected_registry": "data/tracking/csc429/rejected_registry.json",
    }


def run() -> dict:
    # Copy the approved templates into the new working tree before the
    # experiment folder is archived.
    templates = _copy_templates()
    # Read the old manifests before moving them into the archive.
    asset_hashes = _asset_hashes()
    seed_rows, file_hashes = _seed_registry()
    _archive()
    registry = {
        "schema_version": 1,
        "subject": SUBJECT,
        "created": _now(),
        "note": (
            "Every earlier CSC429 seed, cache, asset and generated file. "
            "No hash in this registry may appear in new outputs."),
        "seeds": sorted(seed_rows, key=lambda row: row["seed_id"]),
        "assets": dict(sorted(asset_hashes.items())),
        "files": dict(sorted(file_hashes.items())),
        "counts": {
            "seeds": len(seed_rows),
            "assets": len(asset_hashes),
            "files": len(file_hashes),
        },
    }
    _save(REJECTED, registry)
    subject = _lock_subject()
    lifecycle = _lifecycle(templates)
    _save(LIFECYCLE_PATH, lifecycle)
    report = {
        "schema_version": 1,
        "stage": "P0",
        "created": _now(),
        "archived_to": str(ARCHIVE.relative_to(config.PROJECT_ROOT)),
        "kept_preprocessing": sorted(KEEP_TRACKING),
        "moved_tracking": sorted(MOVE_TRACKING),
        "moved_seed_dirs": [
            str(path.relative_to(config.PROJECT_ROOT)) for path in SEED_DIRS
            if (ARCHIVE / "seeds" / path.name).exists()],
        "inputs": {"pdfs": 23, "unique": 20},
        "templates": templates,
        "subject_type": subject["type"],
        "strategy": subject["strategy"],
        "generators_enabled": subject["generators_enabled"],
        "parametric_variants": subject["parametric_variants"],
        "rejected_counts": registry["counts"],
        "lifecycle_schema_version": lifecycle["schema_version"],
        "cost_usd": 0.0,
    }
    _save(REPORT, report)
    return report


def main() -> None:
    print(json.dumps(run(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
