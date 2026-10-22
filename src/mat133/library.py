"""Build and cache deterministic MAT133 Library papers.

This is the MAT133 counterpart of ``src.app.prebuild_library``.  It has no
LLM calls: the planner regenerates the same paper for a seed, the MAT133
builder writes the paper/scheme DOCX and PDF, and a ``meta.json`` record is
written in the same shape the Library and public-bundle builders expect.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from src.app.filenames import utc_year
from src.app.jobs import cache_path
from src.mat133.build_docx import (build_paper_docx, build_scheme_docx,
                                   update_page_count, validate_docx,
                                   validate_pdf)
from src.mat133.planner import build_paper

SUBJECT = "MAT133"


def _files(out: Path, export: bool) -> dict[str, str]:
    files = {
        "paper_docx": str(out / "paper.docx"),
        "paper_pdf": str(out / "paper.pdf") if export else "",
        "scheme_docx": str(out / "scheme.docx"),
        "scheme_pdf": str(out / "scheme.pdf") if export else "",
    }
    return files


def _progress(paper) -> list[dict]:
    events = []
    for question in paper.questions:
        for part in question.parts:
            events.append({
                "question": f"Q{question.number}",
                "slot": f"Q{question.number}{part.label}",
                "status": "accepted",
                "message": part.topic,
                "cost_usd": 0,
                "calls": 0,
                "accepted": 1,
                "placeholders": 0,
            })
    return events


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
        else:
            if check.get("part_labels_found") != check.get("expected_parts"):
                problems.append(f"{name}: part labels mismatch")
    for name in ("paper_pdf", "scheme_pdf"):
        check = checks[name]
        if not check:
            continue
        if not check.get("page1_has_cover"):
            problems.append(f"{name}: cover missing")
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


def build_seed(seed: int, *, out_dir: Path | None = None, force: bool = False,
               export: bool = True, scheme_only: bool = False) -> dict:
    """Build (or reuse) one seed in the Library cache."""
    out = Path(out_dir) if out_dir is not None else cache_path(
        "realistic", seed, None, subject=SUBJECT)
    meta_path = out / "meta.json"
    if not force and not scheme_only and meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            meta = {}
        files = meta.get("files", {})
        if files and all(Path(path).exists() for path in files.values()
                         if path):
            return {"seed": seed, "cached": True, "path": str(out)}
    out.mkdir(parents=True, exist_ok=True)
    paper, plan = build_paper(seed, out_dir=out / "figures")
    created = time.time()
    year = utc_year(created)
    paper.year = year
    paper_docx = out / "paper.docx"
    scheme_docx = out / "scheme.docx"
    paper_pdf = out / "paper.pdf" if export else None
    scheme_pdf = out / "scheme.pdf" if export else None
    if scheme_only and paper_docx.exists():
        build_scheme_docx(paper, scheme_docx)
        if scheme_pdf is not None:
            update_page_count(scheme_docx, scheme_pdf, scheme=True)
    else:
        build_paper_docx(paper, paper_docx)
        build_scheme_docx(paper, scheme_docx)
        if export:
            update_page_count(paper_docx, paper_pdf, scheme=False)
            update_page_count(scheme_docx, scheme_pdf, scheme=True)
    validation = _validate(paper, paper_docx, scheme_docx,
                           Path(paper_pdf) if paper_pdf else None,
                           Path(scheme_pdf) if scheme_pdf else None)
    if validation["problems"]:
        raise RuntimeError(
            f"MAT133 seed {seed} validation failed: "
            + "; ".join(validation["problems"]))
    files = _files(out, export)
    progress = _progress(paper)
    summary = {
        "subject": SUBJECT,
        "seed": seed,
        "mode": "realistic",
        "computed_marks": None,
        "accepted": plan["accepted"],
        "placeholders": 0,
        "has_practice_mode": False,
        "has_placeholders": False,
        "model": "mat133-deterministic",
        "cost_usd": 0.0,
        "cached": True,
        "topic_marks": plan["topic_marks"],
        "total_marks": plan["total_marks"],
        "generator_ids": plan["generator_ids"],
        "pdf_available": bool(export),
    }
    meta = {
        "subject": SUBJECT,
        "seed": seed,
        "mode": "realistic",
        "computed_marks": None,
        "model": "mat133-deterministic",
        "cost_usd": 0.0,
        "accepted": plan["accepted"],
        "placeholders": 0,
        "has_practice_mode": False,
        "has_placeholders": False,
        "created": created,
        "year": year,
        "topic_marks": plan["topic_marks"],
        "total_marks": plan["total_marks"],
        "question_count": plan["question_count"],
        "generator_ids": plan["generator_ids"],
        "files": files,
        "summary": summary,
        "progress": progress,
        "validation": validation,
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return {"seed": seed, "cached": False, "path": str(out),
            "pdf": bool(export), "scheme_pdf": bool(export),
            "accepted": plan["accepted"], "total_marks": plan["total_marks"]}
