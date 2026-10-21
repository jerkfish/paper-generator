"""Prebuild the no-LLM Library cache from the 20-seed accepted sets."""
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

from src import config
from src.app.filenames import utc_year
from src.app.jobs import DEFAULT_SUBJECT, cache_path
from src.assemble.generic_build import build_paper, build_scheme
from src.subjects.registry import SubjectNotFound, get_subject

SRC = config.OUTPUTS_DIR / "eval_final_deepseek"


def build_scheme_only(seed: int, subject: str = DEFAULT_SUBJECT) -> dict:
    """Rebuild only the scheme from stored plan/theory/cache paper."""
    plan = SRC / f"seed_{seed:02d}_planner.json"
    theory = SRC / f"seed_{seed:02d}_theory.json"
    out = cache_path("realistic", seed, None, subject=subject)
    paper_docx = out / "paper.docx"
    if not plan.exists() or not theory.exists() or not paper_docx.exists():
        return build_seed(seed, force=True, subject=subject)
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
               subject: str = DEFAULT_SUBJECT) -> dict:
    plan = SRC / f"seed_{seed:02d}_planner.json"
    theory = SRC / f"seed_{seed:02d}_theory.json"
    if not plan.exists() or not theory.exists():
        raise FileNotFoundError(f"missing seed {seed}")
    out = cache_path("realistic", seed, None, subject=subject)
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
        m = re.match(r"([AB]\d+)", slot)
        progress.append({"question": m.group(1) if m else slot,
                         "slot": slot, "status": "accepted",
                         "message": "", "cost_usd": 0,
                         "accepted": 0, "placeholders": 0})
    for p in payload.get("placeholders", []):
        slot = str(p.get("slot", ""))
        m = re.match(r"([AB]\d+)", slot)
        progress.append({"question": m.group(1) if m else slot,
                         "slot": slot, "status": "placeholder",
                         "message": str(p.get("reason", ""))[:200],
                         "cost_usd": 0, "accepted": 0, "placeholders": 0})
    created = time.time()
    meta = {
        "subject": subject.upper(),
        "seed": seed,
        "mode": "realistic",
        "computed_marks": None,
        "model": payload.get("model", ""),
        "cost_usd": payload.get("usage", {}).get("cost_usd", 0.0),
        "accepted": len(payload.get("accepted", [])),
        "placeholders": len(payload.get("placeholders", [])),
        "created": created,
        "year": utc_year(created),
        "topic_marks": topic_marks,
        "files": files,
        "progress": progress,
        "summary": {
            "subject": subject.upper(),
            "seed": seed,
            "mode": "realistic",
            "accepted": len(payload.get("accepted", [])),
            "placeholders": len(payload.get("placeholders", [])),
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
    ap.add_argument("--subject", default=DEFAULT_SUBJECT)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--schemes-only", action="store_true")
    args = ap.parse_args()
    try:
        subject = get_subject(args.subject)
    except SubjectNotFound:
        raise SystemExit(f"unknown subject: {args.subject}") from None
    if not subject.available:
        raise SystemExit(f"subject {subject.code} is coming soon")
    if subject.code != DEFAULT_SUBJECT:
        raise SystemExit(f"subject {subject.code} has no generator plugin")
    args.subject = subject.code
    if "-" in args.seeds:
        a, b = args.seeds.split("-")
        seeds = range(int(a), int(b) + 1)
    else:
        seeds = [int(x) for x in args.seeds.split(",")]
    for seed in seeds:
        try:
            if args.schemes_only:
                print(build_scheme_only(seed, subject=args.subject), flush=True)
            else:
                print(build_seed(seed, force=args.force, subject=args.subject), flush=True)
        except Exception as e:
            print(f"seed {seed}: ERROR {e}", flush=True)


if __name__ == "__main__":
    main()
