"""In-process background jobs, cache and library for the local web UI.

Generation is dispatched from subject capabilities and plugins, never from a
subject code.  A type-A/C subject supplies a ``plan`` plugin and uses the LLM
theory pipeline.  A type-B subject supplies a ``prebuild`` plugin that writes
the paper/scheme and ``meta.json`` itself, with no LLM call.
"""
from __future__ import annotations

import hashlib
import json
import random
import re
import shutil
import threading
import time
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from src import config
from src.app.filenames import download_filename, utc_year
from src.assemble.generic_build import build_paper, build_scheme
from src.planner.stem_length import stem_p90_limits
from src.subjects.plugins import (
    generator_labels as subject_generator_labels,
    plugin_for,
    require_plugin,
    topic_labels as subject_topic_labels,
)
from src.subjects.registry import (
    Subject,
    SubjectNotFound,
    default_subject_code,
    get_subject,
)
from src.theory.generate import (CostCapExceeded, GenerationCancelled,
                                 generate, report as theory_report)

PIPELINE_VERSION = 1
_MODEL = config.MOCKGEN_MODEL


def _config_payload(mode: str, seed: int, computed_marks: int | None,
                    public: bool, subject: str | None = None) -> dict:
    payload = {
        "version": PIPELINE_VERSION,
        "mode": mode,
        "seed": seed,
        "computed_marks": computed_marks if mode == "practice" else None,
        "model": _MODEL,
        "near_copy_threshold": config.THEORY_NEAR_COPY_THRESHOLD,
        "stem_overlap_threshold": config.THEORY_STEM_OVERLAP_THRESHOLD,
        "scenario_rate": config.THEORY_SCENARIO_RATE,
        "stem_p90_limits": stem_p90_limits(),
        "public_build": bool(public),
    }
    if subject is not None:
        payload["subject"] = subject
    return payload


def _hash(payload: dict) -> str:
    blob = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:20]


def _config_hash(mode: str, seed: int, computed_marks: int | None,
                 public: bool, subject: str | None = None) -> str:
    code = str(subject or default_subject_code()).upper()
    return _hash(_config_payload(mode, seed, computed_marks, public, code))


def cache_path(mode: str, seed: int, computed_marks: int | None,
               public: bool | None = None,
               subject: str | None = None) -> Path:
    """Per-subject cache folder keyed by the generation configuration."""
    code = str(subject or default_subject_code()).upper()
    is_public = config.PUBLIC_BUILD if public is None else bool(public)
    key = _config_hash(mode, seed, computed_marks, is_public, code)
    return config.WEB_CACHE_DIR / code / key


def _cache_meta(path: Path) -> dict | None:
    meta = path / "meta.json"
    if not meta.exists():
        return None
    try:
        data = json.loads(meta.read_text(encoding="utf-8"))
    except Exception:
        return None
    # Require at least a paper or scheme docx to consider it usable.
    files = data.get("files", {})
    if not any(str(v) and Path(v).exists() for v in files.values()):
        return None
    return data


def _cache_save(path: Path, job: "Job") -> None:
    path.mkdir(parents=True, exist_ok=True)
    files: dict[str, str] = {}
    mapping = {
        "paper_docx": "paper.docx",
        "paper_pdf": "paper.pdf",
        "scheme_docx": "scheme.docx",
        "scheme_pdf": "scheme.pdf",
    }
    for key, name in mapping.items():
        src = job.files.get(key)
        if src and Path(src).exists():
            dst = path / name
            if Path(src).resolve() != dst.resolve():
                shutil.copy2(src, dst)
            files[key] = str(dst)
    report = path / "report.md"
    if job.files.get("report_md"):
        shutil.copy2(job.files["report_md"], report)
    meta = {
        "subject": job.subject,
        "seed": job.seed,
        "mode": job.mode,
        "computed_marks": job.computed_marks,
        "model": job.model,
        "cost_usd": job.cost_usd,
        "accepted": job.accepted,
        "placeholders": job.placeholders,
        "total_slots": job.total_slots,
        "total_marks": job.summary.get("total_marks"),
        "has_practice_mode": job.summary.get("has_practice_mode",
                                             job.has_practice_mode),
        "has_placeholders": job.summary.get("has_placeholders",
                                            job.has_placeholders),
        "created": time.time(),
        "year": utc_year(job.finished or job.created),
        "topic_marks": job.summary.get("topic_marks", {}),
        "files": files,
        "summary": job.summary,
        "progress": job.progress,
    }
    (path / "meta.json").write_text(json.dumps(meta, indent=2),
                                    encoding="utf-8")


