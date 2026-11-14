"""Versioned Library documents (v1 beside a later playbook version)."""
from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.app import jobs
from src.app.filenames import download_filename
from src.subjects.registry import get_subject

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "src/app/templates"


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


def test_public_bundle_can_restrict_document_versions():
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
