"""Content for the ICT450 V4 model answers."""
from __future__ import annotations

from . import concepts, design, erd, normalization, sql

KB_SOURCES = {
    "concepts": [
        "TOPIC 1 DATABASE CONCEPT (1).pdf",
        "TOPIC 2 DATA MODEL (1).pdf",
        "TOPIC 3 RELATIONAL DATA MODELstu.pdf",
    ],
    "design": [
        "TOPIC 2 DATA MODEL (1).pdf",
        "TOPIC 6 DATABASE DESIGN (1).pdf",
    ],
    "sql": ["TOPIC 7 SQL.pdf"],
    "normalization": ["TOPIC 5 NORMALIZATION  (1).pdf"],
    "erd": [
        "TOPIC 4 ERD_stu (2).pdf",
        "TOPIC 3 RELATIONAL DATA MODELstu.pdf",
    ],
}

ANSWERS: dict[str, dict] = {}
for module, keys in (
        (concepts, "concepts"),
        (design, "design"),
        (sql, "sql"),
        (normalization, "normalization"),
        (erd, "erd")):
    for answer in module.ANSWERS.values():
        answer["kb_sources"] = list(KB_SOURCES[keys])
    ANSWERS.update(module.ANSWERS)