def _plan_for_subject(subject: Subject, mode: str, style: str,
                      computed_marks: int | None, seed: int):
    plugin = require_plugin(subject, "plan")
    return plugin(mode, style, computed_marks, seed)


def _plan_markdown(subject: Subject, summary: dict) -> str:
    plugin = plugin_for(subject, "plan_markdown")
    if plugin is not None:
        return str(plugin(summary))
    return json.dumps(summary, indent=2)


@dataclass
class Job:
    id: str
    mode: str
    seed: int
    computed_marks: int | None
    subject: str = field(default_factory=default_subject_code)
    model: str = _MODEL
    status: str = "queued"
    message: str = "Queued"
    progress: list[dict] = field(default_factory=list)
    cost_usd: float = 0.0
    accepted: int = 0
    placeholders: int = 0
    total_slots: int = 0
    has_practice_mode: bool = True
    has_placeholders: bool = True
    files: dict[str, str] = field(default_factory=dict)
    summary: dict = field(default_factory=dict)
    error: str = ""
    cached: bool = False
    created: float = field(default_factory=time.time)
    finished: float | None = None
    year: int | None = None
    cancel_event: threading.Event = field(default_factory=threading.Event)

    @property
    def running(self) -> bool:
        return self.status in {"queued", "running"}

    def display_year(self) -> int:
        return int(self.year or utc_year(self.finished or self.created))

    def download_names(self) -> dict[str, str]:
        marks = self.computed_marks if self.mode == "practice" else None
        names = {}
        for key, scheme, ext in (
                ("paper_docx", False, "docx"),
                ("paper_pdf", False, "pdf"),
                ("scheme_docx", True, "docx"),
                ("scheme_pdf", True, "pdf")):
            names[key] = download_filename(
                self.subject, self.seed, self.display_year(), ext,
                scheme=scheme, practice_marks=marks)
        return names

    def public(self) -> dict:
        """Render slots from the actual progress stream.

        The planner decides the question/part layout (A1a, Q1a, ...).  The UI
        must not assume a subject's paper structure, so rows are built from the
        events the subject emitted.
        """
        latest_by_question: dict[str, dict] = {}
        question_order: list[str] = []
        for event in self.progress:
            question = str(event.get("question", "") or "")
            if not question:
                continue
            if question not in latest_by_question:
                question_order.append(question)
            latest_by_question[question] = event

        fallback = "ready" if self.status == "done" else "waiting"
        questions = []
        rows = []
        for name in question_order:
            events = [e for e in self.progress
                      if str(e.get("question", "")) == name]
            cells_by_slot: dict[str, dict] = {}
            for event in events:
                slot = str(event.get("slot", "") or name)
                label = slot[len(name):] if slot.startswith(name) else slot
                cells_by_slot[slot] = {
                    "slot": slot,
                    "label": label or slot,
                    "status": event.get("status", fallback),
                    "message": event.get("message", ""),
                }
            latest = latest_by_question[name]
            questions.append({
                "name": name,
                "status": latest.get("status", fallback),
                "slot": latest.get("slot", ""),
                "message": latest.get("message", ""),
            })
            rows.append({"name": name,
                         "cells": list(cells_by_slot.values())})

        unique_slots = {str(e.get("slot", "")) for e in self.progress
                        if e.get("slot")}
        total = int(self.total_slots or len(unique_slots)
                    or self.accepted + self.placeholders or 0)
        decided = min(total, self.accepted + self.placeholders) if total else 0
        progress_percent = (round(100 * decided / total) if total else 0)
        last_accepted = ""
        for event in self.progress:
            if event.get("status") == "accepted":
                last_accepted = str(event.get("slot", ""))
        filled = int(round(20 * decided / total)) if total else 0
        elapsed = max(0.0, (self.finished or time.time()) - self.created)
        attempts = max((int(e.get("calls", 0)) for e in self.progress),
                       default=0)
        return {
            "id": self.id, "subject": self.subject, "mode": self.mode,
            "seed": self.seed, "computed_marks": self.computed_marks,
            "model": self.model, "year": self.display_year(),
            "status": self.status, "message": self.message,
            "progress": self.progress, "questions": questions,
            "rows": rows, "cost_usd": round(self.cost_usd, 6),
            "accepted": self.accepted, "placeholders": self.placeholders,
            "total_slots": total,
            "attempts": attempts,
            "decided": decided,
            "progress_percent": progress_percent,
            "progress_bar": "=" * filled + "." * (20 - filled),
            "last_accepted": last_accepted,
            "files": self.files, "summary": self.summary,
            "downloads": self.download_names(),
            "error": self.error, "cached": self.cached,
            "pdf_available": bool(self.files.get("paper_pdf")),
            "running": self.running,
            "elapsed": int(elapsed),
        }


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._pool = ThreadPoolExecutor(max_workers=2,
                                        thread_name_prefix="mockgen")

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def cancel(self, job_id: str) -> bool:
        job = self.get(job_id)
        if job is None:
            return False
        job.cancel_event.set()
        if job.status == "queued":
            job.status = "cancelled"
            job.message = "Cancelled before start"
        return True

    def create(self, mode: str, seed: int | None = None,
               computed_marks: int | None = None,
               subject: str | None = None) -> Job:
        code = str(subject or default_subject_code()).strip().upper()
        try:
            subject_obj = get_subject(code)
        except SubjectNotFound:
            raise ValueError(f"unknown subject: {subject}") from None
        if not subject_obj.available:
            raise ValueError(f"subject {code} is coming soon")
        generation = str(subject_obj.capabilities.get("generation") or "")
        if not generation:
            raise ValueError(f"subject {code} has no generation capability")
        deterministic = subject_obj.deterministic
        if deterministic:
            if mode != "realistic":
                raise ValueError(
                    f"{code} uses deterministic realistic papers; practice "
                    "mode is not available")
        elif mode not in {"realistic", "practice"}:
            raise ValueError("mode must be realistic or practice")
        if mode == "practice" and not subject_obj.has_practice_mode:
            raise ValueError(f"{code} does not support practice mode")
        if seed is None:
            seed = random.SystemRandom().randint(1, 10_000)
        if int(seed) < 1:
            raise ValueError("seed must be a positive integer")
        seed = int(seed)
        if mode == "practice" and not deterministic:
            computed_marks = 22 if computed_marks is None else int(computed_marks)
            if not 0 <= computed_marks <= 80:
                raise ValueError("computed marks must be between 0 and 80")
        else:
            computed_marks = None
        cached = cache_path(mode, seed, computed_marks, subject=code)
        meta = _cache_meta(cached)
        job = Job(id=uuid.uuid4().hex[:12], mode=mode, seed=seed,
                  computed_marks=computed_marks, subject=code,
                  has_practice_mode=subject_obj.has_practice_mode,
                  has_placeholders=subject_obj.has_placeholders)
        if meta:
            job.status = "done"
            job.cached = True
            job.message = "Loaded from cache (no LLM call)"
            job.files = dict(meta.get("files", {}))
            job.summary = meta.get("summary", {})
            job.summary["cost_usd"] = float(meta.get("cost_usd", 0.0))
            job.progress = list(meta.get("progress", []))
            job.cost_usd = 0.0  # this run made no LLM call
            job.accepted = int(meta.get("accepted", 0))
            job.placeholders = int(meta.get("placeholders", 0))
            job.total_slots = int(meta.get("total_slots", 0) or 0)
            job.year = int(meta.get("year") or utc_year(
                meta.get("created") or time.time()))
            job.finished = time.time()
            with self._lock:
                self._jobs[job.id] = job
            return job
        if deterministic:
            with self._lock:
                self._jobs[job.id] = job
            self._pool.submit(self._run_deterministic, job, cached)
            return job
        if not config.llm_key_ready():
            job.status = "error"
            job.error = ("No LLM API key is set for the active model. "
                         "Use the Library tab for cached papers.")
            job.message = job.error
            with self._lock:
                self._jobs[job.id] = job
            return job
        with self._lock:
            self._jobs[job.id] = job
        self._pool.submit(self._run, job, cached)
        return job

    def _run(self, job: Job, cache_dir: Path) -> None:
        job.status = "running"
        job.message = "Planning"
        run_dir = config.WEB_RUNS_DIR / job.subject / job.id
        run_dir.mkdir(parents=True, exist_ok=True)
        plan_path = run_dir / "planner.json"
        theory_path = run_dir / "theory.json"
        try:
            subject_obj = get_subject(job.subject)
            style = str(subject_obj.capabilities.get("planner_style",
                                                     "modern"))
            _, summary = _plan_for_subject(
                subject_obj, job.mode, style, job.computed_marks, job.seed)
            plan_path.write_text(json.dumps(summary, indent=2),
                                 encoding="utf-8")
            (run_dir / "planner.md").write_text(
                _plan_markdown(subject_obj, summary), encoding="utf-8")
            job.computed_marks = summary.get("computed_marks")
            job.total_slots = int(
                summary.get("total_slots")
                or len(summary.get("slots") or []) or 0)
            topic_marks = dict(summary.get("assigned_topic_marks") or {})

            def progress(event: dict) -> None:
                job.progress.append({
                    "question": event.get("question", ""),
                    "slot": event.get("slot", ""),
                    "status": event.get("status", ""),
                    "message": event.get("message", ""),
                    "cost_usd": round(float(event.get("cost_usd", 0)), 6),
                    "calls": int(event.get("calls", 0)),
                    "accepted": int(event.get("accepted", 0)),
                    "placeholders": int(event.get("placeholders", 0)),
                })
                job.cost_usd = float(event.get("cost_usd", job.cost_usd))
                job.accepted = int(event.get("accepted", job.accepted))
                job.placeholders = int(event.get("placeholders",
                                                 job.placeholders))
                job.message = f"{event.get('question', '')} " \
                              f"{event.get('slot', '')} " \
                              f"{event.get('status', '')}"

            payload = generate(
                plan_path, model=config.MOCKGEN_MODEL,
                cost_cap_usd=config.WEB_COST_CAP_USD,
                progress_cb=progress,
                should_stop=job.cancel_event.is_set)
            theory_path.write_text(json.dumps(payload, indent=2),
                                   encoding="utf-8")
            (run_dir / "theory.md").write_text(theory_report(payload),
                                               encoding="utf-8")
            job.cost_usd = float(payload["usage"]["cost_usd"])
            job.accepted = len(payload.get("accepted", []))
            job.placeholders = len(payload.get("placeholders", []))

            job.message = "Building paper and scheme"
            paper = build_paper(
                plan_path, theory_path, run_dir / "paper.docx",
                run_dir / "paper.pdf", public=config.PUBLIC_BUILD)
            scheme = build_scheme(
                run_dir / "paper.docx", plan_path, theory_path,
                run_dir / "scheme.docx", run_dir / "scheme.pdf",
                public=config.PUBLIC_BUILD)
            job.files = {
                "paper_docx": paper.get("docx", ""),
                "paper_pdf": paper.get("pdf", ""),
                "scheme_docx": scheme.get("docx", ""),
                "scheme_pdf": scheme.get("pdf", ""),
                "report_md": str(run_dir / "theory.md"),
            }
            job.summary = {
                "subject": job.subject,
                "seed": job.seed,
                "mode": job.mode,
                "computed_marks": job.computed_marks,
                "accepted": job.accepted,
                "placeholders": job.placeholders,
                "total_slots": job.total_slots,
                "has_practice_mode": job.has_practice_mode,
                "has_placeholders": job.has_placeholders,
                "model": job.model,
                "cost_usd": job.cost_usd,
                "cached": False,
                "topic_marks": topic_marks,
                "pdf_available": bool(paper.get("pdf")),
                "pdf_note": ("PDF export unavailable - use the DOCX links."
                             if not paper.get("pdf") else ""),
            }
            job.status = "done"
            job.message = "Complete"
            job.finished = time.time()
            job.year = utc_year(job.finished)
            _cache_save(cache_dir, job)
        except GenerationCancelled:
            job.status = "cancelled"
            job.message = "Cancelled"
            job.finished = time.time()
        except CostCapExceeded as e:
            job.status = "cost_capped"
            job.cost_usd = e.cost_usd
            job.message = (f"Stopped at cost cap: ${e.cost_usd:.4f} "
                           f"(cap ${e.cap_usd:.4f})")
            job.error = job.message
            job.finished = time.time()
        except Exception as e:
            job.status = "error"
            job.message = f"Error: {e}"
            job.error = f"{e}\n{traceback.format_exc()[-1200:]}"
            job.finished = time.time()

    def _run_deterministic(self, job: Job, cache_dir: Path) -> None:
        job.status = "running"
        run_dir = config.WEB_RUNS_DIR / job.subject / job.id
        run_dir.mkdir(parents=True, exist_ok=True)
        try:
            subject_obj = get_subject(job.subject)
            plugin = require_plugin(subject_obj, "prebuild")
            job.message = f"Building deterministic {job.subject} paper"
            result = plugin(job.seed, out_dir=run_dir, force=True)
            meta_path = Path(result.get("path", run_dir)) / "meta.json"
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            job.files = dict(meta.get("files", {}))
            job.summary = dict(meta.get("summary", {}))
            job.progress = list(meta.get("progress", []))
            job.accepted = int(meta.get("accepted", 0))
            job.placeholders = int(meta.get("placeholders", 0))
            job.total_slots = int(meta.get("total_slots", 0)
                                  or job.accepted + job.placeholders)
            job.has_practice_mode = bool(meta.get(
                "has_practice_mode", job.has_practice_mode))
            job.has_placeholders = bool(meta.get(
                "has_placeholders", job.has_placeholders))
            job.cost_usd = 0.0
            job.model = str(meta.get("model") or f"{job.subject}-deterministic")
            job.year = int(meta.get("year") or utc_year())
            job.status = "done"
            job.message = "Complete"
            job.finished = time.time()
            _cache_save(cache_dir, job)
        except Exception as e:
            job.status = "error"
            job.message = f"Error: {e}"
            job.error = f"{e}\n{traceback.format_exc()[-1200:]}"
            job.finished = time.time()


