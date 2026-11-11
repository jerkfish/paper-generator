"""Build the ICT450 question log and taxonomy from cached MinerU VLM output.

Deterministic: reads normalized.json and the Stage 1 register only. No LLM or
API calls. Topic tags are keyword-based and flagged for human review.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from src import config

MARKS_RE = re.compile(r"\((\d+)\s*marks?\)", re.I)
QUESTION_PREFIX_RE = re.compile(r"^\s*QUESTION\s+\d+\s*", re.I)

TOPICS = [
    ("sql", "SQL", [
        "sql", "select ", "insert ", "update ", "delete ", "create table",
        "drop table", "query", "join", "where", "group by", "order by",
        "relation schema", "write the sql", "write sql",
    ]),
    ("erd", "ERD", [
        "erd", "er diagram", "entity relationship", "entity-relationship",
        "entity", "relationship", "cardinality", "weak entity", "crow",
        "one-to-many", "many-to-many", "one-to-one",
    ]),
    ("normalization", "Normalization", [
        "normal form", "normalization", "normalisation", "1nf", "2nf", "3nf",
        "functional dependency", "denormal", "partial dependency",
        "transitive dependency",
    ]),
    ("relational", "Relational Data Model", [
        "relational model", "relation", "tuple", "attribute", "primary key",
        "foreign key", "candidate key", "schema", "integrity", "domain",
    ]),
    ("database_design", "Database Design", [
        "dblc", "sdlc", "database life cycle", "database design", "top-down",
        "bottom-up", "centralized", "decentralized", "systems development",
    ]),
    ("data_model", "Data Model", [
        "data model", "hierarchical", "network model", "object-oriented",
        "object oriented", "data modeling", "conceptual model", "logical model",
    ]),
    ("database_concept", "Database Concept", [
        "database", "dbms", "file-based", "file based", "data vs information",
        "data and information", "database system", "data management",
    ]),
]


def _topic(text: str) -> tuple[str, str, str, list[str]]:
    lowered = " ".join(text.lower().split())
    scores = []
    for key, label, words in TOPICS:
        hits = [word for word in words if word in lowered]
        if hits:
            scores.append((len(hits), key, label, hits))
    if not scores:
        return "other", "Other", "low", []
    scores.sort(key=lambda item: (-item[0], item[1]))
    best = scores[0]
    if len(scores) > 1 and scores[1][0] == best[0]:
        confidence = "medium"
    else:
        confidence = "high" if best[0] >= 2 else "medium"
    return best[1], best[2], confidence, best[3]


def _load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def build(root: Path) -> dict:
    tracking = root / "data" / "tracking" / "ict450"
    mineru = tracking / "mineru"
    register = _load(tracking / "papers_register.json", [])
    unique = [row for row in register
              if not row.get("error") and not row.get("duplicate_of")]
    entries = []
    papers = []
    topic_counts = Counter()
    topic_papers = defaultdict(set)
    topic_marks = Counter()
    for row in unique:
        paper_id = f"ICT450-{row['year']}-{str(row['month'])[:3]}"
        cache = next((mineru / paper_id).glob("vlm_*"), None)
        if cache is None:
            continue
        normalized = _load(cache / "review" / "normalized.json", {})
        questions = normalized.get("questions", [])
        assets = {asset["asset_id"]: asset
                  for asset in normalized.get("assets", [])}
        marks_values = []
        missing_marks = 0
        fallback_count = 0
        for question in questions:
            text = question.get("text", "")
            found = [int(value) for value in MARKS_RE.findall(text)]
            marks = sum(found) if found else None
            if marks is None:
                missing_marks += 1
            else:
                marks_values.append(marks)
            clean_text = QUESTION_PREFIX_RE.sub("", text).strip()
            topic, label, confidence, hits = _topic(clean_text)
            topic_counts[topic] += 1
            topic_papers[topic].add(paper_id)
            if marks is not None:
                topic_marks[topic] += marks
            refs = list(question.get("refs") or [])
            attached = [assets[aid] for aid in (question.get("assets") or [])
                        if aid in assets]
            fallback = list(question.get("fallback_assets") or [])
            fallback_count += len(fallback)
            entry = {
                "entry_id": question["question_id"],
                "paper_id": paper_id,
                "paper": row["source"],
                "month": row["month"],
                "year": row["year"],
                "question": question.get("number"),
                "part": "",
                "page": int(question.get("page_idx", 0)) + 1,
                "marks": marks,
                "marks_found": found,
                "text": clean_text,
                "subparts": question.get("subparts") or [],
                "refs": refs,
                "assets": [
                    {"asset_id": asset["asset_id"],
                     "kind": asset["kind"],
                     "label": asset.get("label", ""),
                     "page": int(asset.get("page_idx", 0)) + 1}
                    for asset in attached
                ],
                "fallback_assets": fallback,
                "topic": topic,
                "topic_label": label,
                "topic_confidence": confidence,
                "topic_keywords": hits,
                "mineru_report": (
                    f"data/tracking/ict450/mineru/{paper_id}/"
                    "EXTRACTION_REPORT.md"),
                "confidence": "high" if marks is not None else "medium",
                "review_flags": [],
            }
            if marks is None:
                entry["review_flags"].append("missing_marks")
            if fallback:
                entry["review_flags"].append("has_fallback_asset")
            if confidence != "high":
                entry["review_flags"].append("topic_needs_review")
            entries.append(entry)
        marks_sum = sum(marks_values) if marks_values else 0
        paper_flags = []
        if missing_marks:
            paper_flags.append("missing_marks")
        if fallback_count:
            paper_flags.append("has_fallback_asset")
        if marks_values and marks_sum != 100:
            paper_flags.append("marks_total_mismatch")
        papers.append({
            "paper_id": paper_id,
            "paper": row["source"],
            "month": row["month"],
            "year": row["year"],
            "pages": row["pages"],
            "text_source": "mineru-vlm",
            "duplicate_of": None,
            "question_count": len(questions),
            "marks_sum": marks_sum,
            "missing_marks": missing_marks,
            "fallback_assets": fallback_count,
            "question_ids": [question["question_id"] for question in questions],
            "mineru_report": (
                f"data/tracking/ict450/mineru/{paper_id}/"
                "EXTRACTION_REPORT.md"),
            "review_flags": paper_flags,
        })
    taxonomy = {
        "schema_version": 1,
        "subject": "ICT450",
        "source": "ICT200/ICT450 knowledge base deck map + MinerU VLM question text",
        "topics": [
            {
                "key": key,
                "label": label,
                "keywords": words,
                "question_count": topic_counts.get(key, 0),
                "paper_count": len(topic_papers.get(key, set())),
                "marks_sum": topic_marks.get(key, 0),
            }
            for key, label, words in TOPICS
        ] + [{
            "key": "other",
            "label": "Other",
            "keywords": [],
            "question_count": topic_counts.get("other", 0),
            "paper_count": len(topic_papers.get("other", set())),
            "marks_sum": topic_marks.get("other", 0),
        }],
        "generated_at": datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"),
    }
    validation = {
        "papers": len(papers),
        "questions": len(entries),
        "missing_marks": sum(1 for entry in entries
                             if entry["marks"] is None),
        "fallback_questions": sum(
            1 for entry in entries if entry["fallback_assets"]),
        "unresolved_refs": sum(
            1 for entry in entries for ref in entry["refs"]
            if not any(asset.get("label") == ref
                       for asset in entry["assets"])),
        "topic_other": topic_counts.get("other", 0),
        "topic_review": sum(1 for entry in entries
                            if entry["topic_confidence"] != "high"),
        "marks_total_mismatch": sum(
            1 for paper in papers
            if "marks_total_mismatch" in paper["review_flags"]),
        "warnings": [],
    }
    if validation["missing_marks"]:
        validation["warnings"].append(
            f"{validation['missing_marks']} questions have no detected marks")
    if validation["marks_total_mismatch"]:
        validation["warnings"].append(
            f"{validation['marks_total_mismatch']} papers do not sum to 100 marks")
    if validation["unresolved_refs"]:
        validation["warnings"].append(
            f"{validation['unresolved_refs']} referenced assets are unresolved")
    if validation["topic_other"]:
        validation["warnings"].append(
            f"{validation['topic_other']} questions have no topic match")
    question_log = {
        "schema_version": 1,
        "subject": "ICT450",
        "source_dir": "data/papers/ICT450",
        "generated_by": "scripts/build_ict450_question_log.py",
        "model": "mineru-vlm",
        "generated_at": datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"),
        "papers": papers,
        "entries": entries,
        "taxonomy": taxonomy,
        "validation": validation,
    }
    return question_log, taxonomy


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(config.PROJECT_ROOT))
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    tracking = root / "data" / "tracking" / "ict450"
    log, taxonomy = build(root)
    out = Path(args.out) if args.out else tracking / "question_log.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(log, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    (tracking / "taxonomy.json").write_text(
        json.dumps(taxonomy, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    print(json.dumps({
        "question_log": str(out),
        "taxonomy": str(tracking / "taxonomy.json"),
        "validation": log["validation"],
    }, indent=2))


if __name__ == "__main__":
    main()
