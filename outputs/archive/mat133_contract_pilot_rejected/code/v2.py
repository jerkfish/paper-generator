"""MAT133 playbook-v2 documents.

The v1 Library under ``src/mat133`` is complete and published.  This module
adds a second document version beside it without touching any v1 file:

- the paper is rebuilt with the approved MAT133 template;
- the scheme starts from the standard UTM marking-scheme cover required by the
  playbook, then appends the same ``NO | SOLUTION | MARK`` table;
- v2 files live in the existing seed cache folder as ``paper_v2.*`` and
  ``scheme_v2.*`` and are recorded under ``document_versions`` in ``meta.json``.

No LLM call is made.  The same seed produces the same paper as v1, so the v1
approval remains the content basis while the v2 contract and cover are tested.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

import docx
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

from src import config
from src.app.filenames import utc_year
from src.app.jobs import cache_path
from src.mat133.build_docx import (
    _add_scheme_row,
    _month_full,
    _month_short,
    _repeat_header,
    _run,
    _set_table_grid,
    _set_text,
    build_paper_docx,
    update_page_count,
    validate_docx,
    validate_pdf,
)
from src.mat133.planner import build_paper

SUBJECT = "MAT133"
DOCUMENT_VERSION = 2
PLAYBOOK_VERSION = "2.0"
TRACKING = config.TRACKING_DIR / "mat133" / "v2"
SCHEME_TEMPLATE = (config.REFERENCE_DIR / "standard" /
                   "UTM_STANDARD_MARKING_SCHEME.docx")
FORMAT_PROFILE = TRACKING / "format_profile.json"
TEMPLATE_CHECK = TRACKING / "template_check.json"
ANSWERS_DIR = TRACKING / "answers"
REVIEW_DIR = config.OUTPUTS_DIR / "review" / "mat133_v2"

# Template text nodes that must change for MAT133.  Keys are complete <w:t>
# contents, so we never damage a substring such as OCTOBER with a naked OCT
# replacement.
_TEMPLATE_TEXT = {
    "CS/MOCK": "CS/{month_short}",
    "CS/MOCK OCT": "CS/{month_short}",
    "OCT": "",
    "2026/CSC662": "{year}/MAT133",
    "OCTOBER 2026 (MOCK)": "{month} {year}",
    "COMPUTER SECURITY": "PRE CALCULUS",
    "CSC662": "MAT133",
    "3 HOURS": "{duration}",
}


def _parts(paper) -> list[dict]:
    rows = []
    for question in paper.questions:
        for part in question.parts:
            rows.append({
                "question": f"MAT133-S{paper.seed:02d}-Q{question.number}"
                            f"{part.label}",
                "paper_seed": paper.seed,
                "question_no": question.number,
                "label": part.label,
                "marks": part.marks,
                "topic": part.topic,
                "subtopic": part.subtopic,
                "answer": part.answer,
                "answer_latex": part.answer_latex,
                "solution_latex": list(part.solution_latex),
                "marking_notes": list(part.marking_notes),
                "provenance": "solver_verified",
                "solver": "src.mat133.generators",
                "verification": (
                    "deterministic generator; exact answer and worked "
                    "solution emitted with the part"),
                "confidence": "high",
            })
    return rows


def _template_values(paper) -> dict[str, str]:
    return {
        "month": _month_full(paper.month),
        "month_short": _month_short(paper.month),
        "year": str(paper.year),
        "duration": paper.duration,
    }


def _rewrite_text_nodes(xml: str, values: dict[str, str]) -> str:
    mapping = {key: value.format(**values)
               for key, value in _TEMPLATE_TEXT.items()}

    def replace(match):
        whole, prefix, text, suffix = (
            match.group(0), match.group(1), match.group(2), match.group(3))
        if text in mapping:
            return prefix + mapping[text] + suffix
        return whole

    return re.sub(r"(<w:t\b[^>]*>)(.*?)(</w:t>)", replace, xml, flags=re.S)


def _patched_scheme_template(paper, target: Path) -> Path:
    values = _template_values(paper)
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(SCHEME_TEMPLATE) as source, zipfile.ZipFile(
            target, "w", zipfile.ZIP_DEFLATED) as out:
        for item in source.infolist():
            data = source.read(item.filename)
            if item.filename.endswith(".xml") and (
                    item.filename == "word/document.xml"
                    or item.filename.startswith("word/header")
                    or item.filename.startswith("word/footer")):
                data = _rewrite_text_nodes(
                    data.decode("utf-8"), values).encode("utf-8")
            out.writestr(item, data)
    return target


def _clean_note(paragraph, text: str, *, continuation: bool = False) -> None:
    """Replace a note and give it a uniform hanging-indent layout."""
    _set_text(paragraph._p, text)
    for tab in paragraph._p.findall(".//" + qn("w:tab")):
        parent = tab.getparent()
        if parent is not None:
            parent.remove(tab)
    fmt = paragraph.paragraph_format
    fmt.left_indent = Inches(0.45)
    fmt.right_indent = Inches(0)
    fmt.first_line_indent = Inches(0) if continuation else Inches(-0.45)
    fmt.space_before = Pt(0 if continuation else 6)
    fmt.space_after = Pt(4)
    fmt.line_spacing = 1.0
    fmt.alignment = WD_ALIGN_PARAGRAPH.LEFT


def _scheme_notes(doc, paper) -> None:
    month = _month_full(paper.month)
    total = paper.total_marks
    parts = sum(len(question.parts) for question in paper.questions)
    replacements = {
        11: (f"This marking scheme accompanies the MAT133 mock paper "
             f"({month.title()} {paper.year})."),
        12: ("Computed answers show working; every answer is produced by the "
             "deterministic MAT133 generator and verified by code where "
             "possible. No model answer is presented as official."),
        14: ("Every marking point comes from the generator's worked solution; "
             "M1/A1 codes are aligned from the final answer backwards."),
        17: f"Five questions; total = {total:g} marks.",
        18: f"Computed: {parts} part(s). Placeholders: 0.",
        19: "Questions and answers are for local study use only.",
        21: (f"Generated deterministically from the 41 MAT133 past papers; "
             f"seed {paper.seed}."),
    }
    paragraphs = doc.paragraphs
    for index, text in replacements.items():
        if index < len(paragraphs):
            _clean_note(paragraphs[index], text,
                        continuation=index in (12, 19))


def _scheme_body_section(doc, paper) -> None:
    """Configure the template's existing body section for MAT133."""
    section = doc.sections[-1]
    section.start_type = WD_SECTION.NEW_PAGE
    section.different_first_page_header_footer = False
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.footer.is_linked_to_previous = True

    def fill_header(header) -> None:
        header.is_linked_to_previous = False
        paragraph = header.paragraphs[0]
        paragraph.text = ""
        paragraph.paragraph_format.tab_stops.add_tab_stop(
            Inches(6.25), WD_TAB_ALIGNMENT.RIGHT)
        _run(paragraph, f"CS/{_month_short(paper.month)} {paper.year}/MAT133",
             size=8, bold=True)
        _run(paragraph, "\tCONFIDENTIAL", size=8, bold=True)

    fill_header(section.header)
    fill_header(section.even_page_header)