def topic_mix_text(topic_marks: dict,
                   subject: str | Subject | None = None) -> str:
    labels = {}
    if isinstance(subject, Subject):
        labels = subject_topic_labels(subject)
    elif subject:
        try:
            labels = subject_topic_labels(get_subject(subject))
        except SubjectNotFound:
            labels = {}
    parts = sorted(((str(k), int(v)) for k, v in (topic_marks or {}).items()
                    if int(v) > 0), key=lambda kv: (-kv[1], kv[0]))
    return " ".join(f"{labels.get(name, name[:3].upper())} {marks}"
                    for name, marks in parts)


def topic_legend(subject: str | Subject | None = None) -> str:
    """Short abbreviation legend for the Library table, from the registry."""
    record = subject if isinstance(subject, Subject) else None
    if record is None and subject:
        try:
            record = get_subject(str(subject))
        except SubjectNotFound:
            record = None
    labels = subject_topic_labels(record) if record is not None else {}
    prefix = "Topic abbreviations: "
    if labels:
        text = ", ".join(f"{short} {name}"
                         for name, short in sorted(labels.items()))
    else:
        text = "Topic abbreviations are shown in the Topic mix column."
    return (prefix + text + ". Numbers are marks. Click a column title to "
            "sort ascending/descending.")


def _planner_data(seed: int, subject: Subject | None = None) -> dict:
    if subject is None:
        return {}
    plugin = plugin_for(subject, "library_metadata")
    if plugin is None:
        return {}
    try:
        return dict(plugin(seed) or {})
    except Exception:
        return {}


