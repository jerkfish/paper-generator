from __future__ import annotations

import json
from pathlib import Path

from src.mat133.schema import QuestionLog
from src.mat133.taxonomy import (
    PRIORITY_1,
    PRIORITY_2,
    PRIORITY_3,
    SUBTOPIC_IDS,
    TOPIC_IDS,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "tracking" / "mat133"


def load(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def test_taxonomy_ids_are_unique_and_priorities_cover_all() -> None:
    assert len(TOPIC_IDS) == len(set(TOPIC_IDS))
    assert set(PRIORITY_1) | set(PRIORITY_2) | set(PRIORITY_3) <= set(TOPIC_IDS)
    assert PRIORITY_1 == ("functions", "inequalities", "absolute_value")
    assert PRIORITY_2 == ("lines", "circles", "parabolas")
    for topic, subtopics in SUBTOPIC_IDS.items():
        assert len(subtopics) == len(set(subtopics)), topic


def test_question_log_validates_and_is_complete() -> None:
    raw = load("question_log.json")
    log = QuestionLog.model_validate(raw)
    assert log.subject == "MAT133"
    assert log.schema_version == 1
    assert len(log.papers) == 41
    assert len(log.entries) >= 900
    assert len(log.patterns) >= 50
    unique_papers = {e.paper for e in log.entries if not e.duplicate_of}
    assert len(unique_papers) == 37
    assert log.validation.unique_papers == 37
    assert log.validation.unknown_topic == 0
    assert log.validation.unknown_subtopic == 0


def test_every_entry_uses_known_taxonomy_ids() -> None:
    log = QuestionLog.model_validate(load("question_log.json"))
    for entry in log.entries:
        assert entry.topic in TOPIC_IDS, entry.entry_id
        assert entry.subtopic in SUBTOPIC_IDS[entry.topic], entry.entry_id
        assert entry.entry_id == entry.entry_id.strip()
        assert entry.entry_id


def test_entry_ids_are_unique() -> None:
    log = QuestionLog.model_validate(load("question_log.json"))
    ids = [entry.entry_id for entry in log.entries]
    assert len(ids) == len(set(ids))


def test_patterns_have_blueprints_and_examples() -> None:
    log = QuestionLog.model_validate(load("question_log.json"))
    for pattern in log.patterns:
        assert pattern.frequency > 0
        assert pattern.example_entry_ids
        assert pattern.solution_blueprint, pattern.pattern_id
        assert pattern.pattern_id == f"{pattern.topic}.{pattern.subtopic}"


def test_schema_file_matches_model() -> None:
    schema = load("question_log.schema.json")
    assert schema["title"] == "QuestionLog"
    assert "QuestionEntry" in schema["$defs"]
    assert "PatternRecord" in schema["$defs"]
