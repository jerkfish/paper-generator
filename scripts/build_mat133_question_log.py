"""Build the MAT133 paper-derived taxonomy and question log.

The script extracts one structured record per graded question part from every
MAT133 paper.  Text is taken from the cached corpus built by
``scripts.build_mat133_corpus`` (text layer first, Windows OCR fallback).

Run:
    uv run python -m scripts.build_mat133_question_log --workers 4
    uv run python -m scripts.build_mat133_question_log --papers "FEBRUARY 2026"
    uv run python -m scripts.build_mat133_question_log --limit 2 --force

The per-paper LLM responses are cached under
``data/tracking/mat133/question_log/raw`` so reruns are free unless --force is
used.  Deterministic validation and aggregation rerun every time.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pymupdf

from src import config
from src.llm import Usage, chat_json_result
from src.mat133.schema import (
    LLMPaper,
    PaperRecord,
    PatternRecord,
    QuestionEntry,
    QuestionLog,
    ValidationSummary,
)
from src.mat133.taxonomy import (
    SUBTOPIC_IDS,
    TOPIC_IDS,
    priority_of,
    taxonomy_dict,
    topic_label,
)

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "data" / "papers" / "MAT133"
TEXT_DIR = ROOT / "data" / "tracking" / "mat133" / "paper_text"
OUT_DIR = ROOT / "data" / "tracking" / "mat133"
RAW_DIR = OUT_DIR / "question_log" / "raw"
REGISTER = OUT_DIR / "papers_register.json"
SUMMARY = OUT_DIR / "papers_summary.json"

TOPIC_ALIASES = {
    "function": "functions",
    "functions and relations": "functions",
    "inequality": "inequalities",
    "absolute": "absolute_value",
    "absolute value": "absolute_value",
    "absolute values": "absolute_value",
    "complex": "complex_numbers",
    "complex number": "complex_numbers",
    "complex numbers": "complex_numbers",
    "line": "lines",
    "straight line": "lines",
    "straight lines": "lines",
    "circle": "circles",
    "parabola": "parabolas",
    "system of equations": "systems_of_equations",
    "simultaneous equations": "systems_of_equations",
    "systems of equations": "systems_of_equations",
    "system of inequalities": "systems_of_inequalities",
    "systems of inequalities": "systems_of_inequalities",
    "polynomial": "polynomials",
    "exponential and logarithmic": "exponential_logarithmic",
    "exponential and logarithmic equations": "exponential_logarithmic",
    "exponential/logarithmic": "exponential_logarithmic",
    "logarithm": "exponential_logarithmic",
    "logarithms": "exponential_logarithmic",
    "trigonometry": "trigonometry",
    "trigonometric": "trigonometry",
    "circular measure": "circular_measure",
    "triangle": "triangle_geometry",
    "triangles": "triangle_geometry",
    "triangle geometry": "triangle_geometry",
    "geometry": "triangle_geometry",
    "other": "other",
}

DIAGRAMS = {
    "none", "number_line", "cartesian_graph", "circle_graph",
    "parabola_graph", "line_graph", "triangle_figure", "sector_figure",
    "trig_graph", "inequality_region", "mixed_figure",
}

SYSTEM_PROMPT = """You extract graded-question metadata from MAT133
(Pre-Calculus) examination papers.  Return exactly one JSON object with this
shape:
{
  "question_count": 5,
  "total_marks": 100,
  "parts": [
    {
      "question": "1",
      "part": "a",
      "marks": 5,
      "topic": "inequalities",
      "secondary_topics": [],
      "subtopic": "rational",
      "command": "solve",
      "question_pattern": "Solve a rational inequality and express the answer on a number line.",
      "givens": [{"name": "inequality", "value_type": "rational_expression", "example": "(2x-5)/(x+2) <= 1"}],
      "parameter_types": ["linear_numerator", "linear_denominator", "constant_rhs"],
      "formula_forms": ["(ax+b)/(cx+d) <= k"],
      "solution_blueprint": ["Move all terms to one side.", "Find critical values.", "Build a sign table.", "State the solution intervals and shade them on a number line."],
      "diagram": "number_line",
      "evidence": "Solve the inequality ... (5 marks)",
      "confidence": "high",
      "review_flags": []
    }
  ],
  "notes": ""
}