def _library_seeds(subject: str | Subject | None = None) -> list[int]:
    """Return Library seeds from the subject plugin, else its cache folder."""
    record = subject if isinstance(subject, Subject) else None
    if record is None and subject:
        try:
            record = get_subject(str(subject))
        except SubjectNotFound:
            record = None
    if record is not None:
        plugin = plugin_for(record, "library_seeds")
        if plugin is not None:
            try:
                return sorted(int(seed) for seed in plugin() if int(seed) > 0)
            except Exception:
                return []
        code = record.code
    else:
        code = str(subject or default_subject_code()).upper()
    seeds: set[int] = set()
    cache_dir = config.WEB_CACHE_DIR / code
    if cache_dir.exists():
        for meta_path in cache_dir.glob("*/meta.json"):
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                seeds.add(int(meta.get("seed")))
            except Exception:
                continue
    return sorted(seed for seed in seeds if seed > 0)


def _cache_entry(seed: int, subject: str) -> tuple[Path, dict] | None:
    """Find a cached paper by seed, realistic first, then any mode."""
    code = str(subject).upper()
    preferred = cache_path("realistic", seed, None, subject=code)
    meta = _cache_meta(preferred)
    if meta:
        return preferred, meta
    cache_dir = config.WEB_CACHE_DIR / code
    if not cache_dir.exists():
        return None
    candidates: list[tuple[str, Path, dict]] = []
    for meta_path in cache_dir.glob("*/meta.json"):
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if int(data.get("seed", -1)) != int(seed):
            continue
        if not _cache_meta(meta_path.parent):
            continue
        candidates.append((str(data.get("mode") or ""), meta_path.parent,
                           data))
    if not candidates:
        return None
    candidates.sort(key=lambda row: (row[0] != "realistic", row[1].name))
    return candidates[0][1], candidates[0][2]


