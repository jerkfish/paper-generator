"""Prebuild the no-LLM Library cache for a registered subject.

The subject's capabilities decide the path:

* a ``prebuild`` plugin (type B/C) builds each seed itself;
* otherwise a type-A subject uses its ``plan_inputs`` plugin to discover the
  stored planner/theory JSON and rebuilds the paper/scheme from them.

There is no subject allow-list in this module.
"""
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

from src import config
from src.app.filenames import utc_year
from src.app.jobs import cache_path
from src.assemble.generic_build import build_paper, build_scheme
from src.bank.gates import require_seed_gate
from src.subjects.plugins import plugin_for, require_plugin
from src.subjects.registry import (Subject, SubjectNotFound,
                                   default_subject_code, get_subject)


def _record(subject: str | Subject | None) -> Subject:
    if isinstance(subject, Subject):
        return subject
    try:
        return get_subject(subject or default_subject_code())
    except SubjectNotFound:
        raise SystemExit(f"unknown subject: {subject}") from None


def build_scheme_only(seed: int,
                      subject: str | Subject | None = None) -> dict:
    """Rebuild only the scheme from stored plan/theory/cache paper."""
    record = _record(subject)
    require_seed_gate(record.code, seed)
    plugin = plugin_for(record, "prebuild")
    if plugin is not None:
        return plugin(seed, scheme_only=True)
    if record.strategy == "recycle":
        raise SystemExit(
            f"{record.code}: no recycle assembler is registered; a recycle "
            "subject must build through its bank/assembler, not the LLM "
            "prebuild path")
    inputs = require_plugin(record, "plan_inputs")(seed)
    plan = Path(inputs["plan"])
    theory = Path(inputs["theory"])
    out = cache_path("realistic", seed, None, subject=record.code)
    paper_docx = out / "paper.docx"
    if not plan.exists() or not theory.exists() or not paper_docx.exists():
        return build_seed(seed, force=True, subject=record)
    scheme = build_scheme(paper_docx, plan, theory,
                          out / "scheme.docx", out / "scheme.pdf",
                          public=config.PUBLIC_BUILD)
    meta_path = out / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["files"]["scheme_docx"] = scheme.get("docx", "")
    meta["files"]["scheme_pdf"] = scheme.get("pdf", "")
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return {"seed": seed, "scheme_only": True, "path": str(out),
            "scheme_pdf": bool(scheme.get("pdf"))}


def build_seed(seed: int, force: bool = False,
               subject: str | Subject | None = None) -> dict:
    record = _record(subject)
    require_seed_gate(record.code, seed)
    plugin = plugin_for(record, "prebuild")
    if plugin is not None:
        return plugin(seed, force=force)
    if record.strategy == "recycle":
        raise SystemExit(
            f"{record.code}: no recycle assembler is registered; a recycle "
            "subject must build through its bank/assembler, not the LLM "
            "prebuild path")
    return _build_llm_seed(seed, force=force, record=record)


