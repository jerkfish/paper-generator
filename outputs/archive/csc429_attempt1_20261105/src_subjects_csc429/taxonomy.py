"""CSC429 stage-4 taxonomy and question log.

Deterministic parser for the 20 unique CSC429 papers.  The paper format is
stable: PART A contains ten questions (80 or 85 marks in total) and PART B
contains one longer question (20 or 15 marks), for 100 marks overall.  OCR
noise varies by paper, so the parser records aggregate parts, missing marks
and unreconciled totals rather than inventing values.

    uv run python -m src.subjects.csc429.taxonomy
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

import pymupdf
from PIL import Image

from src import config

SUBJECT = "CSC429"
TRACKING = config.TRACKING_DIR / "csc429"
REGISTER = TRACKING / "papers_register.json"
TEXT_DIR = TRACKING / "paper_text"
ASSETS_DIR = TRACKING / "assets"
TAXONOMY_PATH = TRACKING / "taxonomy.json"
LOG_PATH = TRACKING / "question_log.json"
SUMMARY_PATH = TRACKING / "taxonomy_summary.json"

MONTH_NUMBER = {
    "JANUARY": 1, "FEBRUARY": 2, "MARCH": 3, "APRIL": 4, "MAY": 5,
    "JUNE": 6, "JULY": 7, "AUGUST": 8, "SEPTEMBER": 9, "OCTOBER": 10,
    "NOVEMBER": 11, "DECEMBER": 12,
}

TOPICS = {
    "computer_generations_history": {
        "title": "Computer generations and history",
        "keywords": [
            "generation", "generations", "first generation", "second generation",
            "third generation", "fourth generation", "fifth generation",
            "vacuum tube", "vacuum tubes", "transistor", "transistors",
            "integrated circuit", "integrated circuits", "vlsi", "ssi", "msi",
            "lsi", "eniac", "edsac", "ias machine", "calculating machine",
            "calculating machines", "pascal", "leibniz", "babbage",
            "artificial intelligence", "ai", "computer evolution",
            "computer history", "von neumann",
        ],
    },
    "data_representation": {
        "title": "Data representation and number systems",
        "keywords": [
            "binary", "decimal", "octal", "hexadecimal", "hex",
            "number system", "number systems", "base", "conversion", "convert",
            "complement", "1's complement", "2's complement",
            "ones complement", "twos complement", "sign and magnitude",
            "signed", "unsigned", "floating point", "floating-point",
            "ieee", "single precision", "double precision", "bcd", "ascii",
            "character", "characters", "byte", "word", "bit", "bits",
            "overflow", "mantissa", "exponent", "normalize", "normalization",
        ],
    },
    "cpu_organization": {
        "title": "CPU organization and the machine cycle",
        "keywords": [
            "cpu", "central processing unit", "alu",
            "arithmetic logic unit", "control unit", "cu", "register",
            "registers", "program counter", "pc", "instruction register",
            "ir", "accumulator", "ac", "machine cycle", "fetch", "decode",
            "execute", "instruction cycle", "von neumann architecture",
            "von neumann", "computer structure", "computer architecture",
            "datapath", "clock", "clock cycle", "processor", "core",
            "computer components", "system unit", "motherboard",
        ],
    },
    "memory_cache": {
        "title": "Memory hierarchy and cache",
        "keywords": [
            "cache", "cache memory", "main memory", "memory", "ram", "rom",
            "sram", "dram", "memory hierarchy", "tag", "tags", "line number",
            "block address", "mapping function", "direct mapping",
            "direct mapped", "associative", "set associative",
            "fully associative", "hit", "miss", "hit rate", "locality",
            "spatial locality", "temporal locality", "memory address",
            "addressable", "word addressable", "byte addressable",
            "memory cell", "memory chip", "volatile", "non-volatile",
        ],
    },
    "interrupts_io": {
        "title": "Interrupts, I/O and DMA",
        "keywords": [
            "interrupt", "interrupts", "interrupt-driven",
            "interrupt driven", "nested interrupt", "priority", "priorities",
            "dma", "direct memory access", "programmed i/o",
            "programmed input output", "polling", "i/o", "input output",
            "input/output", "device", "devices", "usb", "hot connection",
            "buffer", "buffering", "interface", "peripheral", "peripherals",
            "maskable", "non-maskable", "isr", "interrupt handler",
        ],
    },
    "buses_interconnection": {
        "title": "Buses and system interconnection",
        "keywords": [
            "bus", "buses", "system interconnection", "cpu interconnection",
            "interconnection", "address bus", "data bus", "control bus",
            "bus width", "bus arbitration", "point-to-point", "crossbar",
        ],
    },
    "instruction_set_assembly": {
        "title": "Instruction sets and assembly programming",
        "keywords": [
            "instruction", "instructions", "instruction set",
            "addressing mode", "addressing modes", "assembly",
            "assembly language", "machine language", "opcode", "operand",
            "operands", "zero-address", "one-address", "three-address",
            "two-address", "load", "store", "push", "pop", "add", "sub",
            "mul", "div", "program", "programs", "register transfer",
            "r-type", "i-type", "j-type", "mips",
        ],
    },
    "parallel_architectures": {
        "title": "Parallel architectures",
        "keywords": [
            "mimd", "simd", "sisd", "misd", "flynn", "parallel",
            "parallelism", "multicore", "multi-core", "multiprocessor",
            "multiprocessing", "shared memory", "distributed memory",
            "cluster", "pipeline", "pipelining", "superscalar", "speedup",
            "amdahl", "thread", "threads",
        ],
    },
    "storage_devices": {
        "title": "Storage and I/O devices",
        "keywords": [
            "magnetic", "optical", "ssd", "solid state", "solid-state",
            "raid", "hard disk", "hard drive", "disk", "disks", "tape",
            "cd", "dvd", "blu-ray", "flash", "secondary storage", "storage",
            "tertiary storage", "access time", "seek time", "latency",
        ],
    },
    "other": {"title": "Other / unclassified", "keywords": []},
}

PART_RE = re.compile(r"\bPART\s*([AB])\b")
PART_COUNT_RE = re.compile(
    r"PART\s*([AB])\s*\(\s*(\d+)\s*Questions?\s*\)", re.I)
PART_MARKS_RE = re.compile(r"\(\s*(\d+)\s*MARKS?\s*\)", re.I)
QUESTION_RE = re.compile(
    r"\b(?:QUESTION|QUEST[\]\[]?ON|OUESTION|QUEST[I1]ON)\s+"
    r"(\d{1,2}|I)\b")
LETTER_SUB_RE = re.compile(r"(?m)^\s*([a-h])[\.\)]\s*")
ROMAN_SUB_RE = re.compile(r"(?m)^\s*(i{1,3}|iv|v|vi)[\.\)]\s*")
MARKS_RE = re.compile(
    r"\(?\s*['‘’]?\s*(\d{1,3}|l)\s*marks?\s*\)?", re.I)
FIGURE_RE = re.compile(
    r"\b(?:Figure|Table|Diagram|Image|Chart|Graph)\s*(\d+)?", re.I)


def _figure_refs(text: str) -> list[str]:
    refs = []
    for match in FIGURE_RE.finditer(text or ""):
        label = match.group(0).strip()
        label = re.sub(r"\s+", " ", label)
        if label.lower() not in {ref.lower() for ref in refs}:
            refs.append(label)
    return refs


def normalise(text: str) -> str:
    text = text.replace("\r", "\n").replace("\f", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text


def clean_text(text: str) -> str:
    # Remove the page furniture as tokens, not as whole lines: OCR sometimes
    # joins a page header and a question into one long line.
    text = re.sub(r"(?i)\bCONFIDENTIAL\b", " ", text)
    text = re.sub(
        r"(?i)\b(?:CS|CD)\s*/?\s*I?"
        r"(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)"
        r"[A-Z]*\s+\d{4}\s*/\s*CSC429\b", " ", text)
    text = re.sub(
        r"(?i)\bCSC429\s*/\s*(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|"
        r"NOV|DEC)[A-Z]*\s+\d{4}\b", " ", text)
    text = re.sub(
        r"(?i)(?:@|O)?\s*Hak\s+C[il]p[a-z]*\s+Universiti\s+Teknologi\s+"
        r"MARA", " ", text)
    text = re.sub(
        r"(?i)DO NOT TURN THIS PAGE UNTIL YOU ARE TOLD TO DO SO", " ", text)
    text = re.sub(
        r"(?i)This examination paper consists of[^.\n]*\.?", " ", text)
    text = re.sub(r"(?i)END OF QUESTION PAPER", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()


def classify(text: str) -> tuple[str, list[str], dict[str, int], str]:
    lowered = f" {text.lower()} "
    scores: dict[str, int] = {}
    for topic, spec in TOPICS.items():
        score = 0
        for keyword in spec["keywords"]:
            pattern = r"\b" + re.escape(keyword).replace(r"\ ", r"\s+") + r"\b"
            matches = len(re.findall(pattern, lowered, flags=re.I))
            if matches:
                score += matches * (2 if (" " in keyword or "-" in keyword
                                        or "'" in keyword) else 1)
        scores[topic] = score
    # OCR often destroys the prose around a numeric conversion; recognise the
    # binary/hex tokens directly instead of leaving the entry unclassified.
    if (re.search(r"\b[01]{4,}\b", text)
            or re.search(r"\b[0-9A-F]{1,4}H\b", text, re.I)
            or re.search(r"\b(?:0x[0-9A-F]+|base\s*\d+)\b", text, re.I)):
        scores["data_representation"] += 2
    if re.search(r"\breplacement\s+(?:algorithm|policy)\b", text, re.I):
        scores["memory_cache"] += 3
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    best, top = ranked[0]
    if top == 0:
        return "other", [], scores, "low"
    secondary = [topic for topic, score in ranked[1:]
                 if score > 0 and topic != "other"][:2]
    confidence = "high" if top >= 4 else "medium"
    return best, secondary, scores, confidence


def _marks(text: str) -> list[int]:
    values = []
    for raw in MARKS_RE.findall(text or ""):
        values.append(1 if raw.lower() == "l" else int(raw))
    return values


def _paper_id(row: dict) -> str:
    year = int(row.get("year") or 0)
    month = MONTH_NUMBER.get(str(row.get("month") or "").upper(), 0)
    return f"{SUBJECT}-{year:04d}-{month:02d}"


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


def _part_header_marks(text: str, match: re.Match) -> int | None:
    window = text[match.start():match.start() + 80]
    found = PART_MARKS_RE.search(window)
    return int(found.group(1)) if found else None


def _split_questions(block: str) -> tuple[list[dict], list[str]]:
    """Split a part block by uppercase QUESTION headings.

    Duplicate OCR headings for the same question number are merged; the
    longest block wins.  Title-case references such as "Question 1 is based
    on Figure 1" are not headings because the regex is case-sensitive.
    """
    matches = list(QUESTION_RE.finditer(block))
    issues: list[str] = []
    by_number: dict[str, dict] = {}
    order: list[str] = []
    for index, match in enumerate(matches):
        raw = match.group(1)
        number = "1" if raw.upper() == "I" else str(int(raw))
        start = match.end()
        end = (matches[index + 1].start()
               if index + 1 < len(matches) else len(block))
        text = block[start:end].strip()
        if number in by_number:
            issues.append(
                f"duplicate QUESTION {number} heading; kept the longest block")
            if len(text) > len(by_number[number]["text"]):
                by_number[number]["text"] = text
            continue
        by_number[number] = {"number": number, "text": text}
        order.append(number)
    return [by_number[number] for number in order], issues


def _split_subparts(block: str) -> list[dict]:
    matches = list(LETTER_SUB_RE.finditer(block))
    matches += list(ROMAN_SUB_RE.finditer(block))
    matches.sort(key=lambda match: match.start())
    # Remove overlapping matches; a roman label inside a letter block is kept
    # only when it starts a new line and follows the letter label.
    filtered = []
    last_start = -1
    for match in matches:
        if match.start() <= last_start:
            continue
        filtered.append(match)
        last_start = match.start()
    if not filtered:
        return []
    rows = []
    for index, match in enumerate(filtered):
        start = match.end()
        end = (filtered[index + 1].start()
               if index + 1 < len(filtered) else len(block))
        label = match.group(1).lower()
        rows.append({
            "label": label,
            "text": clean_text(block[start:end])[:1200],
        })
    return rows


def _question_marks(question_text: str, subparts: list[dict],
                    part: str, part_total: int | None,
                    declared: int | None, question_count: int) -> tuple[
                        int | None, str, list[str]]:
    flags: list[str] = []
    subpart_values = []
    reliable_subparts = len(subparts) >= 2
    for subpart in subparts:
        values = _marks(subpart["text"])
        if len(values) == 1:
            subpart["marks"] = values[0]
            subpart_values.append(values[0])
        else:
            subpart["marks"] = None
            subpart_values.append(None)
            if len(values) > 1:
                reliable_subparts = False
                flags.append(f"subpart_{subpart['label']}_multiple_marks")
    explicit = _marks(question_text)
    if reliable_subparts and all(value is not None
                                  for value in subpart_values):
        total = sum(value for value in subpart_values if value is not None)
        if explicit and total not in explicit:
            flags.append(f"marks_conflict:subparts={total},explicit={explicit}")
        return total, "subparts", flags
    if explicit:
        if len(explicit) > 1:
            flags.append("explicit_marks_sum")
        return sum(explicit), "explicit_sum", flags
    if part == "B" and part_total is not None and question_count == 1:
        return part_total, "part_total", flags
    if (part == "A" and part_total is not None and declared
            and question_count == declared and part_total % declared == 0):
        return part_total // declared, "part_total_inferred", flags
    flags.append("marks_missing")
    return None, "missing", flags


def _entry(paper: str, paper_id: str, part: str, question: str, index: int,
           text: str, marks: int | None, marks_source: str,
           topic: str, secondary: list[str], scores: dict[str, int],
           confidence: str, granularity: str, subparts: list[dict],
           source_file: str, source_kind: str,
           review_flags: list[str]) -> dict:
    return {
        "paper": paper,
        "paper_id": paper_id,
        "part": part,
        "question": question,
        "subpart": "",
        "slot": f"{part}{index}",
        "text": text[:1800],
        "marks": marks,
        "marks_source": marks_source,
        "granularity": granularity,
        "topic": topic,
        "secondary_topics": secondary,
        "topic_scores": scores,
        "confidence": confidence,
        "subparts": subparts,
        "figure_refs": _figure_refs(text),
        "source_file": source_file,
        "source_kind": source_kind,
        "review_flags": review_flags,
    }


def _capture_assets(row: dict, paper: str,
                    figure_refs: list[str]) -> list[dict]:
    """Capture source pages at 200 dpi for figure/table/image questions.

    Scanned papers often embed the figure in the full-page scan, so the whole
    page is the safe capture.  The asset paths are recorded in the question
    log; the original PDFs are never modified.
    """
    if not figure_refs:
        return []
    pdf_path = config.subject_papers_dir(SUBJECT) / str(row.get("source", ""))
    if not pdf_path.is_file():
        return []
    out_dir = ASSETS_DIR / paper
    out_dir.mkdir(parents=True, exist_ok=True)
    assets = []
    with pymupdf.open(str(pdf_path)) as document:
        for page in document:
            number = page.number + 1
            path = out_dir / f"page_{number:03d}.jpg"
            if not path.is_file():
                pix = page.get_pixmap(dpi=200, colorspace=pymupdf.csRGB,
                                      alpha=False)
                image = Image.frombytes(
                    "RGB", (pix.width, pix.height), pix.samples)
                image.save(path, "JPEG", quality=90, optimize=True,
                           dpi=(200, 200))
            assets.append({
                "page": number,
                "path": str(path.relative_to(TRACKING)).replace("\\", "/"),
            })
    manifest = {
        "paper": row.get("source"),
        "dpi": 200,
        "format": "JPEG quality 90",
        "pages": assets,
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    return assets


def parse_paper(row: dict) -> dict:
    source_name = str(row.get("source") or "")
    paper = Path(source_name).stem
    paper_id = _paper_id(row)
    text_path = Path(str(row.get("text_file") or (TEXT_DIR / f"{paper}.txt")))
    raw = (text_path.read_text(encoding="utf-8", errors="ignore")
           if text_path.exists() else "")
    text = normalise(raw)
    part_matches = _body_parts(text)
    counts = _part_counts(text)
    declared = {"A": counts.get("A", 10), "B": counts.get("B", 1)}
    part_marks: dict[str, int] = {}
    for match in part_matches:
        value = _part_header_marks(text, match)
        if value is not None:
            part_marks[match.group(1).upper()] = value

    entries: list[dict] = []
    issues: list[str] = []
    aggregates: list[str] = []
    source_kind = str(row.get("source_kind") or "")

    for index, match in enumerate(part_matches):
        part = match.group(1).upper()
        start = match.end()
        end = (part_matches[index + 1].start()
               if index + 1 < len(part_matches) else len(text))
        block_raw = normalise(text[start:end])
        # Drop the rest of the part-header line before parsing questions.
        block_raw = re.sub(r"^\s*\([^)]*MARKS?[^)]*\)\s*", "", block_raw,
                           count=1, flags=re.I)
        block = clean_text(block_raw)
        if not block:
            issues.append(f"{paper}: PART {part} is empty after cleaning")
            continue
        question_rows, duplicate_issues = _split_questions(block_raw)
        issues.extend(f"{paper}: {issue}" for issue in duplicate_issues)
        if not question_rows:
            topic, secondary, scores, confidence = classify(block)
            marks = part_marks.get(part)
            if marks is None:
                marks = sum(_marks(block)) or None
            entries.append(_entry(
                paper, paper_id, part, part, 1, block, marks, "part_total",
                topic, secondary, scores, "low", "part_aggregate", [],
                str(text_path), source_kind, ["part_aggregate"]))
            aggregates.append(part)
            issues.append(
                f"{paper}: PART {part} has no QUESTION headings; logged as "
                "one aggregate entry")
            continue
        if len(question_rows) != declared.get(part):
            issues.append(
                f"{paper}: PART {part} parsed {len(question_rows)} of "
                f"{declared.get(part)} declared questions")
        for q_index, question in enumerate(question_rows, start=1):
            q_text = clean_text(question["text"])
            subparts = _split_subparts(question["text"])
            marks, marks_source, flags = _question_marks(
                q_text, subparts, part, part_marks.get(part),
                declared.get(part), len(question_rows))
            topic, secondary, scores, confidence = classify(q_text)
            entry = _entry(
                paper, paper_id, part, question["number"], q_index, q_text,
                marks, marks_source, topic, secondary, scores,
                confidence if marks is not None else "low", "question",
                subparts, str(text_path), source_kind, flags)
            entries.append(entry)
            if marks is None:
                issues.append(
                    f"{paper}: PART {part} QUESTION {question['number']} has "
                    "no parseable marks")

    # Fill missing part totals from the 100-mark convention where safe.
    parsed_by_part: dict[str, int] = {}
    for entry in entries:
        if isinstance(entry.get("marks"), int):
            parsed_by_part[entry["part"]] = (
                parsed_by_part.get(entry["part"], 0) + entry["marks"])
    if "A" not in part_marks and "B" in part_marks:
        if part_marks["B"] in {15, 20}:
            part_marks["A"] = 100 - part_marks["B"]
            issues.append(
                f"{paper}: PART A total inferred from PART B and 100-mark total")
    if "B" not in part_marks and "A" in part_marks:
        if part_marks["A"] in {80, 85}:
            part_marks["B"] = 100 - part_marks["A"]
            issues.append(
                f"{paper}: PART B total inferred from PART A and 100-mark total")
    if "A" not in part_marks and "B" not in part_marks and parsed_by_part:
        candidates = [(80, 20), (85, 15)]
        best = min(
            candidates,
            key=lambda pair: abs(parsed_by_part.get("A", 0) - pair[0])
            + abs(parsed_by_part.get("B", 0) - pair[1]))
        if (abs(parsed_by_part.get("A", 0) - best[0]) <= 10
                and abs(parsed_by_part.get("B", 0) - best[1]) <= 10):
            part_marks["A"], part_marks["B"] = best
            issues.append(
                f"{paper}: part totals inferred from parsed marks as "
                f"{best[0]}+{best[1]}")
    expected = sum(part_marks.values()) if part_marks else 100
    if not part_marks:
        issues.append(f"{paper}: no part marks headers; expected total assumed 100")
    # If the part total and question count are known, a single missing mark
    # can be recovered from the part remainder without inventing a value.
    for part, total in part_marks.items():
        part_entries = [entry for entry in entries if entry["part"] == part]
        missing_entries = [entry for entry in part_entries
                           if entry.get("marks") is None]
        declared_count = declared.get(part)
        if (declared_count and len(part_entries) == declared_count
                and missing_entries):
            known = sum(entry["marks"] for entry in part_entries
                        if isinstance(entry.get("marks"), int))
            remaining = total - known
            if remaining > 0 and remaining % len(missing_entries) == 0:
                value = remaining // len(missing_entries)
                for entry in missing_entries:
                    entry["marks"] = value
                    entry["marks_source"] = "part_remainder_inferred"
                    entry["review_flags"].append(
                        "marks_inferred_from_part_remainder")
                issues.append(
                    f"{paper}: {len(missing_entries)} PART {part} "
                    f"question(s) inferred as {value} marks from the part "
                    "remainder")
    parsed = sum(entry["marks"] for entry in entries
                 if isinstance(entry.get("marks"), int))
    missing = sum(1 for entry in entries if entry.get("marks") is None)
    complete = parsed == expected and missing == 0
    if parsed != expected:
        issues.append(
            f"{paper}: parsed marks {parsed} do not reconcile with expected "
            f"{expected}")
    if aggregates:
        issues.append(
            f"{paper}: PART {', '.join(aggregates)} logged as aggregate "
            "entries")
    figure_refs = sorted(
        {ref for entry in entries for ref in entry["figure_refs"]},
        key=str.lower)
    assets = _capture_assets(row, paper, figure_refs)
    return {
        "paper": paper,
        "paper_id": paper_id,
        "file": str(text_path),
        "source_kind": source_kind,
        "month": row.get("month"),
        "year": row.get("year"),
        "pages": row.get("pages"),
        "declared_counts": declared,
        "part_marks": part_marks,
        "expected_marks": expected,
        "parsed_marks": parsed,
        "missing_marks": missing,
        "marks_complete": complete,
        "entry_count": len(entries),
        "aggregate_parts": aggregates,
        "figure_refs": figure_refs,
        "assets": assets,
        "issues": issues,
        "entries": entries,
    }


def build() -> dict:
    register = json.loads(REGISTER.read_text(encoding="utf-8"))
    rows = [row for row in register
            if not row.get("duplicate_of") and not row.get("error")]
    papers = [parse_paper(row) for row in rows]
    entries = [entry for paper in papers for entry in paper["entries"]]
    topic_stats = {}
    for topic, spec in TOPICS.items():
        topic_entries = [entry for entry in entries if entry["topic"] == topic]
        topic_stats[topic] = {
            "title": spec["title"],
            "keywords": spec["keywords"],
            "observed_marks": sum(entry["marks"] or 0
                                  for entry in topic_entries),
            "observed_entries": len(topic_entries),
            "paper_count": len({entry["paper"] for entry in topic_entries}),
        }
    part_stats = {}
    for part in ("A", "B"):
        part_papers = [paper for paper in papers
                       if part in paper["part_marks"]]
        part_stats[part] = {
            "papers": len(part_papers),
            "marks_values": sorted({
                paper["part_marks"][part] for paper in part_papers}),
            "declared_questions": sorted({
                paper["declared_counts"].get(part)
                for paper in papers if paper["declared_counts"].get(part)}),
        }
    unsure: list[str] = []
    for paper in papers:
        unsure.extend(paper["issues"])
    questions_without_marks = [
        f"{entry['paper_id']} {entry['slot']}" for entry in entries
        if entry["marks"] is None
    ]
    if questions_without_marks:
        unsure.append(
            "Questions without parseable marks: "
            + ", ".join(questions_without_marks))
    aggregate_papers = [paper["paper_id"] for paper in papers
                        if paper["aggregate_parts"]]
    if aggregate_papers:
        unsure.insert(
            0,
            f"{len(aggregate_papers)} papers have a PART logged as one "
            "aggregate entry; individual questions could not be split "
            "reliably from the OCR/text layer.")
    summary = {
        "subject": SUBJECT,
        "generated_by": "src.subjects.csc429.taxonomy",
        "source": str(TEXT_DIR),
        "papers": len(papers),
        "entries": len(entries),
        "expected_marks_total": sum(paper["expected_marks"] for paper in papers),
        "parsed_marks_total": sum(paper["parsed_marks"] for paper in papers),
        "papers_reconciled": sum(1 for paper in papers
                                 if paper["marks_complete"]),
        "papers_with_issues": [paper["paper_id"] for paper in papers
                               if paper["issues"]],
        "aggregate_papers": aggregate_papers,
        "questions_without_marks": questions_without_marks,
        "topic_stats": topic_stats,
        "part_stats": part_stats,
        "assets": {
            "dir": str(ASSETS_DIR),
            "dpi": 200,
            "format": "JPEG quality 90",
            "strategy": "full source page capture; recreate only where a "
                        "diagram can be structured reliably",
            "papers_with_assets": sum(1 for paper in papers
                                      if paper["assets"]),
            "images": sum(len(paper["assets"]) for paper in papers),
        },
        "unsure": unsure,
    }
    taxonomy = {
        "subject": SUBJECT,
        "version": 1,
        "generated_by": "src.subjects.csc429.taxonomy",
        "topics": topic_stats,
        "part_structure": part_stats,
        "total_marks": summary["expected_marks_total"],
        "paper_count": len(papers),
        "unsure": unsure,
    }
    log = {
        "subject": SUBJECT,
        "version": 1,
        "generated_by": "src.subjects.csc429.taxonomy",
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
    _update_subject_fingerprint(summary, taxonomy)
    return summary


def _update_subject_fingerprint(summary: dict, taxonomy: dict) -> None:
    subject_path = config.PROJECT_ROOT / "subjects" / SUBJECT / "subject.json"
    if not subject_path.is_file():
        return
    data = json.loads(subject_path.read_text(encoding="utf-8"))
    topic_order = sorted(
        taxonomy["topics"],
        key=lambda topic: (-taxonomy["topics"][topic]["observed_marks"],
                           topic))
    data["fingerprint"] = {
        "source_papers": "data/papers/CSC429",
        "paper_count": summary["papers"],
        "unique_papers": summary["papers"],
        "prepared_corpus": "data/tracking/csc429",
        "taxonomy": "data/tracking/csc429/taxonomy.json",
        "question_log": "data/tracking/csc429/question_log.json",
        "taxonomy_summary": "data/tracking/csc429/taxonomy_summary.json",
        "question_log_entries": summary["entries"],
        "papers_with_reconciled_marks": summary["papers_reconciled"],
        "total_marks": summary["expected_marks_total"],
        "part_marks": {
            part: spec["marks_values"]
            for part, spec in taxonomy["part_structure"].items()
        },
        "part_questions": {
            part: spec["declared_questions"]
            for part, spec in taxonomy["part_structure"].items()
        },
        "topic_order": topic_order,
        "topic_marks": {
            topic: taxonomy["topics"][topic]["observed_marks"]
            for topic in topic_order
        },
        "figure_assets": {
            "dir": "data/tracking/csc429/assets",
            "dpi": 200,
            "papers_with_assets": summary["assets"]["papers_with_assets"],
            "images": summary["assets"]["images"],
        },
    }
    subject_path.write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf-8")


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
