"""Registry-first platform, scaffolding, shared preprocess and Worker data."""
from __future__ import annotations

import json
from pathlib import Path

import docx
import pymupdf
import pytest

from src import config
from src.app import jobs, main
from src.subjects import forbidden, lifecycle, preprocess, templates
from src.subjects.registry import load_subjects
from scripts import new_subject


def _write_subject(root: Path, code: str, **overrides) -> dict:
    data = {
        "code": code,
        "title": f"{code} test subject",
        "status": "coming_soon",
        "order": 1,
        "has_practice_mode": True,
        "has_placeholders": True,
        "header_text": f"{code} TEST SUBJECT",
        "template_path": "",
        "fingerprint": {},
        "deck_map": {},
        "topic_deck_allowlist": {},
        "enabled_computed_generators": [],
    }
    data.update(overrides)
    path = root / "subjects" / code / "subject.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return data


def test_stub_subject_appears_in_ui_without_a_code_edit(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    root = tmp_path / "project"
    _write_subject(root, "TEST000", status="available", order=1)
    monkeypatch.setattr(config, "PROJECT_ROOT", root)
    monkeypatch.setattr(config, "WEB_CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(config, "WEB_RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(config, "OUTPUTS_DIR", tmp_path)

    client = TestClient(main.app)
    home = client.get("/")
    assert home.status_code == 200
    assert "TEST000" in home.text
    assert "TEST000 test subject" in home.text
    assert 'href="/test000"' in home.text
    assert client.get("/test000").status_code == 200
    assert client.get("/test000/library").status_code == 200
    assert client.get("/test000/generate").status_code == 200


def test_registry_capabilities_are_data_driven():
    subjects = load_subjects()
    assert subjects["CSC662"].subject_type == "A"
    assert subjects["CSC662"].capabilities["generation"] == "llm_theory"
    assert subjects["MAT133"].subject_type == "B"
    assert subjects["MAT133"].capabilities["generation"] == "deterministic"
    assert subjects["MAT133"].deterministic is True
    assert subjects["MAT133"].needs_llm is False
    assert subjects["CSC662"].plugins["plan"].startswith("src.subjects.csc662")
    assert subjects["MAT133"].plugins["prebuild"].startswith(
        "src.subjects.mat133")


def test_dry_run_scaffold_writes_nothing_and_keeps_coming_soon(tmp_path):
    root = tmp_path / "project"
    _write_subject(root, "BASE01")
    plan = new_subject.scaffold(root, "TEST000", "Test Subject", "C",
                                dry_run=True)
    assert plan["subject"]["status"] == "coming_soon"
    assert plan["subject"]["capabilities"]["generation"] == "hybrid"
    assert plan["subject"]["permissions"]["papers"]["allowed"] is False
    assert plan["lifecycle_state"]["stages"]["0_intake"]["status"] == "pending"
    assert not (root / "subjects" / "TEST000").exists()
    assert not (root / "src" / "subjects" / "test000").exists()
    assert "build_seed" in plan["files"][
        "src/subjects/test000/plugin.py"]


def test_scaffold_creates_lifecycle_and_status_reports_stage_zero(tmp_path):
    root = tmp_path / "project"
    _write_subject(root, "BASE01")
    plan = new_subject.scaffold(root, "TEST000", "Test Subject", "A")
    assert (root / "subjects/TEST000/subject.json").is_file()
    state = json.loads(
        (root / "subjects/TEST000/lifecycle_state.json").read_text(
            encoding="utf-8"))
    assert state["subject"] == "TEST000"
    assert state["stages"]["0_intake"]["human_approval"]["required"] is True
    assert state["unsure"]
    report = lifecycle.status_report(root, "TEST000")
    assert report["initialized"] is True
    assert report["next_stage"] == "0_intake"
    assert report["human_checkpoint"] is True
    assert any("unsure" in blocker for blocker in report["blockers"])


def test_lifecycle_status_script_reports_next_stage_and_blockers(tmp_path):
    from scripts import lifecycle_status

    root = tmp_path / "project"
    _write_subject(root, "BASE01")
    new_subject.scaffold(root, "TEST000", "Test Subject", "C")
    data = lifecycle_status.report(root, "TEST000")
    assert data["next_stage"] == "0_intake"
    assert data["type"] == "C"
    assert data["human_checkpoint"] is True
    assert any("unsure" in blocker for blocker in data["blockers"])
    assert data["stage_statuses"]["0_intake"] == "pending"


def test_scaffold_refuses_to_overwrite(tmp_path):
    root = tmp_path / "project"
    _write_subject(root, "BASE01")
    new_subject.scaffold(root, "TEST000", "Test Subject", "B")
    with pytest.raises(SystemExit):
        new_subject.scaffold(root, "TEST000", "Test Subject", "B")


def _pdf(path: Path, text: str) -> None:
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    document.save(str(path))
    document.close()


def test_preprocess_registers_dedupes_and_refuses_originals(monkeypatch,
                                                            tmp_path):
    papers_root = tmp_path / "data" / "papers"
    tracking_root = tmp_path / "data" / "tracking"
    monkeypatch.setattr(config, "PAPERS_ROOT", papers_root)
    monkeypatch.setattr(config, "TRACKING_DIR", tracking_root)
    papers = papers_root / "TEST000"
    papers.mkdir(parents=True)
    _pdf(papers / "first.pdf",
         "CS/JUNE 2024/TEST000\nTEST000 TEST SUBJECT\n" + "cover " * 20)
    (papers / "copy.pdf").write_bytes((papers / "first.pdf").read_bytes())
    _pdf(papers / "second.pdf",
         "CS/DECEMBER 2023/TEST000\nTEST000 TEST SUBJECT\n" + "cover " * 20)

    summary = preprocess.register(
        "TEST000", papers_dir=papers, tracking_dir=tracking_root / "test000",
        apply_rename=False, corpus=True, ocr=False)
    assert summary["total"] == 3
    assert summary["unique"] == 2
    assert summary["duplicates"] == 1
    assert summary["month_year_found"] == 2
    assert summary["renamed"] is False
    register = json.loads(
        (tracking_root / "test000" / "papers_register.json").read_text(
            encoding="utf-8"))
    assert {row["source"] for row in register} == {
        "first.pdf", "copy.pdf", "second.pdf"}
    assert any(row.get("duplicate_of") for row in register)
    assert (tracking_root / "test000" / "paper_text" / "index.json").is_file()

    with pytest.raises(SystemExit):
        preprocess.require_working_copies(tmp_path / "originals")


def test_preprocess_apply_rename_is_opt_in(tmp_path, monkeypatch):
    papers_root = tmp_path / "data" / "papers"
    tracking_root = tmp_path / "data" / "tracking"
    monkeypatch.setattr(config, "PAPERS_ROOT", papers_root)
    monkeypatch.setattr(config, "TRACKING_DIR", tracking_root)
    papers = papers_root / "TEST000"
    papers.mkdir(parents=True)
    _pdf(papers / "noisy-name.pdf",
         "CS/MAY 2022/TEST000\nTEST000 TEST SUBJECT\n" + "cover " * 20)
    summary = preprocess.register(
        "TEST000", papers_dir=papers, tracking_dir=tracking_root / "test000",
        apply_rename=True, ocr=False)
    assert summary["renamed"] is True
    assert (papers / "TEST000 MAY 2022.pdf").is_file()


def test_template_check_and_install(tmp_path):
    root = tmp_path / "project"
    _write_subject(root, "TEST000")
    source = tmp_path / "template.docx"
    document = docx.Document()
    document.add_paragraph("TEST000 TEST SUBJECT")
    document.add_paragraph("cover")
    document.sections[0].header.paragraphs[0].text = "TEST000 header"
    document.save(str(source))
    check = templates.check_template(source)
    assert check["xml_valid"] is True
    assert check["headers"] >= 1
    assert not check["problems"]
    result = templates.install_template(
        root, "TEST000", source, apply=True)
    assert result["written"] is True
    target = root / "data/reference/TEST000/TEST000 TEMPLATE.docx"
    assert target.is_file()
    data = json.loads(
        (root / "subjects/TEST000/subject.json").read_text(encoding="utf-8"))
    assert data["template_path"] == "data/reference/TEST000/TEST000 TEMPLATE.docx"


def test_forbidden_scan_catches_other_subject_and_private_path(tmp_path):
    path = tmp_path / "deliverable.txt"
    path.write_text("CSC662 leaked\ndata/reference/secret\n", encoding="utf-8")
    result = forbidden.scan([path], "TEST000", config.PROJECT_ROOT)
    tokens = {hit["token"] for hit in result["hits"]}
    assert "CSC662" in tokens
    assert "data/reference" in tokens


def test_job_public_renders_subject_planner_shape():
    job = jobs.Job(id="shape", mode="realistic", seed=1, computed_marks=None,
                   subject="MAT133", total_slots=3)
    job.progress = [
        {"question": "Q1", "slot": "Q1a", "status": "accepted",
         "message": "functions"},
        {"question": "Q1", "slot": "Q1b", "status": "accepted",
         "message": "lines"},
        {"question": "Q2", "slot": "Q2a", "status": "accepted",
         "message": "circles"},
    ]
    job.status = "done"
    public = job.public()
    assert [row["name"] for row in public["rows"]] == ["Q1", "Q2"]
    assert [cell["label"] for cell in public["rows"][0]["cells"]] == ["a", "b"]


def test_generated_subjects_json_drives_routes(tmp_path):
    from scripts.build_public_bundle import _write_manifests

    item = {
        "subject": "MAT133", "seed": 1, "mode": "realistic",
        "computed_display": 0, "total_marks": 68, "marks_value": 68,
        "has_practice_mode": False, "has_placeholders": False,
        "year": 2026, "accepted": 15, "placeholders": 0,
        "topic_marks": {"functions": 9}, "topic_mix": "FUN 9",
        "downloads": {
            "paper_docx": "MAT133 Seed 01 2026.docx",
            "paper_pdf": "MAT133 Seed 01 2026.pdf",
            "scheme_docx": "MAT133 Seed 01 2026 - Marking Scheme.docx",
            "scheme_pdf": "MAT133 Seed 01 2026 - Marking Scheme.pdf",
        },
    }
    _write_manifests(tmp_path, {"MAT133": [item]})
    data = json.loads((tmp_path / "subjects.json").read_text(encoding="utf-8"))
    by_code = {row["code"]: row for row in data["subjects"]}
    assert by_code["MAT133"]["route"] == "mat133"
    assert by_code["MAT133"]["available"] is True
    assert by_code["MAT133"]["routes"]["library"] == "/mat133/library"
    assert by_code["CSC662"]["route"] == "csc662"
    assert by_code["CSC662"]["available"] is True