def _build_llm_seed(seed: int, *, force: bool, record: Subject) -> dict:
    inputs = require_plugin(record, "plan_inputs")(seed)
    plan = Path(inputs["plan"])
    theory = Path(inputs["theory"])
    if not plan.exists() or not theory.exists():
        raise FileNotFoundError(f"missing seed {seed}")
    out = cache_path("realistic", seed, None, subject=record.code)
    if not force and (out / "meta.json").exists():
        return {"seed": seed, "cached": True, "path": str(out)}
    out.mkdir(parents=True, exist_ok=True)
    paper = build_paper(plan, theory, out / "paper.docx",
                        out / "paper.pdf", public=config.PUBLIC_BUILD)
    scheme = build_scheme(out / "paper.docx", plan, theory,
                          out / "scheme.docx", out / "scheme.pdf",
                          public=config.PUBLIC_BUILD)
    payload = json.loads(theory.read_text(encoding="utf-8"))
    plan_data = json.loads(plan.read_text(encoding="utf-8"))
    topic_marks = dict(plan_data.get("assigned_topic_marks") or {})
    files = {
        "paper_docx": paper.get("docx", ""),
        "paper_pdf": paper.get("pdf", ""),
        "scheme_docx": scheme.get("docx", ""),
        "scheme_pdf": scheme.get("pdf", ""),
    }
    progress = []
    for q in payload.get("accepted", []):
        slot = str(q.get("slot", ""))
        question = str(q.get("question", ""))
        if not question:
            match = re.match(r"^([A-Z]+\d+)", slot)
            question = match.group(1) if match else slot
        progress.append({"question": question, "slot": slot,
                         "status": "accepted", "message": "",
                         "cost_usd": 0, "calls": 0, "accepted": 0,
                         "placeholders": 0})
    for p in payload.get("placeholders", []):
        slot = str(p.get("slot", ""))
        question = str(p.get("question", ""))
        if not question:
            match = re.match(r"^([A-Z]+\d+)", slot)
            question = match.group(1) if match else slot
        progress.append({"question": question, "slot": slot,
                         "status": "placeholder",
                         "message": str(p.get("reason", ""))[:200],
                         "cost_usd": 0, "calls": 0, "accepted": 0,
                         "placeholders": 0})
    created = time.time()
    total_slots = len(payload.get("accepted", [])) + len(
        payload.get("placeholders", []))
    meta = {
        "subject": record.code,
        "seed": seed,
        "mode": "realistic",
        "computed_marks": None,
        "model": payload.get("model", ""),
        "cost_usd": payload.get("usage", {}).get("cost_usd", 0.0),
        "accepted": len(payload.get("accepted", [])),
        "placeholders": len(payload.get("placeholders", [])),
        "total_slots": total_slots,
        "has_practice_mode": record.has_practice_mode,
        "has_placeholders": record.has_placeholders,
        "created": created,
        "year": utc_year(created),
        "topic_marks": topic_marks,
        "files": files,
        "progress": progress,
        "summary": {
            "subject": record.code,
            "seed": seed,
            "mode": "realistic",
            "accepted": len(payload.get("accepted", [])),
            "placeholders": len(payload.get("placeholders", [])),
            "total_slots": total_slots,
            "has_practice_mode": record.has_practice_mode,
            "has_placeholders": record.has_placeholders,
            "model": payload.get("model", ""),
            "cost_usd": payload.get("usage", {}).get("cost_usd", 0.0),
            "cached": True,
            "topic_marks": topic_marks,
            "pdf_available": bool(paper.get("pdf")),
        },
    }
    (out / "meta.json").write_text(json.dumps(meta, indent=2),
                                   encoding="utf-8")
    return {"seed": seed, "cached": False, "path": str(out),
            "pdf": bool(paper.get("pdf")),
            "scheme_pdf": bool(scheme.get("pdf"))}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="1-20")
    ap.add_argument("--subject", default=default_subject_code())
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--schemes-only", action="store_true")
    args = ap.parse_args()
    try:
        subject = get_subject(args.subject)
    except SubjectNotFound:
        raise SystemExit(f"unknown subject: {args.subject}") from None
    if not subject.available:
        raise SystemExit(f"subject {subject.code} is coming soon")
    if not subject.capabilities.get("generation"):
        raise SystemExit(f"subject {subject.code} has no generation capability")
    args.subject = subject.code
    if "-" in args.seeds:
        a, b = args.seeds.split("-")
        seeds = range(int(a), int(b) + 1)
    else:
        seeds = [int(x) for x in args.seeds.split(",")]
    for seed in seeds:
        try:
            if args.schemes_only:
                print(build_scheme_only(seed, subject=args.subject),
                      flush=True)
            else:
                print(build_seed(seed, force=args.force,
                                 subject=args.subject), flush=True)
        except Exception as e:
            print(f"seed {seed}: ERROR {e}", flush=True)


if __name__ == "__main__":
    main()
