"""CSC413 stage-4 taxonomy and question log.

Deterministic parser for the 15 unique CSC413 papers.  The paper format
changes over time:

- 2014-2019: PART A objective questions and PART B structured questions;
- 2021: PART A/B/C objective and PART D structured, total 50 marks;
- 2022-2023: PART A/B/C objective and PART D structured, total 100 marks.

The parser splits each paper into body PARTS, extracts QUESTION or numbered
items, associates ``(N marks)`` with the nearest question/subpart and
classifies each entry against a paper-derived interactive-multimedia
taxonomy.  When the text layer cannot reconstruct individual objective
questions, that part is logged as one aggregate entry and recorded in
``unsure``.

    uv run python -m src.subjects.csc413.taxonomy
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from src import config

SUBJECT = "CSC413"
TRACKING = config.TRACKING_DIR / "csc413"
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
    "multimedia_fundamentals": {
        "title": "Multimedia fundamentals and interactivity",
        "keywords": [
            "multimedia", "linear", "nonlinear", "non-linear", "hypermedia",
            "interactivity", "interactive", "presentation", "application",
            "convergence", "digital", "analog", "analogue", "bandwidth",
            "compression", "file size", "platform", "medium", "media",
            "multimedia project", "multimedia element",
        ],
    },
    "text": {
        "title": "Text and typography",
        "keywords": [
            "text", "font", "typeface", "serif", "sans serif", "kerning",
            "tracking", "leading", "anti-alias", "antialias", "alias",
            "hypertext", "hyperlink", "typography", "ascii", "ocr",
            "character", "glyph", "typesetting", "text file",
        ],
    },
    "graphics": {
        "title": "Graphics, images and colour",
        "keywords": [
            "graphic", "image", "bitmap", "vector", "pixel", "resolution",
            "color", "colour", "rgb", "cmyk", "hue", "palette", "dpi",
            "2d", "3d", "rendering", "render", "clip art", "photograph",
            "scanner", "drawing", "illustration", "model", "texture",
            "shading", "grayscale", "greyscale", "monochrome", "saturation",
        ],
    },
    "audio": {
        "title": "Audio and sound",
        "keywords": [
            "audio", "sound", "frequency", "hertz", "hz", "sample",
            "sampling", "midi", "wav", "mp3", "waveform", "amplitude",
            "decibel", "db", "microphone", "speaker", "sound card",
            "digital audio", "analog audio", "mono", "stereo", "sound pressure",
        ],
    },
    "video": {
        "title": "Video and digital video",
        "keywords": [
            "video", "frame", "fps", "codec", "mpeg", "avi", "streaming",
            "chroma key", "blue screen", "camera", "shooting", "interlacing",
            "editing", "footage", "movie", "film", "camcorder", "video clip",
            "video format",
        ],
    },
    "animation": {
        "title": "Animation",
        "keywords": [
            "animation", "animate", "keyframe", "tween", "morphing", "cel",
            "path animation", "sprite", "frame rate", "motion", "flipbook",
            "2d animation", "3d animation", "stop motion", "claymation",
        ],
    },
    "authoring_interactivity": {
        "title": "Authoring tools and interactive design",
        "keywords": [
            "authoring", "authoring tool", "authoring software", "storyboard",
            "prototype", "gui", "navigation", "button", "hotspot",
            "hot spot", "scripting", "programming", "html5", "web browser",
            "card", "page-based", "timeline", "icon", "menu", "interactive",
            "interactivity", "user control",
        ],
    },
    "hardware_devices": {
        "title": "Hardware and multimedia devices",
        "keywords": [
            "hardware", "device", "input", "output", "scanner", "printer",
            "monitor", "cpu", "ram", "storage", "hard drive", "hard disk",
            "usb", "plug and play", "infrared", "scsi", "ethernet", "lan",
            "touchscreen", "touch screen", "camera", "webcam", "barcode",
            "bar code", "digitizer", "graphics tablet", "joystick",
            "sound card", "video card",
        ],
    },
    "web_hypermedia": {
        "title": "Web and hypermedia",
        "keywords": [
            "web", "internet", "html", "hypertext", "hyperlink", "browser",
            "website", "web site", "online", "url", "http", "www",
            "search engine", "social media", "web page", "webpage",
        ],
    },
    "design_project": {
        "title": "Design, planning and project management",
        "keywords": [
            "design", "interface", "usability", "user experience", "ux",
            "layout", "color scheme", "colour scheme", "project management",
            "team", "client", "prototype", "storyboard", "planning", "cost",
            "timeline", "evaluation", "requirement", "target audience",
            "mockup", "wireframe", "low-fidelity", "high-fidelity",
            "project manager", "schedule",
        ],
    },
    "legal_ethics": {
        "title": "Legal, ethical and ownership issues",
        "keywords": [
            "copyright", "ownership", "legal", "ethical", "ethics",
            "privacy", "license", "licence", "trademark", "plagiarism",
            "intellectual property", "royalty", "permission", "patent",
        ],
    },
    "virtual_reality": {
        "title": "Virtual and augmented reality",
        "keywords": [
            "virtual reality", "vr", "augmented reality", "ar", "immersion",
            "immersive", "headset", "simulation", "3d environment",
            "haptic", "cave", "virtual environment",
        ],
    },
    "other": {"title": "Other / unclassified", "keywords": []},
}

PART_RE = re.compile(r"PART\s*([A-D])\s*(?:\(([^)]*)\))?", re.I)
PART_COUNT_RE = re.compile(
    r"PART\s*([A-D])\s*\(\s*(\d+)\s*Questions?\s*\)", re.I)
QUESTION_RE = re.compile(r"\bQUESTION\s+(\d+)\b", re.I)
NUMBERED_RE = re.compile(r"(?m)^\s*(\d{1,2})\.\s+")
SUBPART_RE = re.compile(r"(?<![A-Za-z0-9])([a-h])[\.\)]\s+")
MARKS_RE = re.compile(r"\(\s*['‘’]?\s*(\d+)\s*marks?\s*\)", re.I)


def normalise(text: str) -> str:
    text = text.replace("\r", "\n").replace("\f", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text


def clean_text(text: str) -> str:
    text = re.sub(r"CONFIDENTIAL", " ", text, flags=re.I)
    text = re.sub(r"CS\s*/\s*[A-Z]{3,9}\s+\d{4}\s*/\s*CSC413", " ", text,
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


def _body_parts(text: str) -> list[re.Match]:
    """Return the body header for each part (the last occurrence)."""
    latest: dict[str, re.Match] = {}
    for match in PART_RE.finditer(text):
        latest[match.group(1).upper()] = match
    return sorted(latest.values(), key=lambda match: match.start())


def _part_counts(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for match in PART_COUNT_RE.finditer(text):
        counts.setdefault(match.group(1).upper(), int(match.group(2)))
    return counts


def _header_marks(match: re.Match) -> int | None:
    inside = match.group(2) or ""
    found = re.search(r"(\d+)\s*MARKS?", inside, re.I)
    return int(found.group(1)) if found else None


def _split_questions(block: str, declared: int | None) -> tuple[list[tuple[int, int, str]], str]:
    """Return (start, end, label) blocks and the marker kind used."""
    candidates: list[tuple[str, list[re.Match]]] = []
    qmatches = list(QUESTION_RE.finditer(block))
    if len(qmatches) >= 2:
        candidates.append(("question", qmatches))
    nmatches = list(NUMBERED_RE.finditer(block))
    if len(nmatches) >= 2:
        candidates.append(("numbered", nmatches))
    if not candidates:
        return [], ""
    if declared:
        candidates.sort(key=lambda item: (abs(len(item[1]) - declared),
                                          item[0] != "question"))
    else:
        candidates.sort(key=lambda item: item[0] != "question")
    kind, matches = candidates[0]
    rows = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(block)
        rows.append((start, end, match.group(1)))
    return rows, kind


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


def parse_paper(row: dict) -> dict:
    source_name = str(row.get("paper") or row.get("source") or "")
    paper = Path(source_name).stem
    paper_id = _paper_id(row)
    text_path = Path(str(row.get("text_file") or ""))
    if not text_path.is_file():
        text_path = TEXT_DIR / f"{paper}.txt"
    source_text = (text_path.read_text(encoding="utf-8", errors="ignore")
                   if text_path.exists() else "")
    text = normalise(source_text)
    part_matches = _body_parts(text)
    counts = _part_counts(text)
    part_marks: dict[str, int] = {}
    for match in part_matches:
        value = _header_marks(match)
        if value is not None:
            part_marks[match.group(1).upper()] = value

    entries: list[dict] = []
    issues: list[str] = []
    aggregates: list[str] = []
    source_file = str(text_path)
    source_kind = row.get("source_kind", "")

    for index, match in enumerate(part_matches):
        part = match.group(1).upper()
        start = match.end()
        end = (part_matches[index + 1].start()
               if index + 1 < len(part_matches) else len(text))
        block_raw = normalise(text[start:end])
        block = clean_text(block_raw)
        if not block:
            continue
        declared = counts.get(part)
        question_rows, kind = _split_questions(block_raw, declared)
        # Objective parts normally have one mark per question; Part D uses
        # explicit marks.  A part with no usable split, or a split that does
        # not match the declared question count, is an aggregate.
        count_mismatch = bool(
            declared and question_rows and len(question_rows) != declared)
        if count_mismatch:
            issues.append(
                f"{paper}: PART {part} parsed {len(question_rows)} of "
                f"{declared} declared questions; logged as aggregate")
        if len(question_rows) < 2 or count_mismatch:
            topic, scores, _ = classify(block)
            marks = part_marks.get(part)
            if marks is None:
                marks = sum(_marks(block)) or None
            entries.append(_entry(
                paper, paper_id, part, part, "", part, block, marks,
                topic, scores, "low", "part", source_file, source_kind))
            aggregates.append(part)
        else:
            per_question = None
            if declared and part in part_marks:
                if part_marks[part] % declared == 0:
                    per_question = part_marks[part] // declared
            for q_index, (q_start, q_end, q_number) in enumerate(question_rows):
                q_block_raw = block_raw[q_start:q_end].strip()
                q_block = clean_text(q_block_raw)
                label = f"{part}{q_index + 1}"
                explicit = _marks(q_block_raw)
                subparts = _split_subparts(q_block_raw)
                if subparts:
                    subpart_rows = []
                    subpart_values = []
                    for subpart, sub_text in subparts:
                        sub_marks = sum(_marks(sub_text)) or None
                        subpart_values.append(sub_marks)
                        subpart_rows.append({
                            "label": subpart,
                            "text": clean_text(sub_text)[:1200],
                            "marks": sub_marks,
                        })
                    if subpart_values and all(
                            isinstance(value, int) and value > 0
                            for value in subpart_values):
                        marks = sum(subpart_values)
                    else:
                        marks = sum(explicit) if explicit else None
                    topic, scores, confidence = classify(q_block)
                    entry = _entry(
                        paper, paper_id, part, label, "", label, q_block,
                        marks, topic, scores,
                        confidence if marks is not None else "low",
                        "question", source_file, source_kind)
                    entry["subparts"] = subpart_rows
                    entries.append(entry)
                else:
                    marks = sum(explicit) if explicit else per_question
                    topic, scores, confidence = classify(q_block)
                    entries.append(_entry(
                        paper, paper_id, part, label, "", label, q_block,
                        marks, topic, scores,
                        confidence if marks is not None else "low",
                        "question", source_file, source_kind))
                if entries[-1]["marks"] is None:
                    issues.append(
                        f"{paper}: {label} has no parseable marks")
            if kind == "numbered" and declared and len(question_rows) < declared:
                issues.append(
                    f"{paper}: PART {part} parsed {len(question_rows)} of "
                    f"{declared} declared questions")

    # If a part's header has no marks but its parsed entries do, use the sum.
    parsed_by_part: dict[str, int] = {}
    for entry in entries:
        if isinstance(entry.get("marks"), int):
            parsed_by_part[entry["part"]] = (
                parsed_by_part.get(entry["part"], 0) + entry["marks"])
    for part, total in parsed_by_part.items():
        part_marks.setdefault(part, total)

    expected = sum(part_marks.values()) if part_marks else None
    parsed = sum(entry["marks"] for entry in entries
                 if isinstance(entry.get("marks"), int))
    complete = expected is not None and parsed == expected
    if expected is None:
        issues.append(f"{paper}: no part marks headers found")
    elif not complete:
        issues.append(
            f"{paper}: parsed marks {parsed} do not reconcile with part "
            f"headers {expected}")
    if aggregates:
        issues.append(
            f"{paper}: PART {', '.join(aggregates)} logged as aggregate "
            "entries because individual items were not reliably split")
    return {
        "paper": paper,
        "paper_id": paper_id,
        "file": source_file,
        "source_kind": source_kind,
        "part_marks": part_marks,
        "expected_marks": expected,
        "parsed_marks": parsed,
        "marks_complete": complete,
        "entry_count": len(entries),
        "aggregate_parts": aggregates,
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
    for part in ("A", "B", "C", "D"):
        part_papers = [paper for paper in papers
                       if part in paper["part_marks"]]
        part_stats[part] = {
            "papers": len(part_papers),
            "marks_values": sorted({
                paper["part_marks"][part] for paper in part_papers}),
        }
    unsure = [issue for paper in papers for issue in paper["issues"]]
    aggregate_papers = [paper["paper_id"] for paper in papers
                        if paper["aggregate_parts"]]
    if aggregate_papers:
        unsure.insert(
            0,
            f"{len(aggregate_papers)} papers have at least one PART logged as "
            "one aggregate entry; individual objective items could not be "
            "reliably reconstructed from the OCR/text layer.")
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
        "generated_by": "src.subjects.csc413.taxonomy",
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
        "aggregate_papers": aggregate_papers,
        "questions_without_marks": questions_without_marks,
        "topic_stats": topic_stats,
        "part_stats": part_stats,
        "unsure": unsure,
    }
    taxonomy = {
        "subject": SUBJECT,
        "version": 1,
        "generated_by": "src.subjects.csc413.taxonomy",
        "topics": topic_stats,
        "part_structure": part_stats,
        "total_marks": summary["expected_marks_total"],
        "paper_count": len(papers),
        "unsure": unsure,
    }
    log = {
        "subject": SUBJECT,
        "version": 1,
        "generated_by": "src.subjects.csc413.taxonomy",
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