Extraction rules:
1. Include every graded question part, including roman-numeral subparts.
   Exclude the cover page, instructions, appendix formula sheets and figures
   with no question text.  Do not merge two different tasks into one part.
2. ``question`` is the main question number as a string ("1", "2"). ``part`` is
   the local label ("a", "b", "i", "ii") or "b(i)" when the paper nests it.
   Leave ``part`` empty when the whole question is one task.
3. ``question_count`` is the number of main QUESTION headings in the paper
   (normally 4 or 5), NOT the number of extracted parts.  ``total_marks`` is
   the sum of the part marks you extracted, or the printed total when it is
   clearly visible.
4. ``marks`` is the integer from the nearest "(N marks)" marker.  Use null when
   the OCR does not show a mark.  Never guess or invent marks.
5. ``topic`` MUST be one of: {topics}.
6. ``subtopic`` SHOULD be one of the allowed subtopics for that topic:
{subtopics}
   If no listed subtopic fits, use a short snake_case id and add
   "unmapped_subtopic" to review_flags.
7. ``command`` is the dominant instruction: solve, find, determine, express,
   sketch, graph, prove, evaluate, state, write, use, other.
8. ``question_pattern`` is a compact, reusable description of the task (not a
   verbatim copy and not a solution).  Keep it under 300 characters.
9. ``givens`` lists only concrete quantities/expressions visible in the
   question.  Use objects with name, value_type and example.  Do not invent
   values lost by OCR; mark those parts low confidence instead.
10. ``parameter_types`` describes the variable parts a generator would need
    (e.g. linear_coefficients, circle_centre, angle_degrees).
11. ``formula_forms`` lists symbolic templates seen, e.g. "a(x-h)^2+k" or
    "a/sin A = b/sin B".  Use plain text/ASCII, not LaTeX.
12. ``solution_blueprint`` is an ordered list of 2-8 method steps a marking
    scheme would follow.  It must be specific to this pattern but may use
    symbolic coefficients; do not fabricate a numeric final answer.
13. ``diagram`` MUST be one of: {diagrams}.  Use "none" if no diagram is
    required or referenced.
14. ``evidence`` must be a short fragment copied from the supplied text that
    supports the part, at most 300 characters.  Do not paraphrase it.
15. ``confidence`` is high, medium or low.  Use low when OCR corruption makes
    the task or a formula uncertain.  Put specific problems in review_flags.
