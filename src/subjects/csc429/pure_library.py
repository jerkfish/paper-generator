"""P8: publish the approved Type D seeds into the local Library cache.

No upload or deployment. The public bundle remains disabled.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import time
from collections import Counter
from pathlib import Path

from src import config

SUBJECT = "CSC429"
TRACKING = config.TRACKING_DIR / "csc429"
BANK = TRACKING / "bank"
SOURCE = config.PROJECT_ROOT / "outputs" / "pure_extraction" / "CSC429_all_seeds"
CACHE = config.WEB_CACHE_DIR / SUBJECT
MANIFEST = CACHE / "manifest.json"


def _load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _save(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _meta_for_seed(seed: int) -> dict:
    from src.app.jobs import cache_path
    out = cache_path("realistic", seed, None, subject=SUBJECT)
    source = SOURCE / f"seed_{seed:02d}"
    plan = _load(BANK / "plans" / f"seed_{seed:02d}.json", {})
    qa = _load(source / "qa.json", {})
    source_meta = _load(source / "meta.json", {})
    topic_marks = Counter()
    for slot in plan.get("slots") or []:
        topic_marks[slot["topic"]] += int(slot["marks"])
    created = time.time()
    files = {}
    for key, name in (
            ("paper_docx", "paper.docx"), ("paper_pdf", "paper.pdf"),
            ("scheme_docx", "scheme.docx"), ("scheme_pdf", "scheme.pdf")):
        src = source / name
        dst = out / name
        out.mkdir(parents=True, exist_ok=True)
        if src.is_file():
            shutil.copy2(src, dst)
            files[key] = str(dst)
    meta = {
        "subject": SUBJECT,
        "seed": seed,
        "mode": "realistic",
        "computed_marks": None,
        "model": "csc429-pure-extraction+deepseek-flash",
        "cost_usd": 0.0,
        "accepted": 11,
        "placeholders": 0,
        "total_slots": 11,
        "total_marks": 100,
        "question_count": 11,
        "has_practice_mode": False,
        "has_placeholders": False,
        "created": created,
        "year": 2026,
        "topic_marks": dict(sorted(topic_marks.items())),
        "files": files,
        "warnings": [],
        "format_status": "native_word_numbering_applied",
        "source_papers": source_meta.get("source_papers", []),
        "questions": source_meta.get("questions", []),
        "qa": {
            "problems": qa.get("problems", []),
            "paper_pages": (qa.get("paper") or {}).get("pages"),
            "scheme_pages": (qa.get("scheme") or {}).get("pages"),
            "word_version": qa.get("word_version"),
        },
        "summary": {
            "subject": SUBJECT,
            "seed": seed,
            "mode": "realistic",
            "accepted": 11,
            "placeholders": 0,
            "total_slots": 11,
            "total_marks": 100,
            "question_count": 11,
            "has_practice_mode": False,
            "has_placeholders": False,
            "model": "csc429-pure-extraction+deepseek-flash",
            "cost_usd": 0.0,
            "cached": True,
            "topic_marks": dict(sorted(topic_marks.items())),
            "pdf_available": True,
            "generated_slots": 0,
            "real_bank_slots": 11,
            "unofficial_answers": 11,
            "warnings": [],
            "format_status": "native_word_numbering_applied",
        },
        "progress": [
            {"question": slot["slot"], "slot": slot["slot"],
             "status": "approved", "message": slot["topic"],
             "cost_usd": 0.0, "calls": 0, "accepted": 1,
             "placeholders": 0}
            for slot in plan.get("slots") or []
        ],
    }
    _save(out / "meta.json", meta)
    return meta


def build_library(force: bool = False) -> dict:
    rows = []
    for seed in range(1, 21):
        source = SOURCE / f"seed_{seed:02d}"
        if not source.is_dir():
            raise RuntimeError(f"missing assembled seed: {source}")
        meta = _meta_for_seed(seed)
        rows.append({
            "seed": seed,
            "path": str(Path(meta["files"]["paper_pdf"]).parent),
            "paper_pdf": meta["files"]["paper_pdf"],
            "scheme_pdf": meta["files"]["scheme_pdf"],
            "paper_pages": meta["qa"]["paper_pages"],
            "scheme_pages": meta["qa"]["scheme_pages"],
            "problems": meta["qa"]["problems"],
            "source_papers": meta["source_papers"],
            "questions": meta["questions"],
            "topic_marks": meta["topic_marks"],
        })
    usage = _load(TRACKING / "usage.json", {})
    manifest = {
        "schema_version": 1,
        "subject": SUBJECT,
        "type": "D",
        "strategy": "pure_extraction",
        "status": "local_library_prebuilt",
        "publication": False,
        "seeds": rows,
        "counts": {
            "seeds": len(rows),
            "qa_failures": sum(1 for row in rows if row["problems"]),
            "accepted": 11 * len(rows),
            "placeholders": 0,
        },
        "format_status": "native_word_numbering_applied",
        "question_headings": "QUESTION 1..11",
        "templates": {
            "paper": "data/tracking/csc429/templates/paper_template_good_example_recreational.docx",
            "scheme": "data/tracking/csc429/templates/scheme_template_fix_wide_content.docx",
        },
        "rejected_registry": "data/tracking/csc429/rejected_registry.json",
        "cost": usage,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    _save(MANIFEST, manifest)
    return manifest


def library_seeds() -> list[int]:
    manifest = _load(MANIFEST, {})
    seeds = [int(row["seed"]) for row in manifest.get("seeds", [])]
    return sorted(seed for seed in seeds if seed > 0) or list(range(1, 21))


def library_metadata(seed: int) -> dict:
    from src.app.jobs import cache_path
    path = cache_path("realistic", int(seed), None, subject=SUBJECT)
    return _load(path / "meta.json", {})


def build_seed(seed: int, force: bool = False, **kwargs) -> dict:
    if not force:
        meta = library_metadata(seed)
        if meta:
            return {"seed": int(seed), "cached": True, "path": meta.get(
                "files", {}).get("paper_pdf", "")}
    build_library(force=force)
    meta = library_metadata(seed)
    return {"seed": int(seed), "cached": False, "path": meta.get(
        "files", {}).get("paper_pdf", "")}


def main() -> None:
    print(json.dumps(build_library(), indent=2, ensure_ascii=False)[:4000])


if __name__ == "__main__":
    main()