def build_scheme_docx_v2(paper, out_docx: Path) -> Path:
    """Build the v2 scheme from the standard marking-scheme cover."""
    import tempfile

    with tempfile.TemporaryDirectory(prefix="mat133_v2_template_") as tmp:
        template = _patched_scheme_template(
            paper, Path(tmp) / "scheme_template.docx")
        doc = docx.Document(str(template))
    _scheme_notes(doc, paper)
    _scheme_body_section(doc, paper)
    table = doc.add_table(rows=1, cols=3)
    table.autofit = False
    table.columns[0].width = Inches(0.8)
    table.columns[1].width = Inches(4.9)
    table.columns[2].width = Inches(0.8)
    _set_table_grid(table)
    for cell, text in zip(table.rows[0].cells, ("NO", "SOLUTION", "MARK")):
        cell.width = Inches(0.8) if text != "SOLUTION" else Inches(4.9)
        _run(cell.paragraphs[0], text, bold=True, size=10)
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    _repeat_header(table.rows[0])
    with tempfile.TemporaryDirectory(prefix="mat133_v2_latex_") as tmp:
        latex_dir = Path(tmp)
        counter = [0]
        for question in paper.questions:
            for part in question.parts:
                _add_scheme_row(doc, table, question, part, latex_dir, counter)
        out_docx.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(out_docx))
    return out_docx