16. Do not include a question part twice.  Do not output prose outside JSON.
"""


def parse_month_year(name: str) -> tuple[str, int]:
    match = re.match(r"MAT133\s+([A-Z]+)\s+(\d{4})", name, re.I)
    if not match:
        raise ValueError(f"cannot parse month/year from {name}")
    return match.group(1).upper(), int(match.group(2))


def slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-")


def normalize_topic(raw: str) -> tuple[str, str]:
    value = str(raw or "").strip().lower()
    key = re.sub(r"[\s\-/]+", " ", value).strip()
    key = re.sub(r"\s+", " ", key)
    if key in TOPIC_ALIASES:
        return TOPIC_ALIASES[key], ""
    snake = re.sub(r"[^a-z0-9]+", "_", key).strip("_")
    if snake in TOPIC_IDS:
        return snake, ""
    for topic in TOPIC_IDS:
        if topic.replace("_", " ") == key:
            return topic, ""
    return "other", f"unknown_topic:{raw}"


def normalize_subtopic(topic: str, raw: str) -> tuple[str, str]:
    value = str(raw or "").strip().lower()
    snake = re.sub(r"[^a-z0-9]+", "_", value).strip("_")
    allowed = SUBTOPIC_IDS.get(topic, ())
    if snake in allowed:
        return snake, ""
    compact = snake.replace("_", "")
    for candidate in allowed:
        if candidate.replace("_", "") == compact:
            return candidate, ""
    return "other", f"unmapped_subtopic:{raw}"


def normalize_question(raw: str) -> str:
    value = str(raw or "").strip()
    value = re.sub(r"^(QUESTION|Q)\s*", "", value, flags=re.I)
    return value.strip()


def normalize_part(raw: str) -> str:
    value = str(raw or "").strip().lower()
    value = value.replace("(", "").replace(")", "")
    value = value.replace(".", "")
    return value.strip()


def normalize_paper_text(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def evidence_verified(evidence: str, text: str) -> bool:
    ev = normalize_paper_text(evidence)
    hay = normalize_paper_text(text)
    if not ev or not hay:
        return False
    if ev in hay:
        return True
    if len(ev) <= 12:
        return False
    # The extractor may append a nearby "(N marks)" marker or normalise an
    # OCR formula.  Accept the quote when a long contiguous block survives.
    from difflib import SequenceMatcher
    match = SequenceMatcher(None, ev, hay, autojunk=False).find_longest_match(
        0, len(ev), 0, len(hay))
    return match.size >= max(12, int(0.60 * len(ev)))


def load_metadata() -> tuple[dict[str, dict], dict[str, str]]:
    register: dict[str, dict] = {}
    if REGISTER.exists():
        data = json.loads(REGISTER.read_text(encoding="utf-8"))
        for item in data:
            name = item.get("renamed_to") or item.get("source")
            if name:
                register[name] = item
    duplicate_of: dict[str, str] = {}
    if SUMMARY.exists():
        summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
        for group in summary.get("duplicate_groups", {}).values():
            names = sorted(group)
            canonical = next((n for n in names if "(2)" not in n), names[0])
            for name in names:
                if name != canonical:
                    duplicate_of[name] = canonical
    return register, duplicate_of


def load_texts() -> dict[str, str]:
    return {
        path.stem: path.read_text(encoding="utf-8", errors="replace")
        for path in TEXT_DIR.glob("*.txt")
        if path.name != "index.json"
    }


def build_prompt(name: str, text: str) -> str:
    topic_lines = "\n".join(f"- {t}" for t in TOPIC_IDS)
    subtopic_lines = "\n".join(
        f"  {topic}: {', '.join(SUBTOPIC_IDS[topic])}"
        for topic in TOPIC_IDS
    )
    system = (SYSTEM_PROMPT
              .replace("{topics}", topic_lines)
              .replace("{subtopics}", subtopic_lines)
              .replace("{diagrams}", ", ".join(sorted(DIAGRAMS))))
    return system, (
        f"PAPER FILE: {name}\n\n"
        "Extract every graded question part from the paper text below.  The "
        "text may contain OCR errors; classify what is visible and flag "
        "uncertain parts rather than inventing values.\n\n"
        f"PAPER TEXT:\n{text}\n"
    )


def call_paper(name: str, text: str, force: bool) -> tuple[str, LLMPaper, Usage]:
    raw_path = RAW_DIR / f"{slug(name)}.json"
    usage_path = RAW_DIR / f"{slug(name)}.usage.json"
    if raw_path.exists() and not force:
        data = json.loads(raw_path.read_text(encoding="utf-8"))
        usage = Usage()
        if usage_path.exists():
            saved = json.loads(usage_path.read_text(encoding="utf-8"))
            usage.add(saved.get("prompt_tokens", 0),
                      saved.get("completion_tokens", 0),
                      saved.get("total_tokens", 0),
                      model=saved.get("model", config.DEEPSEEK_MODEL))
        return name, LLMPaper.model_validate(data), usage
    system, user = build_prompt(name, text)
    result = chat_json_result(
        system, user, model=config.DEEPSEEK_MODEL, temperature=0.1,
        max_tokens=16000)
    paper = LLMPaper.model_validate(result.data)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(
        json.dumps(paper.model_dump(), indent=2, ensure_ascii=False),
        encoding="utf-8")
    usage_path.write_text(
        json.dumps(result.usage.as_dict(), indent=2), encoding="utf-8")
    return name, paper, result.usage


def aggregate_patterns(entries: list[QuestionEntry]) -> list[PatternRecord]:
    # Duplicate copies must not double-count a pattern's frequency.
    unique = [e for e in entries if not e.duplicate_of]
    groups: dict[str, list[QuestionEntry]] = defaultdict(list)
    for entry in unique:
        groups[f"{entry.topic}.{entry.subtopic}"].append(entry)
    records: list[PatternRecord] = []
    for pattern_id, rows in groups.items():
        marks = [r.marks for r in rows if r.marks is not None]
        blueprints = Counter(tuple(r.solution_blueprint) for r in rows)
        blueprint = list(blueprints.most_common(1)[0][0]) if blueprints else []
        parameter_types = sorted({p for r in rows for p in r.parameter_types})
        formula_forms = sorted({f for r in rows for f in r.formula_forms})
        diagrams = sorted({r.diagram for r in rows if r.diagram})
        commands = sorted({r.command for r in rows if r.command})
        papers = {r.paper for r in rows}
        examples = [r.entry_id for r in rows
                    if r.confidence == "high"][:5] or [r.entry_id for r in rows[:5]]
        representative = next(
            (r.question_pattern for r in rows if r.confidence == "high"
             and r.question_pattern), rows[0].question_pattern)
        records.append(PatternRecord(
            pattern_id=pattern_id,
            topic=rows[0].topic,
            topic_label=topic_label(rows[0].topic),
            subtopic=rows[0].subtopic,
            priority=priority_of(rows[0].topic),
            frequency=len(rows),
            paper_count=len(papers),
            example_entry_ids=examples,
            commands=commands,
            parameter_types=parameter_types,
            formula_forms=formula_forms,
            solution_blueprint=blueprint,
            diagram_types=diagrams,
            marks_min=min(marks) if marks else None,
            marks_max=max(marks) if marks else None,
            marks_mean=round(sum(marks) / len(marks), 2) if marks else None,
            representative_question=representative,
        ))
    records.sort(key=lambda r: (r.priority, -r.frequency, r.pattern_id))
    return records


def load_text_sources() -> dict[str, str]:
    index_path = TEXT_DIR / "index.json"
    if not index_path.exists():
        return {}
    data = json.loads(index_path.read_text(encoding="utf-8"))
    return {
        Path(item["paper"]).stem: item.get("source", "")
        for item in data
    }


def build_records(
        raw: dict[str, LLMPaper], texts: dict[str, str],
        duplicate_of: dict[str, str],
        text_sources: dict[str, str] | None = None) -> tuple[list[PaperRecord], list[QuestionEntry]]:
    text_sources = text_sources or {}
    paper_records: list[PaperRecord] = []
    entries: list[QuestionEntry] = []
    for name in sorted(raw):
        paper = raw[name]
        stem = Path(name).stem
        month, year = parse_month_year(name)
        duplicate = duplicate_of.get(name)
        text = texts.get(stem, "")
        flags: list[str] = []
        try:
            pages = len(pymupdf.open(str(PAPERS / name)))
        except Exception:
            pages = 0
        for part in paper.parts:
            topic, topic_flag = normalize_topic(part.topic)
            subtopic, subtopic_flag = normalize_subtopic(topic, part.subtopic)
            secondary = []
            for item in part.secondary_topics:
                sec, _ = normalize_topic(item)
                if sec != "other" and sec != topic and sec not in secondary:
                    secondary.append(sec)
            entry_flags = list(part.review_flags)
            if topic_flag:
                entry_flags.append(topic_flag)
            if subtopic_flag:
                entry_flags.append(subtopic_flag)
            if part.marks is None:
                entry_flags.append("marks_missing")
            elif float(part.marks) != int(part.marks):
                entry_flags.append(f"fractional_marks:{part.marks}")
            if part.confidence == "low":
                entry_flags.append("low_confidence")
            diagram = str(part.diagram or "none").strip().lower()
            if diagram not in DIAGRAMS:
                entry_flags.append(f"unknown_diagram:{part.diagram}")
                diagram = "none"
            if text and not evidence_verified(part.evidence, text):
                entry_flags.append("evidence_unverified")
            question = normalize_question(part.question)
            local_part = normalize_part(part.part)
            label = f"Q{question}{local_part}"
            entry_id = f"{stem}-{label}".replace(" ", "-")
            entries.append(QuestionEntry(
                entry_id=entry_id,
                paper=name,
                paper_stem=stem,
                month=month,
                year=year,
                question=question,
                part=local_part,
                marks=part.marks,
                topic=topic,
                secondary_topics=secondary,
                subtopic=subtopic,
                command=str(part.command or "solve").strip().lower(),
                question_pattern=part.question_pattern,
                givens=part.givens,
                parameter_types=part.parameter_types,
                formula_forms=part.formula_forms,
                solution_blueprint=part.solution_blueprint,
                diagram=diagram,
                evidence=part.evidence,
                confidence=part.confidence,
                review_flags=entry_flags,
                priority=priority_of(topic),
                topic_label=topic_label(topic),
                duplicate_of=duplicate,
            ))
        paper_entries = [e for e in entries if e.paper == name]
        marks_sum = sum(e.marks or 0 for e in paper_entries)
        questions = {e.question for e in paper_entries}
        if paper.total_marks is not None and marks_sum and paper.total_marks != marks_sum:
            # Keep the observed sum as the authoritative total; the model's
            # stated total is retained only as a review hint.
            flags.append(
                f"llm_total_marks_ignored:llm={paper.total_marks},sum={marks_sum}")
        if marks_sum > 130:
            flags.append(f"marks_sum_anomaly:{marks_sum}")
        if any("fractional_marks" in f for e in paper_entries for f in e.review_flags):
            flags.append("has_fractional_marks")
        if paper.question_count is not None and len(questions) != paper.question_count:
            flags.append(
                f"question_count_mismatch:llm={paper.question_count},found={len(questions)}")
        if duplicate:
            flags.append(f"duplicate_of:{duplicate}")
        if any(e.confidence == "low" for e in paper_entries):
            flags.append("has_low_confidence")
        if any("evidence_unverified" in e.review_flags for e in paper_entries):
            flags.append("has_unverified_evidence")
        paper_records.append(PaperRecord(
            paper=name,
            paper_stem=stem,
            month=month,
            year=year,
            pages=pages,
            text_source=text_sources.get(stem, ""),
            duplicate_of=duplicate,
            question_count=paper.question_count,
            total_marks=marks_sum or paper.total_marks,
            entry_count=len(paper_entries),
            marks_sum=marks_sum,
            notes=paper.notes,
            review_flags=flags,
        ))
    return paper_records, entries


def build_validation(
        papers: list[PaperRecord], entries: list[QuestionEntry]) -> ValidationSummary:
    warnings = []
    unknown_topic = sum(1 for e in entries if e.topic == "other")
    unknown_subtopic = sum(1 for e in entries if e.subtopic == "other")
    missing_marks = sum(1 for e in entries if e.marks is None)
    unverified = sum(1 for e in entries if "evidence_unverified" in e.review_flags)
    low = sum(1 for e in entries if e.confidence == "low")
    duplicate_entries = sum(1 for e in entries if e.duplicate_of)
    unique_papers = len({p.paper for p in papers if not p.duplicate_of})
    totals = [p.marks_sum for p in papers if p.marks_sum]
    if unknown_topic:
        warnings.append(f"{unknown_topic} entries fell into topic 'other'")
    if unknown_subtopic:
        warnings.append(f"{unknown_subtopic} entries fell into subtopic 'other'")
    if missing_marks:
        warnings.append(f"{missing_marks} entries have no mark")
    if unverified:
        warnings.append(f"{unverified} evidence fragments could not be matched")
    if duplicate_entries:
        warnings.append(f"{duplicate_entries} entries are duplicate-paper copies")
    return ValidationSummary(
        entries=len(entries),
        papers=len(papers),
        unique_papers=unique_papers,
        unknown_topic=unknown_topic,
        unknown_subtopic=unknown_subtopic,
        missing_marks=missing_marks,
        unverified_evidence=unverified,
        low_confidence=low,
        duplicate_entries=duplicate_entries,
        total_marks_min=min(totals) if totals else 0,
        total_marks_max=max(totals) if totals else 0,
        warnings=warnings,
    )


def taxonomy_with_observed(entries: list[QuestionEntry]) -> dict:
    data = taxonomy_dict()
    unique = [e for e in entries if not e.duplicate_of]
    topic_counts = Counter(e.topic for e in unique)
    topic_papers = {t: {e.paper for e in unique if e.topic == t} for t in TOPIC_IDS}
    subtopic_counts = Counter((e.topic, e.subtopic) for e in unique)
    subtopic_papers = defaultdict(set)
    for e in unique:
        subtopic_papers[(e.topic, e.subtopic)].add(e.paper)
    for topic in data["topics"]:
        topic["frequency"] = topic_counts.get(topic["id"], 0)
        topic["paper_count"] = len(topic_papers.get(topic["id"], set()))
        for sub in topic["subtopics"]:
            sub["frequency"] = subtopic_counts.get((topic["id"], sub["id"]), 0)
            sub["paper_count"] = len(
                subtopic_papers.get((topic["id"], sub["id"]), set()))
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--papers", nargs="*", default=[],
                        help="substring filters, e.g. 'FEBRUARY 2026'")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if not config.DEEPSEEK_API_KEY:
        print("DEEPSEEK_API_KEY is not set", file=sys.stderr)
        return 2
    texts = load_texts()
    names = sorted(
        p.name for p in PAPERS.glob("*.pdf")
        if p.stem in texts
    )
    if args.papers:
        names = [n for n in names
                 if any(f.lower() in n.lower() for f in args.papers)]
    if args.limit:
        names = names[:args.limit]
    _, duplicate_of = load_metadata()

    print(f"papers: {len(names)}; workers: {args.workers}", flush=True)
    raw: dict[str, LLMPaper] = {}
    total_usage = Usage()
    errors = []
    if args.workers <= 1:
        for index, name in enumerate(names, 1):
            try:
                _, paper, usage = call_paper(name, texts[Path(name).stem], args.force)
                raw[name] = paper
                total_usage.add(usage.prompt_tokens, usage.completion_tokens,
                                usage.total_tokens, model=usage.model)
                print(f"[{index}/{len(names)}] {name}: {len(paper.parts)} parts "
                      f"({usage.cost_usd:.4f} USD)", flush=True)
            except Exception as exc:
                errors.append((name, str(exc)))
                print(f"[{index}/{len(names)}] FAILED {name}: {exc}", flush=True)
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {
                pool.submit(call_paper, name, texts[Path(name).stem], args.force): name
                for name in names
            }
            for index, future in enumerate(as_completed(futures), 1):
                name = futures[future]
                try:
                    _, paper, usage = future.result()
                    raw[name] = paper
                    total_usage.add(usage.prompt_tokens, usage.completion_tokens,
                                    usage.total_tokens, model=usage.model)
                    print(f"[{index}/{len(names)}] {name}: {len(paper.parts)} parts "
                          f"({usage.cost_usd:.4f} USD)", flush=True)
                except Exception as exc:
                    errors.append((name, str(exc)))
                    print(f"[{index}/{len(names)}] FAILED {name}: {exc}", flush=True)

    if not raw:
        print("no papers parsed", file=sys.stderr)
        return 1
    papers, entries = build_records(raw, texts, duplicate_of,
                                    load_text_sources())
    patterns = aggregate_patterns(entries)
    validation = build_validation(papers, entries)
    log = QuestionLog(
        source_dir=str(PAPERS.relative_to(ROOT)),
        generated_by="scripts/build_mat133_question_log.py",
        model=config.DEEPSEEK_MODEL,
        papers=papers,
        entries=entries,
        patterns=patterns,
        validation=validation,
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "taxonomy.json").write_text(
        json.dumps(taxonomy_with_observed(entries), indent=2, ensure_ascii=False),
        encoding="utf-8")
    (OUT_DIR / "question_log.json").write_text(
        json.dumps(log.model_dump(), indent=2, ensure_ascii=False),
        encoding="utf-8")
    (OUT_DIR / "question_log.schema.json").write_text(
        json.dumps(QuestionLog.model_json_schema(), indent=2),
        encoding="utf-8")
    run = {
        "model": config.DEEPSEEK_MODEL,
        "papers_requested": len(names),
        "papers_parsed": len(raw),
        "errors": errors,
        "usage": total_usage.as_dict(),
    }
    (OUT_DIR / "question_log" / "run.json").write_text(
        json.dumps(run, indent=2), encoding="utf-8")
    print(json.dumps({
        "papers": len(papers),
        "entries": len(entries),
        "patterns": len(patterns),
        "usage": total_usage.as_dict(),
        "warnings": validation.warnings,
    }, indent=2), flush=True)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
