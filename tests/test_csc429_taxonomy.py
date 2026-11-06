"""CSC429 Stage-4 taxonomy and question log."""
from __future__ import annotations

import json

from src.subjects.csc429 import taxonomy


def _bank():
    return json.loads(taxonomy.BANK_PATH.read_text(encoding="utf-8"))


def test_taxonomy_classifies_the_main_question_types():
    bank = _bank()
    by_id = {question["question_id"]: question for question in bank["questions"]}
    expected = {
        "CSC429-2014-06-A3": "data_representation",
        "CSC429-2014-06-A5": "computer_architecture",
        "CSC429-2014-12-A9": "instruction_set_addressing",
        "CSC429-2016-06-A7": "memory_system",
        "CSC429-2016-12-A7": "io_system",
        "CSC429-2018-01-A10": "parallel_architecture",
        "CSC429-2018-06-A1": "computer_generations",
        "CSC429-2019-06-B1": "assembly_programming",
    }
    for question_id, topic in expected.items():
        assert taxonomy.classify(by_id[question_id])[0] == topic


def test_taxonomy_build_reconciles_every_paper(tmp_path, monkeypatch):
    subject = tmp_path / "subject.json"
    subject.write_text(json.dumps({"code": "CSC429"}), encoding="utf-8")
    monkeypatch.setattr(taxonomy, "TAXONOMY_PATH", tmp_path / "taxonomy.json")
    monkeypatch.setattr(taxonomy, "LOG_PATH", tmp_path / "question_log.json")
    monkeypatch.setattr(taxonomy, "SUMMARY_PATH", tmp_path / "summary.json")
    monkeypatch.setattr(taxonomy, "SUBJECT_PATH", subject)

    summary = taxonomy.build()
    assert summary["papers"] == 20
    assert summary["entries"] == 215
    assert summary["marks_total"] == 2000
    assert summary["papers_reconciled"] == 20
    assert summary["unsure_count"] == 6
    assert summary["topic_entries"].get("other", 0) == 0

    log = json.loads((tmp_path / "question_log.json").read_text(encoding="utf-8"))
    assert len(log["entries"]) == 215
    for entry in log["entries"]:
        assert entry["topic"] in taxonomy.TOPICS
        assert entry["topic"] != "other"
        assert entry["text"]
        assert entry["source_file"]
        assert entry["source_spans"]
        assert entry["marks"] in {5, 10, 15, 20}
    for paper in log["papers"]:
        assert paper["marks_complete"] is True
        assert paper["parsed_marks"] == 100

    fingerprint = json.loads(subject.read_text(encoding="utf-8"))["fingerprint"]
    assert fingerprint["question_log_entries"] == 215
    assert fingerprint["year_min"] == 2013
    assert fingerprint["year_max"] == 2026
