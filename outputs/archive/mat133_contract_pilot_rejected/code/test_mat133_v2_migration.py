"""MAT133 legacy-contract migration to playbook v2.

The v1 lifecycle and documents are preserved. v2 documents live beside them
and the Library exposes both versions through a registry-driven column model.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.app import jobs
from src.app.filenames import download_filename
from src.subjects.lifecycle import (
    gate_approved,
    is_v2,
    load_state,
    status_report,
)
from src.subjects.registry import get_subject

ROOT = Path(__file__).resolve().parents[1]
SUBJECT = ROOT / "subjects/MAT133/subject.json"
LIFECYCLE = ROOT / "subjects/MAT133/lifecycle_state.json"
LIFECYCLE_V1 = ROOT / "subjects/MAT133/lifecycle_state_v1.json"
TEMPLATES = ROOT / "src/app/templates"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_v1_lifecycle_is_preserved_verbatim():
    v1 = _load(LIFECYCLE_V1)
    v2 = _load(LIFECYCLE)
    assert v1["schema_version"] == 1
    assert "0_intake" in v1["stages"]
    assert "10_close_out" in v1["stages"]
    assert v2["legacy_state"] == "subjects/MAT133/lifecycle_state_v1.json"
    assert v2["legacy_state_sha256"] == _sha(LIFECYCLE_V1)


def test_v2_lifecycle_stops_at_gate_b():
    state = _load(LIFECYCLE)
    assert state["schema_version"] == 2
    assert state["playbook_version"] == "2.0"
    assert state["type"] == "B"
    assert state["strategy"] == "generate"
    assert is_v2(state)
    assert set(state["stages"]) == {
        "V0_intake", "V1_extract", "V2_bank", "V3_format", "V4_answers",
        "V5_seeds_1_3", "V6_library", "V7_publish", "V8_close_out"}
    assert state["stages"]["V5_seeds_1_3"]["status"] == "in_progress"
    assert state["gates"]["A"]["status"] == "not_applicable"
    assert state["gates"]["B"]["status"] == "pending"
    assert state["gates"]["C"]["status"] == "pending"
    assert state["lifecycle_status"] == "awaiting_gate_b"
    assert gate_approved(state, "A") is True
    assert gate_approved(state, "B") is False
    assert gate_approved(state, "C") is False

    report = status_report(ROOT, "MAT133")
    assert report["next_stage"] == "V5_seeds_1_3"
    assert report["next_gate"] == "B"
    assert any("Gate B" in blocker for blocker in report["blockers"])


def test_subject_contract_records_v2_documents():
    subject = get_subject("MAT133")
    assert subject.subject_type == "B"
    assert subject.strategy == "generate"
    assert subject.variants["enabled"] is True
    assert subject.documents["versions"] == [1, 2]
    assert subject.public_document_versions == {"1"}
    assert subject.public_dict()["documents"] == {
        "versions": [1, 2], "public_versions": ["1"]}


def test_versioned_download_filename_keeps_v1_name():
    assert download_filename("MAT133", 1, 2026, "docx") == (
        "MAT133 Seed 01 2026.docx")
    assert download_filename("MAT133", 1, 2026, "docx", version=2) == (
        "MAT133 Seed 01 2026 (v2).docx")
    assert download_filename("MAT133", 1, 2026, "pdf", scheme=True,
                             version=2) == (
        "MAT133 Seed 01 2026 - Marking Scheme (v2).pdf")


def test_library_item_and_file_expose_both_versions(monkeypatch, tmp_path):
    monkeypatch.setattr(jobs.config, "WEB_CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(jobs.config, "PUBLIC_BUILD", False)
    out = jobs.cache_path("realistic", 7, None, subject="MAT133")
    out.mkdir(parents=True)
    v1 = {kind: out / f"{kind}.bin" for kind in
          ("paper_docx", "paper_pdf", "scheme_docx", "scheme_pdf")}
    v2 = {kind: out / f"{kind}_v2.bin" for kind in v1}
    for path in [*v1.values(), *v2.values()]:
        path.write_bytes(b"x")
    meta = {
        "seed": 7,
        "mode": "realistic",
        "year": 2026,
        "total_marks": 68,
        "has_practice_mode": False,
        "has_placeholders": False,
        "files": {key: str(value) for key, value in v1.items()},
        "document_versions": {
            "2": {
                "label": "v2",
                "playbook_version": "2.0",
                "files": {key: str(value) for key, value in v2.items()},
            },
        },
    }
    (out / "meta.json").write_text(json.dumps(meta), encoding="utf-8")

    item = jobs.library_item(7, "MAT133")
    assert [version["version"] for version in item["versions"]] == [1, 2]
    assert item["version_map"]["1"]["kinds"]["paper_docx"] == "paper_docx"
    assert item["version_map"]["2"]["kinds"]["paper_docx"] == "paper_v2_docx"
    assert item["downloads"]["paper_v2_docx"] == (
        "MAT133 Seed 07 2026 (v2).docx")
    assert [column["label"] for column in
            jobs.library_version_columns([item])] == ["v1", "v2"]
    assert jobs.library_file(7, "paper_v2_docx", "MAT133") == v2["paper_docx"]
    assert jobs.library_file(7, "scheme_v2_pdf", "MAT133") == v2["scheme_pdf"]
    assert jobs.library_file(7, "paper_docx", "MAT133") == v1["paper_docx"]


def test_library_table_renders_version_columns():
    version1 = {
        "version": 1, "label": "v1",
        "files": {"paper_docx": "a", "paper_pdf": "b",
                  "scheme_docx": "c", "scheme_pdf": "d"},
        "downloads": {key: key for key in
                      ("paper_docx", "paper_pdf", "scheme_docx",
                       "scheme_pdf")},
        "kinds": {key: key for key in
                  ("paper_docx", "paper_pdf", "scheme_docx", "scheme_pdf")},
    }
    version2 = {
        "version": 2, "label": "v2",
        "files": {"paper_docx": "a", "paper_pdf": "b",
                  "scheme_docx": "c", "scheme_pdf": "d"},
        "downloads": {key: key for key in
                      ("paper_v2_docx", "paper_v2_pdf", "scheme_v2_docx",
                       "scheme_v2_pdf")},
        "kinds": {"paper_docx": "paper_v2_docx",
                  "paper_pdf": "paper_v2_pdf",
                  "scheme_docx": "scheme_v2_docx",
                  "scheme_pdf": "scheme_v2_pdf"},
    }
    item = {
        "subject": "MAT133", "seed": 1, "mode": "realistic",
        "computed_display": 0, "marks_value": 68,
        "topic_marks": {"functions": 10}, "topic_keys": "functions",
        "topic_mix": "FUN 10", "has_placeholders": False,
        "placeholders": 0, "files": version1["files"],
        "downloads": {**version1["downloads"], **version2["downloads"]},
        "versions": [version1, version2],
        "version_map": {"1": version1, "2": version2},
    }
    env = Environment(loader=FileSystemLoader(str(TEMPLATES)),
                      autoescape=select_autoescape(["html", "xml"]))
    html = env.get_template("_library.html").render(
        subject=get_subject("MAT133"), items=[item], total=1, public=False,
        library_disabled=False,
        version_columns=jobs.library_version_columns([item]))
    for label in ("Docs v1", "Scheme v1", "Docs v2", "Scheme v2"):
        assert label in html
    assert "/mat133/library/1/paper_v2_docx" in html
    assert "/mat133/library/1/scheme_v2_pdf" in html
    assert "/mat133/library/1/paper_docx" in html


def test_public_bundle_keeps_mat133_v1_only():
    from scripts.build_public_bundle import _public_item

    subject = get_subject("MAT133")
    item = {
        "versions": [
            {"version": 1, "label": "v1",
             "downloads": {"paper_docx": "v1.docx"},
             "kinds": {"paper_docx": "paper_docx"}, "files": {}},
            {"version": 2, "label": "v2",
             "downloads": {"paper_v2_docx": "v2.docx"},
             "kinds": {"paper_docx": "paper_v2_docx"}, "files": {}},
        ],
        "downloads": {"paper_docx": "v1.docx",
                      "paper_v2_docx": "v2.docx"},
    }
    public = _public_item(item, subject)
    assert [version["label"] for version in public["versions"]] == ["v1"]
    assert list(public["downloads"]) == ["paper_docx"]


def test_seeds_4_plus_are_blocked_until_gate_b(monkeypatch):
    from src.subjects.mat133 import v2

    monkeypatch.setattr(v2, "_gate_b_approved", lambda: False)
    with pytest.raises(RuntimeError, match="Gate B"):
        v2.build_seed_v2(4)


def test_v2_documents_exist_and_pass_validation():
    item = jobs.library_item(1, "MAT133")
    if item is None or len(item["versions"]) < 2:
        pytest.skip("MAT133 v2 cache is not present")
    v1 = item["version_map"]["1"]
    assert Path(v1["files"]["paper_docx"]).name == "paper.docx"
    assert Path(v1["files"]["paper_pdf"]).name == "paper.pdf"
    assert Path(v1["files"]["scheme_docx"]).name == "scheme.docx"
    assert Path(v1["files"]["scheme_pdf"]).name == "scheme.pdf"
    for seed in (1, 2, 3):
        item = jobs.library_item(seed, "MAT133")
        assert item is not None
        assert "2" in item["version_map"]
        version = item["version_map"]["2"]
        for kind in ("paper_docx", "paper_pdf", "scheme_docx", "scheme_pdf"):
            assert Path(version["files"][kind]).is_file()
        entry = jobs._cache_entry(seed, "MAT133")
        metadata = entry[1]["document_versions"]["2"]
        assert metadata["playbook_version"] == "2.0"
        assert metadata["validation"]["problems"] == []
        answers = json.loads(
            Path(metadata["answers"]).read_text(encoding="utf-8"))
        assert answers["count"] == 15
        assert len(answers["parts"]) == 15
        assert sum(part["marks"] for part in answers["parts"]) == (
            item["total_marks"])
        for part in answers["parts"]:
            assert part["answer"] or part["answer_latex"]
            assert part["provenance"] == "solver_verified"
