"""CSC402 stage-4 taxonomy and question log.

Deterministic parser for the 21 unique CSC402 papers.  It splits each paper
into PART A/B/C, extracts QUESTION blocks and lettered subparts, associates
``(N marks)`` with the nearest subpart, and classifies each block against a
small paper-derived topic taxonomy.  Part A is logged as one aggregate MCQ
entry because the OCR/text layer does not reliably preserve individual MCQ
stems; that limitation is recorded as an ``unsure`` item.

    uv run python -m src.subjects.csc402.taxonomy
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from src import config

SUBJECT = "CSC402"
TRACKING = config.TRACKING_DIR / "csc402"
REGISTER = TRACKING / "papers_register.json"
TEXT_DIR = TRACKING / "paper_text"
TAXONOMY_PATH = TRACKING / "taxonomy.json"
LOG_PATH = TRACKING / "question_log.json"
SUMMARY_PATH = TRACKING / "taxonomy_summary.json"

MONTH_NUMBER = {
    "JANUARY": 1, "FEBRUARY": 2, "MARCH": 3, "APRIL": 4, "MAY": 5,
    "JUNE": 6, "JULY": 7, "AUGUST": 8, "SEPTEMBER": 9, "OCTOBER": 10,
    "NOVEMBER": 11, "DECEMBER": 12,
}

TOPICS = {
    "fundamentals": {
        "title": "Programming fundamentals",
        "keywords": [
            "algorithm", "pseudocode", "pseudo-code", "flowchart",
            "programming paradigm", "pdlc", "program development life cycle",
            "compilation", "compiler", "interpreter", "high-level language",
            "source code", "machine language",
        ],
    },
    "data_types": {
        "title": "Data types, variables and expressions",
        "keywords": [
            "data type", "identifier", "variable", "constant", "declaration",
            "operator", "expression", "int", "float", "double", "char",
            "bool", "string", "assignment", "initialise", "initialize",
        ],
    },
    "control_structures": {
        "title": "Control structures",
        "keywords": [
            "if", "else", "switch", "for", "while", "do while", "do-while",
            "loop", "selection", "repetition", "nested", "sentinel",
            "condition", "iteration",
        ],
    },
    "functions": {
        "title": "Functions and modular programming",
        "keywords": [
            "function", "parameter", "argument", "return", "void", "scope",
            "prototype", "call", "pass by value", "pass by reference",
        ],
    },
    "arrays": {
        "title": "Arrays and collections",
        "keywords": [
            "array", "subscript", "index", "parallel array", "search",
            "sort", "two-dimensional", "2d array", "element",
        ],
    },
    "input_output": {
        "title": "Input, output and streams",
        "keywords": [
            "cin", "cout", "input", "output", "format", "setw", "stream",
            "prompt", "display", "read", "print",
        ],
    },
    "debugging_testing": {
        "title": "Debugging, testing and tracing",
        "keywords": [
            "debug", "error", "syntax", "runtime", "run-time", "logic error",
            "test", "trace", "dry run", "correct the",
        ],
    },
    "file_handling": {
        "title": "File handling",
        "keywords": [
            "file", "fstream", "eof", "open", "close", "read from",
            "write to", "append",
        ],
    },
    "structures": {
        "title": "Structures and data organisation",
        "keywords": [
            "struct", "structure", "record", "member", "object", "class",
        ],
    },
    "other": {"title": "Other / unclassified", "keywords": []},
}

PART_RE = re.compile(r"PART\s*([ABC])\s*\(\s*([^)]*?)\s*\)", re.I)
QUESTION_RE = re.compile(r"\bQUESTION\s+(\d+)\b", re.I)
SUBPART_RE = re.compile(r"(?<![A-Za-z0-9])([a-h])\)\s+", re.I)
MARKS_RE = re.compile(
    r"\(\s*['‘’]?\s*(\d+)\s*marks?\s*\)",
    re.I)
MCQ_COUNT_RE = re.compile(
    r"PART\s*A\s*\(\s*(\d+)\s*Questions?\s*\)", re.I)


def normalise(text: str) -> str:
    text = text.replace("\r", "\n").replace("\f", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text


def clean_text(text: str) -> str:
    text = re.sub(r"CONFIDENTIAL", " ", text, flags=re.I)
    text = re.sub(r"CS\s*/\s*[A-Z]{3,9}\s+\d{4}\s*/\s*CSC402", " ", text,
                  flags=re.I)
    text = re.sub(r"@?\s*Hak Cipta Universiti Teknologi MARA", " ", text,
                  flags=re.I)
    text = re.sub(r"\b\d{1,2}\s+(?=CS\s*/)", " ", text)
    text = re.sub(r"\b\d{1,2}\s+(?=CONFIDENTIAL)", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def classify(text: str) -> tuple[str, dict[str, int], str]:
    lowered = f" {text.lower()} "
    scores: dict[str, int] = {}
    for topic, spec in TOPICS.items():
        score = 0
        for keyword in spec["keywords"]:
            pattern = r"\b" + re.escape(keyword).replace(r"\ ", r"\s+") + r"\b"
            matches = len(re.findall(pattern, lowered, flags=re.I))
            if matches:
                score += matches * (2 if " " in keyword or "-" in keyword else 1)
        scores[topic] = score
    best = max(scores, key=lambda topic: (scores[topic], topic != "other"))
    if scores[best] == 0:
        return "other", scores, "low"
    top = scores[best]
    confidence = "high" if top >= 4 else "medium"
    return best, scores, confidence


def _marks(text: str) -> list[int]:
    return [int(value) for value in MARKS_RE.findall(text)]


def _split_subparts(block: str) -> list[tuple[str, str]]:
    matches = list(SUBPART_RE.finditer(block))
    if not matches:
        return []
    parts = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(block)
        parts.append((match.group(1).lower(), block[start:end].strip()))
    return parts


def _paper_id(row: dict) -> str:
    year = int(row.get("year") or 0)
    month = MONTH_NUMBER.get(str(row.get("month") or "").upper(), 0)
    return f"{SUBJECT}-{year:04d}-{month:02d}"


def _entry(paper: str, paper_id: str, part: str, question: str,
           subpart: str, slot: str, text: str, marks: int | None,
           topic: str, scores: dict[str, int], confidence: str,
           granularity: str, source_file: str, source_kind: str) -> dict:
    return {
        "paper": paper,
        "paper_id": paper_id,
        "part": part,
        "question": question,
        "subpart": subpart,
        "slot": slot,
        "text": text[:1800],
        "marks": marks,
        "granularity": granularity,
        "topic": topic,
        "topic_scores": scores,
        "confidence": confidence,
        "source_file": source_file,
        "source_kind": source_kind,
    }


def parse_paper(row: dict) -> dict:
    paper = Path(str(row.get("paper") or "")).stem
    paper_id = _paper_id(row)
    text_path = Path(str(row.get("text_file") or ""))
    if not text_path.exists():
        text_path = TEXT_DIR / f"{paper}.txt"
    source_text = (text_path.read_text(encoding="utf-8", errors="ignore")
                   if text_path.exists() else "")
    text = normalise(source_text)
    part_matches = [
        match for match in PART_RE.finditer(text)
        if "MARK" in match.group(2).upper()
    ]
    part_marks = {}
    for match in part_matches:
        header_marks = re.search(r"(\d+)\s*MARKS?", match.group(2), re.I)
        if header_marks:
            part_marks[match.group(1).upper()] = int(header_marks.group(1))
    entries: list[dict] = []
    issues: list[str] = []
    source_file = str(text_path)

    for index, match in enumerate(part_matches):
        part = match.group(1).upper()
        start = match.end()
        end = (part_matches[index + 1].start()
               if index + 1 < len(part_matches) else len(text))
        block = clean_text(text[start:end])
        if not block:
            continue
        part_mark = part_marks.get(part)
        if part == "A":
            count_match = MCQ_COUNT_RE.search(text) or MCQ_COUNT_RE.search(
                source_text)
            count = int(count_match.group(1)) if count_match else 10
            topic, scores, _ = classify(block)
            entries.append(_entry(
                paper, paper_id, part, "A", "MCQ", "A", block, part_mark,
                topic, scores, "low", "part", source_file,
                row.get("source_kind", "")))
            continue

        unreliable_subparts = 0
        question_matches = list(QUESTION_RE.finditer(block))
        if not question_matches:
            topic, scores, _ = classify(block)
            entries.append(_entry(
                paper, paper_id, part, part, "", part, block, part_mark,
                topic, scores, "low", "part", source_file,
                row.get("source_kind", "")))
            issues.append(f"{paper}: PART {part} had no QUESTION markers")
            continue

        for q_index, q_match in enumerate(question_matches):
            q_start = q_match.end()
            q_end = (question_matches[q_index + 1].start()
                     if q_index + 1 < len(question_matches) else len(block))
            q_block = block[q_start:q_end].strip()
            q_number = q_match.group(1)
            question_label = f"{part}{q_number}"
            subparts = _split_subparts(q_block)
            if not subparts:
                topic, scores, confidence = classify(q_block)
                marks = sum(_marks(q_block)) or None
                entries.append(_entry(
                    paper, paper_id, part, question_label, "", question_label,
                    q_block, marks, topic, scores,
                    confidence if marks else "low", "question", source_file,
                    row.get("source_kind", "")))
                if marks is None:
                    issues.append(
                        f"{paper}: {question_label} has no parseable marks")
                continue
            subpart_rows = []
            for subpart, sub_text in subparts:
                sub_marks = sum(_marks(sub_text)) or None
                subpart_rows.append({
                    "label": subpart,
                    "text": sub_text[:1200],
                    "marks": sub_marks,
                })
                if not sub_text:
                    unreliable_subparts += 1
            marks_list = _marks(q_block)
            marks = sum(marks_list) if marks_list else None
            topic, scores, topic_confidence = classify(q_block)
            confidence = topic_confidence if marks else "low"
            entry = _entry(
                paper, paper_id, part, question_label, "", question_label,
                q_block, marks, topic, scores, confidence, "question",
                source_file, row.get("source_kind", ""))
            entry["subparts"] = subpart_rows
            entries.append(entry)
            if marks is None:
                issues.append(
                    f"{paper}: {question_label} has no parseable marks")
        if unreliable_subparts:
            issues.append(
                f"{paper}: {unreliable_subparts} question(s) have "
                "unreliable subpart text order")

    expected = sum(part_marks.values()) if part_marks else None
    parsed = sum(entry["marks"] for entry in entries
                 if isinstance(entry.get("marks"), int))
    complete = expected is not None and parsed == expected
    if not part_matches:
        issues.append(f"{paper}: no PART A/B/C marks headers found")
    elif not complete:
        issues.append(
            f"{paper}: parsed marks {parsed} do not reconcile with part "
            f"headers {expected}")
    return {
        "paper": paper,
        "paper_id": paper_id,
        "file": source_file,
        "source_kind": row.get("source_kind", ""),
        "part_marks": part_marks,
        "expected_marks": expected,
        "parsed_marks": parsed,
        "marks_complete": complete,
        "entry_count": len(entries),
        "part_a_aggregate": any(
            entry["part"] == "A" for entry in entries),
        "issues": issues,
        "entries": entries,
    }


def build() -> dict:
    register = json.loads(REGISTER.read_text(encoding="utf-8"))
    rows = [row for row in register if not row.get("duplicate_of")]
    papers = [parse_paper(row) for row in rows]
    entries = [entry for paper in papers for entry in paper["entries"]]
    topic_stats = {}
    for topic, spec in TOPICS.items():
        topic_entries = [entry for entry in entries if entry["topic"] == topic]
        topic_stats[topic] = {
            "title": spec["title"],
            "keywords": spec["keywords"],
            "observed_marks": sum(entry["marks"] or 0 for entry in topic_entries),
            "observed_entries": len(topic_entries),
        }
    part_stats = {}
    for part in ("A", "B", "C"):
        part_papers = [paper for paper in papers
                       if part in paper["part_marks"]]
        part_stats[part] = {
            "papers": len(part_papers),
            "marks_values": sorted({
                paper["part_marks"][part] for paper in part_papers}),
        }
    unsure = [issue for paper in papers for issue in paper["issues"]]
    part_a_papers = [paper["paper_id"] for paper in papers
                     if paper["part_a_aggregate"]]
    if part_a_papers:
        unsure.insert(
            0,
            f"{len(part_a_papers)} papers: PART A is logged as one aggregate "
            "MCQ entry per paper; individual MCQ stems/topics were not "
            "reconstructed from the OCR/text layer.")
    questions_without_marks = [
        f"{entry['paper_id']} {entry['slot']}" for entry in entries
        if entry["marks"] is None
    ]
    if questions_without_marks:
        unsure.append(
            "Questions without parseable marks: "
            + ", ".join(questions_without_marks))
    summary = {
        "subject": SUBJECT,
        "generated_by": "src.subjects.csc402.taxonomy",
        "source": str(TEXT_DIR),
        "papers": len(papers),
        "entries": len(entries),
        "expected_marks_total": sum(paper["expected_marks"] or 0
                                    for paper in papers),
        "parsed_marks_total": sum(paper["parsed_marks"] for paper in papers),
        "papers_reconciled": sum(1 for paper in papers
                                 if paper["marks_complete"]),
        "papers_with_issues": [paper["paper_id"] for paper in papers
                               if paper["issues"]],
        "part_a_aggregate_papers": part_a_papers,
        "questions_without_marks": questions_without_marks,
        "topic_stats": topic_stats,
        "part_stats": part_stats,
        "unsure": unsure,
    }
    taxonomy = {
        "subject": SUBJECT,
        "version": 1,
        "generated_by": "src.subjects.csc402.taxonomy",
        "topics": topic_stats,
        "part_structure": part_stats,
        "total_marks": summary["expected_marks_total"],
        "paper_count": len(papers),
        "unsure": unsure,
    }
    log = {
        "subject": SUBJECT,
        "version": 1,
        "generated_by": "src.subjects.csc402.taxonomy",
        "source": str(TEXT_DIR),
        "papers": [
            {key: value for key, value in paper.items() if key != "entries"}
            for paper in papers
        ],
        "entries": entries,
    }
    TAXONOMY_PATH.write_text(
        json.dumps(taxonomy, indent=2, ensure_ascii=False), encoding="utf-8")
    LOG_PATH.write_text(
        json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    summary = build()
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if args.json:
        return


if __name__ == "__main__":
    main()