def _validate(paper, paper_docx: Path, scheme_docx: Path,
              paper_pdf: Path | None, scheme_pdf: Path | None) -> dict:
    checks = {
        "paper_docx": validate_docx(paper_docx, paper),
        "scheme_docx": validate_docx(scheme_docx, paper, scheme=True),
        "paper_pdf": validate_pdf(paper_pdf, paper) if paper_pdf else {},
        "scheme_pdf": (validate_pdf(scheme_pdf, paper, scheme=True)
                       if scheme_pdf else {}),
    }
    problems: list[str] = []
    for name in ("paper_docx", "scheme_docx"):
        check = checks[name]
        if not check.get("xml_valid"):
            problems.append(f"{name}: invalid XML")
        if check.get("forbidden_tokens"):
            problems.append(f"{name}: forbidden tokens "
                            f"{check['forbidden_tokens']}")
        if not check.get("has_crest"):
            problems.append(f"{name}: crest missing")
        if name == "paper_docx":
            if check.get("question_headings") != check.get("expected_questions"):
                problems.append(f"{name}: question headings mismatch")
        elif check.get("part_labels_found") != check.get("expected_parts"):
            problems.append(f"{name}: part labels mismatch")
    for name in ("paper_pdf", "scheme_pdf"):
        check = checks[name]
        if not check:
            continue
        if not check.get("page1_has_cover"):
            problems.append(f"{name}: cover missing")
        if not check.get("page1_has_mat133"):
            problems.append(f"{name}: MAT133 missing from cover")
        if not check.get("body_starts_on_page2"):
            problems.append(f"{name}: body does not start on page 2")
        if not check.get("headings_found"):
            problems.append(f"{name}: headings/labels missing")
        if not check.get("full_marks"):
            problems.append(f"{name}: marks missing")
        if check.get("forbidden_tokens"):
            problems.append(f"{name}: forbidden tokens "
                            f"{check['forbidden_tokens']}")
        if check.get("right_overflow"):
            problems.append(f"{name}: right-margin overflow "
                            f"{check['right_overflow'][:2]}")
    checks["problems"] = problems
    return checks


def write_format_profile() -> dict:
    profile = {
        "schema_version": 2,
        "playbook_version": PLAYBOOK_VERSION,
        "subject": SUBJECT,
        "era": "current",
        "strategy": "generate",
        "sources": {
            "papers": "data/papers/MAT133",
            "paper_count": 41,
            "fingerprint": "data/tracking/mat133/scheme_fingerprint.json",
            "question_log": "data/tracking/mat133/question_log.json",
        },
        "sections": [{
            "key": "Q",
            "questions": 5,
            "parts_per_question": "3 (fixed)",
            "marks_per_slot": "variable by generator",
        }],
        "parts_per_paper": 15,
        "total_marks": {
            "observed": "64-72",
            "policy": "sum of generated part marks; no fixed 100-mark total",
        },
        "duration": "2 HOURS",
        "numbering": {
            "question": "QUESTION n",
            "subparts": "a), b), c)",
            "scheme_table": "NO | SOLUTION | MARK",
        },
        "templates": {
            "paper": "data/reference/MAT133/MAT133 TEMPLATE.docx",
            "scheme": "data/reference/standard/"
                      "UTM_STANDARD_MARKING_SCHEME.docx",
        },
        "answers": {
            "source": "deterministic generator",
            "provenance": "solver_verified",
        },
        "basis": (
            "Mapped from the approved v1 MAT133 planner and question log. "
            "The five-question, fifteen-part structure and 64-72 mark range "
            "are the observed paper-derived format; v2 keeps that contract."),
    }
    FORMAT_PROFILE.parent.mkdir(parents=True, exist_ok=True)
    FORMAT_PROFILE.write_text(json.dumps(profile, indent=2) + "\n",
                              encoding="utf-8")
    return profile