def library_item(seed: int,
                 subject: str | Subject | None = None) -> dict | None:
    if config.PUBLIC_BUILD:
        return None
    record = subject if isinstance(subject, Subject) else None
    if record is None:
        try:
            record = get_subject(subject or default_subject_code())
        except SubjectNotFound:
            record = None
    code = record.code if record is not None else str(
        subject or default_subject_code()).upper()
    entry = _cache_entry(seed, code)
    if entry is None:
        return None
    meta = entry[1]
    mode = str(meta.get("mode") or "realistic")
    plan = _planner_data(seed, record)
    computed = meta.get("computed_marks")
    if computed is None:
        computed = plan.get("computed_marks")
    has_practice = bool(meta.get(
        "has_practice_mode",
        getattr(record, "has_practice_mode", True)))
    has_placeholders = bool(meta.get(
        "has_placeholders",
        getattr(record, "has_placeholders", True)))
    total_marks = meta.get("total_marks")
    if total_marks is None:
        total_marks = plan.get("total_marks")
    computed_display = 0 if computed is None else int(computed)
    marks_value = computed_display
    if not has_practice and total_marks is not None:
        marks_value = int(total_marks)
    year = int(meta.get("year") or utc_year(
        meta.get("created") or time.time()))
    marks = computed if mode == "practice" else None
    files = dict(meta.get("files", {}))
    names = {}
    for key, scheme, ext in (
            ("paper_docx", False, "docx"), ("paper_pdf", False, "pdf"),
            ("scheme_docx", True, "docx"), ("scheme_pdf", True, "pdf")):
        names[key] = download_filename(code, seed, year, ext, scheme=scheme,
                                       practice_marks=marks)
    topic_marks = dict(meta.get("topic_marks")
                       or plan.get("assigned_topic_marks") or {})
    return {
        "subject": code,
        "seed": seed,
        "mode": mode,
        "computed_marks": computed,
        "computed_display": computed_display,
        "total_marks": int(total_marks) if total_marks is not None else None,
        "marks_value": marks_value,
        "marks_label": ("Computed marks" if has_practice else "Total marks"),
        "has_practice_mode": has_practice,
        "has_placeholders": has_placeholders,
        "year": year,
        "accepted": meta.get("accepted", 0),
        "placeholders": meta.get("placeholders", 0),
        "cost_usd": meta.get("cost_usd", 0),
        "model": meta.get("model", ""),
        "topic_marks": topic_marks,
        "topic_keys": "|".join(str(k) for k in topic_marks),
        "topic_mix": topic_mix_text(topic_marks, record or code),
        "files": files,
        "downloads": names,
    }


