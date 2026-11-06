"""Stage-4 taxonomy and question log for CSC429.

The question bank is already a verbatim, geometry-checked extraction. This
module only classifies each bank item against a small paper-derived taxonomy;
it never rewrites question text and never calls a model.

Run::

    uv run python -m src.subjects.csc429.taxonomy
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from src import config

SUBJECT = "CSC429"
TRACKING = config.TRACKING_DIR / "csc429"
BANK_PATH = TRACKING / "question_bank_draft.json"
STAGE1_REPORT = TRACKING / "stage1_report.json"
TAXONOMY_PATH = TRACKING / "taxonomy.json"
LOG_PATH = TRACKING / "question_log.json"
SUMMARY_PATH = TRACKING / "taxonomy_summary.json"
SUBJECT_PATH = config.PROJECT_ROOT / "subjects" / SUBJECT / "subject.json"
PAPER_TOTAL = 100

TOPICS = {
    "computer_generations": {
        "title": "Computer generations and history",
        "description": "Generations, early calculating machines, inventors and the historical evolution of computers.",
        "keywords": [
            "computer generation", "history", "inventor", "Babbage",
            "Difference Engine", "Analytical Engine", "Step Reckoner",
            "Jacquard", "ENIAC", "EDVAC", "IAS machine", "vacuum tube",
            "transistor", "integrated circuit", "personal computer", "GUI",
        ],
    },
    "computer_architecture": {
        "title": "Computer architecture and CPU organisation",
        "description": "Von Neumann architecture, computer components, CPU registers, machine/instruction cycle, buses and system interconnection.",
        "keywords": [
            "Von Neumann architecture", "computer components", "CPU",
            "control unit", "ALU", "register", "program counter",
            "instruction register", "accumulator", "machine cycle",
            "instruction cycle", "bus", "bus timing", "system interconnection",
            "organisation", "architecture",
        ],
    },
    "data_representation": {
        "title": "Data representation and number systems",
        "description": "Number bases, signed arithmetic, complements, IEEE 754 floating point, bit/byte/word/block and character encoding.",
        "keywords": [
            "binary", "decimal", "hexadecimal", "octal", "number base",
            "sign and magnitude", "one's complement", "two's complement",
            "floating point", "IEEE 754", "bit", "byte", "word", "block",
            "ASCII", "character representation",
        ],
    },
    "instruction_set_addressing": {
        "title": "Instruction formats and addressing modes",
        "description": "Instruction operands, effective addresses and addressing-mode tables for LOAD/AC behaviour.",
        "keywords": [
            "addressing mode", "mode of addressing", "addressing technique",
            "opcode", "operand", "effective address", "direct addressing",
            "indirect addressing", "immediate addressing", "indexed addressing",
        ],
    },
    "memory_system": {
        "title": "Memory hierarchy and cache",
        "description": "Cache mapping and replacement, SRAM/DRAM, main memory, storage access methods and memory selection.",
        "keywords": [
            "cache", "main memory", "memory hierarchy", "SRAM", "DRAM",
            "mapping function", "direct mapping", "associative mapping",
            "replacement algorithm", "tag", "line number", "storage device",
            "access method", "memory selection", "write policy",
        ],
    },
    "io_system": {
        "title": "Input/output and interrupts",
        "description": "I/O modules, programmed/interrupt-driven I/O, DMA, polling, buffering, device interfaces and interrupt handling.",
        "keywords": [
            "input/output", "I/O module", "interrupt", "DMA",
            "direct memory access", "polling", "buffering", "USB",
            "hot connection", "external device", "peripheral", "keyboard",
            "touch screen", "interface",
        ],
    },
    "parallel_architecture": {
        "title": "Parallel and multiprocessor architecture",
        "description": "Parallel processor classification, SISD/SIMD/MIMD, SMP, NUMA, clusters and coupled multiprocessor systems.",
        "keywords": [
            "parallel processor", "multiprocessor", "multiprocessing",
            "multiprogramming", "SMP", "NUMA", "cluster", "MIMD", "SIMD",
            "SISD", "MISD", "tightly coupled", "loosely coupled",
            "processor organisation",
        ],
    },
    "assembly_programming": {
        "title": "Assembly-language programming",
        "description": "Part B assembly tasks: translate an equation into zero-, one-, two- or three-address programs using the supplied instruction table.",
        "keywords": [
            "assembly language", "zero-address", "one-address", "two-address",
            "three-address", "machine instruction", "program",
        ],
    },
    "other": {
        "title": "Other / unclassified",
        "description": "Questions with no confident taxonomy match.",
        "keywords": [],
    },
}

# Rules are deliberately ordered. Earlier, more specific rules win; this keeps
# a history question that mentions binary from becoming a data-representation
# item, and keeps a cache question that mentions CPU from becoming an
# architecture item.
RULES = [
    ("instruction_set_addressing", re.compile(
        r"addressing\s+(?:mode|modes|technique)|mode\s+of\s+addressing|"
        r"effective\s+address|direct\s+addressing|indirect\s+addressing|"
        r"immediate\s+addressing|indexed\s+addressing", re.I)),
    ("parallel_architecture", re.compile(
        r"parallel|multi[- ]?processor|multiprocessor|multiprocessing|"
        r"multiprogramming|\bsmp\b|symmetric\s+multiprocessor|\bnuma\b|"
        r"non[- ]?uniform\s+memory\s+access|cluster|\bmimd\b|\bsimd\b|"
        r"\bsisd\b|\bmisd\b|tightly\s+coupled|loosely\s+coupled|"
        r"processor\s+organization|multiple\s+processor", re.I)),
    ("computer_generations", re.compile(
        r"inventor|who\s+is\s+the\s+inventor|invented\s+the\s+first|"
        r"father\s+of\s+(?:the\s+)?computer|"
        r"first\s+automatic\s+electronic\s+digital\s+computer|"
        r"what\s+is\s+x\s+machine|prominent\s+machines|babbage|"
        r"difference\s+engine|step\s+reckoner|\beniac\b|"
        r"label\s+the\s+correct\s+computer\s+generation|"
        r"identify\s+the\s+correct\s+generation", re.I)),
    ("computer_architecture", re.compile(
        r"machine\s+cycle|instruction\s+cycle|"
        r"computer\s+systems?\s+interconnecti|"
        r"computer\s+consists\s+of\s+four\s+main\s+components|"
        r"four\s+main\s+components", re.I)),
    ("computer_architecture", re.compile(r"von\s+neuman", re.I)),
    ("data_representation", re.compile(
        r"binary\s+(?:number|numbering)\s+system|"
        r"binary\s+used\s+instead\s+of\s+decimal|why\s+is\s+binary|"
        r"binary\s+number\s+representation", re.I)),
    ("computer_generations", re.compile(
        r"generation|jacquard|personal\s+computer|"
        r"graphical\s+user\s+interface|\bgui\b|history\s+of\s+computer|"
        r"computer\s+evolution", re.I)),
    ("io_system", re.compile(
        r"interrupt|\bdma\b|direct\s+memory\s+access|polling|buffer(?:ing)?|"
        r"\b[il1]/[o0]\b|io\s+module|"
        r"input\s+(?:and\s+)?output\s+(?:module|technique|device|controller|"
        r"problem|interface)|input[/-]output|\bperipheral(s)?\b|\busb\b|"
        r"hot\s+connection|keyboard|touch\s+screen|printer|external\s+device|"
        r"interfaces?\s+to\s+external|device\s+controller", re.I)),
    ("memory_system", re.compile(
        r"\bcache\b|main\s+memory|memory\s+hierarchy|\bsram\b|\bdram\b|"
        r"replacement\s+algorithm|mapping\s+function|direct\s+mapping|"
        r"associative\s+mapping|set\s+associative|\btag\b|line\s+number|"
        r"memory\s+address|storage\s+device|access\s+method|"
        r"memory\s+selection|memory\s+type|memory\s+location|address\s+bits?|"
        r"cache\s+block|write\s+(?:policy|through|back)", re.I)),
    ("computer_architecture", re.compile(
        r"von\s+neumann|\barchitecture\b|organization|\bcpu\b|"
        r"central\s+processing\s+unit|control\s+unit|"
        r"arithmetic\s*(?:/|and)?\s*logic|\balu\b|\bregister(s)?\b|"
        r"program\s+counter|instruction\s+register|accumulator|"
        r"\bbus(?:es)?\b|system\s+interconnection|interconnection|"
        r"computer\s+components|components?\s+of\s+(?:a\s+)?computer", re.I)),
    ("data_representation", re.compile(
        r"floating[- ]?point|\bieee\b|sign\s+and\s+magnitude|"
        r"[12]'?s\s+complement|one'?s\s+complement|two'?s\s+complement|"
        r"number\s+bases?|binary\s+number|hexadecimal|decimal|octal|"
        r"\bascii\b|\bbit\b|\bbyte\b|\bword\b|\bblock\b|unicode|"
        r"character\s+representation|"
        r"\b[0-9A-Fa-f]{1,4}\.[0-9A-Fa-f]*[Hh]\b", re.I)),
]

STRONG_TIERS = 5


def normalise(text: str) -> str:
    return " ".join(str(text).split())


def classify(question: dict) -> tuple[str, str, str, int]:
    """Return ``(topic, matched_text, confidence, rule_index)``."""
    if question.get("part") == "B":
        return "assembly_programming", "PART B", "high", -1
    text = normalise(question.get("text", "")).lower()
    for index, (topic, pattern) in enumerate(RULES):
        match = pattern.search(text)
        if match:
            confidence = "high" if index < STRONG_TIERS else "medium"
            return topic, match.group(0), confidence, index
    return "other", "", "low", len(RULES)


def _source_spans(question: dict) -> list[dict]:
    return [
        {"page": span.get("page"), "bbox": span.get("bbox"),
         "text": span.get("text")}
        for span in question.get("source_spans") or []
    ]


def _paper_meta(bank: dict) -> dict[str, dict]:
    return {paper["paper_id"]: paper for paper in bank.get("papers", [])}


def _stage1_unsure() -> list[dict]:
    if not STAGE1_REPORT.exists():
        return []
    try:
        payload = json.loads(STAGE1_REPORT.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return list(payload.get("unsure") or [])


def build() -> dict:
    bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))
    papers = _paper_meta(bank)
    entries = []
    topic_stats = {
        key: {
            "title": spec["title"],
            "description": spec["description"],
            "keywords": spec["keywords"],
            "observed_entries": 0,
            "observed_marks": 0,
            "papers": set(),
            "by_part": Counter(),
            "confidence": Counter(),
        }
        for key, spec in TOPICS.items()
    }
    paper_rows = []
    topic_counter: Counter = Counter()
    confidence_counter: Counter = Counter()
    paper_topics: dict[str, Counter] = defaultdict(Counter)
    paper_marks: dict[str, int] = defaultdict(int)

    seen_ids = set()
    for question in bank.get("questions", []):
        question_id = question["question_id"]
        if question_id in seen_ids:
            raise RuntimeError(f"duplicate question id: {question_id}")
        seen_ids.add(question_id)
        topic, matched, confidence, rule_index = classify(question)
        meta = papers.get(question["paper_id"], {})
        marks = question.get("marks")
        if marks is None:
            confidence = "low"
        entry = {
            "question_id": question_id,
            "paper_id": question["paper_id"],
            "source_file": question.get("source_file", ""),
            "source_kind": meta.get("source_kind", ""),
            "part": question.get("part", ""),
            "question_no": question.get("question_no"),
            "slot": question.get("slot", ""),
            "marks": marks,
            "marks_source": question.get("marks_source", ""),
            "topic": topic,
            "topic_label": TOPICS[topic]["title"],
            "classification_confidence": confidence,
            "matched_rule": matched,
            "rule_tier": rule_index,
            "text": question.get("text", ""),
            "text_sha256": question.get("text_sha256", ""),
            "pages": question.get("pages", []),
            "asset_ids": question.get("asset_ids", []),
            "asset_status": question.get("asset_status", ""),
            "figure_refs": question.get("figure_refs", []),
            "review_flags": question.get("review_flags", []),
            "subparts": [
                {
                    "label": subpart.get("label"),
                    "text": subpart.get("text", ""),
                    "marks": subpart.get("marks"),
                    "marks_source": subpart.get("marks_source", ""),
                    "bbox": subpart.get("bbox"),
                    "figure_refs": subpart.get("figure_refs", []),
                    "asset_ids": subpart.get("asset_ids", []),
                }
                for subpart in question.get("subparts") or []
            ],
            "source_spans": _source_spans(question),
        }
        entries.append(entry)
        topic_stats[topic]["observed_entries"] += 1
        topic_stats[topic]["observed_marks"] += marks or 0
        topic_stats[topic]["papers"].add(question["paper_id"])
        topic_stats[topic]["by_part"][question.get("part", "")] += 1
        topic_stats[topic]["confidence"][confidence] += 1
        topic_counter[topic] += 1
        confidence_counter[confidence] += 1
        paper_topics[question["paper_id"]][topic] += 1
        paper_marks[question["paper_id"]] += marks or 0

    for paper_id, meta in papers.items():
        parsed = paper_marks.get(paper_id, 0)
        rows = [entry for entry in entries if entry["paper_id"] == paper_id]
        paper_rows.append({
            "paper_id": paper_id,
            "source_file": meta.get("source_file", ""),
            "source_kind": meta.get("source_kind", ""),
            "question_count": len(rows),
            "parsed_marks": parsed,
            "expected_marks": PAPER_TOTAL,
            "marks_complete": parsed == PAPER_TOTAL,
            "topics": dict(paper_topics.get(paper_id, {})),
            "unsure": [
                entry["question_id"] for entry in rows
                if entry["classification_confidence"] == "low"
                or entry["marks"] is None
            ],
        })

    unsure = list(_stage1_unsure())
    for row in paper_rows:
        if not row["marks_complete"]:
            unsure.append({
                "code": "marks_mismatch",
                "paper_id": row["paper_id"],
                "detail": f"parsed {row['parsed_marks']} marks, expected "
                          f"{row['expected_marks']}",
            })
    for entry in entries:
        if entry["topic"] == "other":
            unsure.append({
                "code": "unclassified_question",
                "paper_id": entry["paper_id"],
                "question_id": entry["question_id"],
                "detail": "no taxonomy rule matched",
            })

    topic_payload = {}
    for key, stats in topic_stats.items():
        topic_payload[key] = {
            "title": stats["title"],
            "description": stats["description"],
            "keywords": stats["keywords"],
            "observed_entries": stats["observed_entries"],
            "observed_marks": stats["observed_marks"],
            "papers": sorted(stats["papers"]),
            "by_part": dict(stats["by_part"]),
            "confidence": dict(stats["confidence"]),
        }

    part_marks: dict[str, list[int]] = defaultdict(list)
    part_questions: dict[str, list[int]] = defaultdict(list)
    for paper_id in papers:
        rows = [entry for entry in entries if entry["paper_id"] == paper_id]
        for part in ("A", "B"):
            part_rows = [entry for entry in rows if entry["part"] == part]
            if part_rows:
                part_marks[part].append(sum(row["marks"] or 0
                                            for row in part_rows))
                part_questions[part].append(len(part_rows))
    part_structure = {
        part: {
            "papers": len(part_questions[part]),
            "question_counts": sorted(set(part_questions[part])),
            "marks_values": sorted(set(part_marks[part])),
        }
        for part in ("A", "B") if part_questions[part]
    }

    summary = {
        "subject": SUBJECT,
        "generated_by": "src.subjects.csc429.taxonomy",
        "source": "data/tracking/csc429/question_bank_draft.json",
        "model": "deterministic",
        "cost_usd": 0.0,
        "papers": len(papers),
        "entries": len(entries),
        "topics": len([key for key in TOPICS if key != "other"]),
        "topic_entries": dict(topic_counter),
        "confidence": dict(confidence_counter),
        "marks_total": sum(entry["marks"] or 0 for entry in entries),
        "expected_marks_total": len(papers) * PAPER_TOTAL,
        "papers_reconciled": sum(1 for row in paper_rows
                                 if row["marks_complete"]),
        "papers_with_issues": [row["paper_id"] for row in paper_rows
                               if not row["marks_complete"]],
        "unsure_count": len(unsure),
        "part_structure": part_structure,
        "topic_stats": {
            key: {
                "title": value["title"],
                "observed_entries": value["observed_entries"],
                "observed_marks": value["observed_marks"],
                "papers": len(value["papers"]),
            }
            for key, value in topic_payload.items()
        },
    }

    taxonomy = {
        "subject": SUBJECT,
        "version": 1,
        "generated_by": "src.subjects.csc429.taxonomy",
        "source": summary["source"],
        "topics": topic_payload,
        "part_structure": part_structure,
        "paper_count": len(papers),
        "question_count": len(entries),
        "total_marks": summary["marks_total"],
        "unsure": unsure,
    }
    question_log = {
        "schema_version": 1,
        "subject": SUBJECT,
        "version": 1,
        "generated_by": "src.subjects.csc429.taxonomy",
        "source": summary["source"],
        "model": "deterministic",
        "cost_usd": 0.0,
        "summary": summary,
        "papers": paper_rows,
        "entries": entries,
    }

    TAXONOMY_PATH.write_text(
        json.dumps(taxonomy, indent=2, ensure_ascii=False), encoding="utf-8")
    LOG_PATH.write_text(
        json.dumps(question_log, indent=2, ensure_ascii=False),
        encoding="utf-8")
    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    _update_subject_fingerprint(summary, part_structure, topic_payload)
    return summary


def _update_subject_fingerprint(summary: dict, part_structure: dict,
                                topic_payload: dict) -> None:
    if not SUBJECT_PATH.exists():
        return
    subject = json.loads(SUBJECT_PATH.read_text(encoding="utf-8"))
    previous = subject.get("fingerprint") or {}
    bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))
    paper_ids = sorted(bank.get("papers", []), key=lambda row: row["paper_id"])
    years = []
    for row in paper_ids:
        match = re.search(r"-(\d{4})-", row["paper_id"])
        if match:
            years.append(int(match.group(1)))
    subject["fingerprint"] = {
        "source_papers": "data/papers/CSC429",
        "paper_count": 23,
        "unique_papers": summary["papers"],
        "year_min": min(years) if years else None,
        "year_max": max(years) if years else None,
        "prepared_corpus": "data/tracking/csc429",
        "taxonomy": "data/tracking/csc429/taxonomy.json",
        "question_log": "data/tracking/csc429/question_log.json",
        "taxonomy_summary": "data/tracking/csc429/taxonomy_summary.json",
        "question_log_entries": summary["entries"],
        "papers_with_reconciled_marks": summary["papers_reconciled"],
        "part_marks": {
            part: value["marks_values"]
            for part, value in part_structure.items()
        },
        "topic_count": summary["topics"],
        "topic_marks": {
            key: value["observed_marks"]
            for key, value in topic_payload.items() if key != "other"
        },
        "planner_format": {
            "A": {"questions": 10, "marks": 80},
            "B": {"questions": 1, "marks": 20},
        },
        "generation_model": "deterministic_real_question_bank",
    }
    # Planner/generator/builder stages add their own evidence keys after the
    # taxonomy.  Preserve them when this stage is re-run.
    for key in (
        "planner", "planner_sample", "planner_slots", "planner_topic_quota",
        "generators", "generator_sample", "generator_validation",
        "generator_count", "generator_slots_20_seeds", "builder",
        "build_sample", "sample_pages", "marking_scheme",
    ):
        if key in previous:
            subject["fingerprint"][key] = previous[key]
    SUBJECT_PATH.write_text(json.dumps(subject, indent=2) + "\n",
                            encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    summary = build()
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if args.json:
        return


if __name__ == "__main__":
    main()