def _docx_structure(path: Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml")
        ET.fromstring(xml)
        names = archive.namelist()
        headers = [name for name in names if name.startswith("word/header")]
        text = "".join(re.findall(r"<w:t\b[^>]*>([^<]*)</w:t>",
                                  xml.decode("utf-8")))
    return {
        "xml_valid": True,
        "has_cover_text": "UNIVERSITI TEKNOLOGI MARA" in text,
        "has_header": bool(headers),
        "header_parts": headers,
        "has_crest": any(name.startswith("word/media/") for name in names),
    }


def write_template_check(paper_docx: Path, paper_pdf: Path,
                         scheme_docx: Path, scheme_pdf: Path) -> dict:
    """Record the V3 template check and rendered cover evidence."""
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    covers = {}
    try:
        import pymupdf
        for name, pdf in (("paper", paper_pdf), ("scheme", scheme_pdf)):
            target = REVIEW_DIR / f"{name}_v2_cover_p1.png"
            with pymupdf.open(str(pdf)) as document:
                page = document[0]
                page.get_pixmap(dpi=110).save(str(target))
            covers[name] = str(target)
    except Exception as exc:  # pragma: no cover - visual aid only
        covers = {"error": str(exc)}
    check = {
        "schema_version": 2,
        "subject": SUBJECT,
        "checked_on": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "paper": {
            "path": str(paper_docx),
            **_docx_structure(paper_docx),
            "cover_render": covers.get("paper", ""),
        },
        "scheme": {
            "path": str(scheme_docx),
            **_docx_structure(scheme_docx),
            "cover_render": covers.get("scheme", ""),
        },
        "templates": {
            "paper": "data/reference/MAT133/MAT133 TEMPLATE.docx",
            "scheme": "data/reference/standard/"
                      "UTM_STANDARD_MARKING_SCHEME.docx",
        },
        "notes": (
            "The paper template is the approved MAT133 v1 template. The v2 "
            "scheme uses the standard UTM marking-scheme cover required by "
            "AGENTS.md; its fields are patched from the standard template, "
            "not a bespoke cover."),
    }
    TEMPLATE_CHECK.parent.mkdir(parents=True, exist_ok=True)
    TEMPLATE_CHECK.write_text(json.dumps(check, indent=2) + "\n",
                              encoding="utf-8")
    return check


def _review_copies(seed: int, files: dict) -> dict:
    """Keep stable review copies outside the cache for gate evidence."""
    target = REVIEW_DIR / "seeds"
    target.mkdir(parents=True, exist_ok=True)
    names = {
        "paper_docx": f"seed_{seed:02d}_paper_v2.docx",
        "paper_pdf": f"seed_{seed:02d}_paper_v2.pdf",
        "scheme_docx": f"seed_{seed:02d}_scheme_v2.docx",
        "scheme_pdf": f"seed_{seed:02d}_scheme_v2.pdf",
    }
    copied = {}
    for kind, destination in names.items():
        source = Path(str(files.get(kind, "")))
        if source.exists():
            shutil.copy2(source, target / destination)
            copied[kind] = str(target / destination)
        else:
            copied[kind] = ""
    return copied


def _gate_b_approved() -> bool:
    path = config.PROJECT_ROOT / "subjects/MAT133/lifecycle_state.json"
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    gate = (state.get("gates") or {}).get("B") or {}
    return str(gate.get("status", "")).lower() == "approved"


def build_seed_v2(seed: int, *, force: bool = False,
                  export: bool = True) -> dict:
    """Build or reuse the v2 documents for one seed.

    Seeds 1-3 are the Gate B pilot. Seeds 4+ are blocked until the owner
    records Gate B approval in the lifecycle state.
    """
    if int(seed) > 3 and not _gate_b_approved():
        raise RuntimeError(
            f"MAT133 seed {seed}: Gate B is not approved; seeds 4+ are "
            "blocked (see docs/SUBJECT_PLAYBOOK.md V5).")
    out = cache_path("realistic", seed, None, subject=SUBJECT)
    meta_path = out / "meta.json"
    if not meta_path.exists():
        raise RuntimeError(
            f"MAT133 seed {seed}: v1 cache is missing at {out}")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    paper_docx = out / "paper_v2.docx"
    paper_pdf = out / "paper_v2.pdf" if export else None
    scheme_docx = out / "scheme_v2.docx"
    scheme_pdf = out / "scheme_v2.pdf" if export else None
    if (not force and paper_docx.exists() and scheme_docx.exists()
            and (not export or (paper_pdf.exists() and scheme_pdf.exists()))):
        return {"seed": seed, "cached": True, "path": str(out)}

    created_at = float(meta.get("created") or 0)
    if created_at:
        library_month = datetime.fromtimestamp(
            created_at, timezone.utc).strftime("%B").upper()
    else:
        library_month = None
    paper, plan = build_paper(
        seed, year=int(meta.get("year") or utc_year()),
        month=library_month, out_dir=out / "figures_v2")
    build_paper_docx(paper, paper_docx)
    build_scheme_docx_v2(paper, scheme_docx)
    if export:
        update_page_count(paper_docx, paper_pdf, scheme=False)
        update_page_count(scheme_docx, scheme_pdf, scheme=True)
    validation = _validate(
        paper, paper_docx, scheme_docx,
        Path(paper_pdf) if paper_pdf else None,
        Path(scheme_pdf) if scheme_pdf else None)
    if validation["problems"]:
        raise RuntimeError(
            f"MAT133 seed {seed} v2 validation failed: "
            + "; ".join(validation["problems"]))

    answers = _parts(paper)
    ANSWERS_DIR.mkdir(parents=True, exist_ok=True)
    answers_path = ANSWERS_DIR / f"seed_{seed:02d}.json"
    answers_path.write_text(json.dumps({
        "schema_version": 2,
        "subject": SUBJECT,
        "seed": seed,
        "playbook_version": PLAYBOOK_VERSION,
        "count": len(answers),
        "parts": answers,
    }, indent=2) + "\n", encoding="utf-8")
    write_format_profile()

    built = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    files = {
        "paper_docx": str(paper_docx),
        "paper_pdf": str(paper_pdf) if export else "",
        "scheme_docx": str(scheme_docx),
        "scheme_pdf": str(scheme_pdf) if export else "",
    }
    review_files = _review_copies(seed, files)
    if export and (seed == 1 or not TEMPLATE_CHECK.exists()):
        write_template_check(paper_docx, paper_pdf, scheme_docx, scheme_pdf)
    versions = dict(meta.get("document_versions") or {})
    versions[str(DOCUMENT_VERSION)] = {
        "version": DOCUMENT_VERSION,
        "label": f"v{DOCUMENT_VERSION}",
        "playbook_version": PLAYBOOK_VERSION,
        "built": built,
        "files": files,
        "validation": validation,
        "answers": str(answers_path),
        "format_profile": str(FORMAT_PROFILE),
        "template_check": str(TEMPLATE_CHECK),
        "review_files": review_files,
        "source": "deterministic MAT133 planner; v1 content basis",
    }
    meta["document_versions"] = versions
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return {
        "seed": seed,
        "cached": False,
        "path": str(out),
        "files": files,
        "marks": plan["total_marks"],
        "parts": len(answers),
        "validation": validation,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build MAT133 playbook-v2 documents beside v1.")
    parser.add_argument("--seeds", default="1-3",
                        help="seed or range/list, e.g. 1-3 or 1,2,5")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--no-pdf", action="store_true")
    args = parser.parse_args()
    values = []
    for chunk in args.seeds.split(","):
        if "-" in chunk:
            start, end = chunk.split("-", 1)
            values.extend(range(int(start), int(end) + 1))
        elif chunk.strip():
            values.append(int(chunk))
    results = [build_seed_v2(seed, force=args.force,
                             export=not args.no_pdf) for seed in values]
    for result in results:
        print(json.dumps({key: value for key, value in result.items()
                          if key != "validation"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
