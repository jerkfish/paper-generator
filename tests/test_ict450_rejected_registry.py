"""ICT450 v1 archive and rejected-registry guards.

The v1 subject was not approved. New ICT450 work must not read or copy the
archived v1 outputs, and the active contract must be the v2 recycle contract.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "docs/archive/ict450_v1"
MANIFEST = ARCHIVE / "MANIFEST.json"
REJECTED = ARCHIVE / "rejected_registry.json"
KEEP = ARCHIVE / "UNVERIFIED_KEEP.json"
SUBJECT = ROOT / "subjects/ICT450/subject.json"
LIFECYCLE = ROOT / "subjects/ICT450/lifecycle_state.json"


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_archive_manifest_and_rejected_registry_exist():
    assert MANIFEST.is_file()
    assert REJECTED.is_file()
    assert KEEP.is_file()

    manifest = _load(MANIFEST)
    rejected = _load(REJECTED)
    assert manifest["subject"] == "ICT450"
    assert manifest["description"].startswith("Archive of all ICT450 v1 work")
    assert rejected["subject"] == "ICT450"
    assert rejected["seed_ids"] == [1, 2, 3, 10]
    assert rejected["hashes"]
    assert rejected["seeds"]

    # Tracked archive paths must exist. Data paths are checked only when the
    # local private data tree is present (it is gitignored).
    data_present = (ROOT / "data").exists()
    for entry in manifest["moved"]:
        archive_path = ROOT / entry["archive"]
        if not data_present and entry["archive"].startswith("data/"):
            continue
        assert archive_path.is_file(), entry["archive"]
    copied = manifest["copied"][0]
    assert (ROOT / copied["archive"]).is_file()


def test_active_contract_is_v2_recycle():
    subject = _load(SUBJECT)
    lifecycle = _load(LIFECYCLE)

    assert subject["type"] == "D"
    assert subject["strategy"] == "recycle"
    assert subject["variants"]["enabled"] is False
    assert subject["extraction"]["method"] == "mineru"
    assert subject["permissions"]["publication"]["allowed"] is True
    assert subject["archive"]["v1_manifest"] == (
        "docs/archive/ict450_v1/MANIFEST.json")

    assert lifecycle["schema_version"] == 2
    assert lifecycle["playbook_version"] == "2.0"
    assert lifecycle["type"] == "D"
    assert lifecycle["strategy"] == "recycle"
    assert "V0_intake" in lifecycle["stages"]
    assert lifecycle["lifecycle_status"] in {
        "restarting_v2", "in_progress", "blocked", "complete"}
    assert lifecycle["gates"]["A"]["status"] in {"pending", "approved"}
    assert lifecycle["gates"]["B"]["status"] == "approved"
    assert lifecycle["gates"]["C"]["status"] == "approved"
    assert int(lifecycle["bank"]["questions"]) >= 0
    assert lifecycle["answers"]["official"] == 0


def test_active_ict450_outputs_do_not_use_rejected_hashes():
    rejected = _load(REJECTED)
    rejected_hashes = set(rejected["hashes"])

    # V6 builds a fresh library under the active cache root.  None of those
    # files may be a copy of a rejected v1 artifact.
    cache_root = ROOT / "outputs/web_cache/ICT450"
    if cache_root.exists():
        manifest = _load(cache_root / "library_manifest.json")
        assert manifest["library_size"] <= 20
        assert manifest["reuse"]["within_cap"] is True
        for path in cache_root.rglob("*"):
            if path.is_file():
                assert _sha(path) not in rejected_hashes, path

    # Kept paper-register files may remain under data/tracking/ict450, but no
    # bank output may match a rejected v1 artifact.  The raw MinerU cache is
    # excluded: re-extracting the same source page can legitimately produce an
    # identical image hash; what matters is the reviewed bank crop.
    active = ROOT / "data/tracking/ict450"
    if active.exists():
        for path in active.rglob("*"):
            if not path.is_file():
                continue
            if "v2/mineru" in path.as_posix() or "v2\\mineru" in str(path):
                continue
            assert _sha(path) not in rejected_hashes, path

    # Active subject code must not import or point at the v1 archive.
    code_root = ROOT / "src/subjects/ict450"
    if code_root.exists():
        for path in code_root.rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="replace")
            assert "ict450_v1" not in text, path
            assert "docs/archive/ict450_v1" not in text, path


def test_kept_material_is_marked_unverified():
    keep = _load(KEEP)
    assert keep["items"]
    for item in keep["items"]:
        assert item["status"] == (
            "unverified, reuse only after owner confirmation")
        if (ROOT / "data").exists():
            assert (ROOT / item["path"]).is_file(), item["path"]
    assert keep["crest_assets"]["embedded_in"]
    assert keep["retained_source_material"]