def library_count(subject: str | Subject | None = None) -> int:
    """Count cached papers even when PUBLIC_BUILD disables browsing."""
    record = subject if isinstance(subject, Subject) else None
    code = record.code if record is not None else str(
        subject or default_subject_code()).upper()
    count = 0
    for seed in _library_seeds(record or code):
        if _cache_meta(cache_path("realistic", seed, None, public=False,
                                  subject=code)):
            count += 1
    return count


def library_items(subject: str | Subject | None = None) -> list[dict]:
    if config.PUBLIC_BUILD:
        return []
    record = subject if isinstance(subject, Subject) else None
    if record is None:
        try:
            record = get_subject(subject or default_subject_code())
        except SubjectNotFound:
            return []
    if not record.available:
        return []
    items = [item for seed in _library_seeds(record)
             if (item := library_item(seed, record)) is not None]
    return items


def filter_library(items: list[dict], q: str = "", computed: str = "any",
                   topic: str = "any", placeholders: str = "any") -> list[dict]:
    query = (q or "").strip().lower()
    out = []
    for item in items:
        if query:
            haystack = " ".join([
                str(item.get("seed", "")), item.get("mode", ""),
                item.get("year", ""), item.get("topic_mix", ""),
                " ".join((item.get("topic_marks") or {}).keys()),
            ]).lower()
            if query not in haystack:
                continue
        if computed not in ("", "any"):
            try:
                value = item.get("marks_value",
                                 item.get("computed_display", 0))
                if int(value) != int(computed):
                    continue
            except (TypeError, ValueError):
                continue
        if topic not in ("", "any"):
            if not int((item.get("topic_marks") or {}).get(topic, 0)):
                continue
        if item.get("has_placeholders", True):
            if placeholders == "0" and int(item.get("placeholders", 0)) != 0:
                continue
            if placeholders == "1+" and int(item.get("placeholders", 0)) < 1:
                continue
        out.append(item)
    return out


def library_file(seed: int, kind: str,
                 subject: str | None = None) -> Path | None:
    if config.PUBLIC_BUILD:
        return None
    if kind not in {"paper_pdf", "paper_docx", "scheme_pdf", "scheme_docx"}:
        return None
    entry = _cache_entry(seed, str(subject or default_subject_code()).upper())
    if entry is None:
        return None
    path = Path(entry[1].get("files", {}).get(kind, ""))
    return path if path.exists() else None


manager = JobManager()
