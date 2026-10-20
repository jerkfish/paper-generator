"""In-process background jobs, cache and library for the local web UI."""
from __future__ import annotations

import hashlib
import json
import random
import shutil
import threading
import time
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from src import config
from src.assemble.generic_build import build_paper, build_scheme
from src.planner.planner import build_plan, to_markdown
from src.planner.stem_length import stem_p90_limits
from src.theory.generate import (CostCapExceeded, GenerationCancelled,
                                 generate, report as theory_report)

PIPELINE_VERSION = 1
_MODEL = config.MOCKGEN_MODEL


def _config_hash(mode: str, seed: int, computed_marks: int | None,
                 public: bool) -> str:
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
    blob = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:20]


def cache_path(mode: str, seed: int, computed_marks: int | None,
               public: bool | None = None) -> Path:
    key = _config_hash(mode, seed, computed_marks,
                       config.PUBLIC_BUILD if public is None else public)
    return config.WEB_CACHE_DIR / key


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
        "seed": job.seed,
        "mode": job.mode,
        "computed_marks": job.computed_marks,
        "model": job.model,
        "cost_usd": job.cost_usd,
        "accepted": job.accepted,
        "placeholders": job.placeholders,
        "created": time.time(),
        "files": files,
        "summary": job.summary,
        "progress": job.progress,
    }
    (path / "meta.json").write_text(json.dumps(meta, indent=2),
                                    encoding="utf-8")


@dataclass
class Job:
    id: str
    mode: str
    seed: int
    computed_marks: int | None
    model: str = _MODEL
    status: str = "queued"
    message: str = "Queued"
    progress: list[dict] = field(default_factory=list)
    cost_usd: float = 0.0
    accepted: int = 0
    placeholders: int = 0
    files: dict[str, str] = field(default_factory=dict)
    summary: dict = field(default_factory=dict)
    error: str = ""
    cached: bool = False
    created: float = field(default_factory=time.time)
    finished: float | None = None
    cancel_event: threading.Event = field(default_factory=threading.Event)

    @property
    def running(self) -> bool:
        return self.status in {"queued", "running"}

    def public(self) -> dict:
        order = ([f"A{i}" for i in range(1, 11)] + ["B1", "B2"])
        latest: dict[str, dict] = {}
        for event in self.progress:
            latest[event.get("question", "")] = event
        questions = []
        for name in order:
            event = latest.get(name)
            fallback = ("ready" if self.status == "done" else "waiting")
            questions.append({
                "name": name,
                "status": event.get("status", fallback) if event else fallback,
                "slot": event.get("slot", "") if event else "",
                "message": event.get("message", "") if event else "",
            })
        return {
            "id": self.id, "mode": self.mode, "seed": self.seed,
            "computed_marks": self.computed_marks, "model": self.model,
            "status": self.status, "message": self.message,
            "progress": self.progress, "questions": questions,
            "cost_usd": round(self.cost_usd, 6),
            "accepted": self.accepted, "placeholders": self.placeholders,
            "files": self.files, "summary": self.summary,
            "error": self.error, "cached": self.cached,
            "pdf_available": bool(self.files.get("paper_pdf")),
            "running": self.running,
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
               computed_marks: int | None = None) -> Job:
        if mode not in {"realistic", "practice"}:
            raise ValueError("mode must be realistic or practice")
        if seed is None:
            seed = random.SystemRandom().randint(1, 10_000)
        if int(seed) < 1:
            raise ValueError("seed must be a positive integer")
        seed = int(seed)
        if mode == "practice":
            computed_marks = 22 if computed_marks is None else int(computed_marks)
            if not 0 <= computed_marks <= 80:
                raise ValueError("computed marks must be between 0 and 80")
        else:
            computed_marks = None
        cached = cache_path(mode, seed, computed_marks)
        meta = _cache_meta(cached)
        job = Job(id=uuid.uuid4().hex[:12], mode=mode, seed=seed,
                  computed_marks=computed_marks)
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
            job.finished = time.time()
            with self._lock:
                self._jobs[job.id] = job
            return job
        if not config.DEEPSEEK_API_KEY:
            job.status = "error"
            job.error = ("DEEPSEEK_API_KEY is not set. Use the Library tab "
                         "for cached papers.")
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
        run_dir = config.WEB_RUNS_DIR / job.id
        run_dir.mkdir(parents=True, exist_ok=True)
        plan_path = run_dir / "planner.json"
        theory_path = run_dir / "theory.json"
        try:
            _, summary = build_plan(job.mode, "modern", job.computed_marks,
                                    job.seed)
            plan_path.write_text(json.dumps(summary, indent=2),
                                 encoding="utf-8")
            (run_dir / "planner.md").write_text(to_markdown(summary),
                                                encoding="utf-8")
            job.computed_marks = summary.get("computed_marks")

            def progress(event: dict) -> None:
                job.progress.append({
                    "question": event.get("question", ""),
                    "slot": event.get("slot", ""),
                    "status": event.get("status", ""),
                    "message": event.get("message", ""),
                    "cost_usd": round(float(event.get("cost_usd", 0)), 6),
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
                "seed": job.seed,
                "mode": job.mode,
                "computed_marks": job.computed_marks,
                "accepted": job.accepted,
                "placeholders": job.placeholders,
                "model": job.model,
                "cost_usd": job.cost_usd,
                "cached": False,
                "pdf_available": bool(paper.get("pdf")),
                "pdf_note": ("PDF export unavailable - use the DOCX links."
                             if not paper.get("pdf") else ""),
            }
            _cache_save(cache_dir, job)
            job.status = "done"
            job.message = "Complete"
            job.finished = time.time()
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


def library_items() -> list[dict]:
    if config.PUBLIC_BUILD:
        return []
    items = []
    for p in sorted(config.OUTPUTS_DIR.glob("eval_final_deepseek/"
                                            "seed_*_theory.json")):
        try:
            seed = int(p.stem.split("_")[1])
        except Exception:
            continue
        meta = _cache_meta(cache_path("realistic", seed, None))
        if not meta:
            continue
        items.append({
            "seed": seed,
            "accepted": meta.get("accepted", 0),
            "placeholders": meta.get("placeholders", 0),
            "cost_usd": meta.get("cost_usd", 0),
            "model": meta.get("model", ""),
            "files": meta.get("files", {}),
        })
    return items


def library_file(seed: int, kind: str) -> Path | None:
    if config.PUBLIC_BUILD:
        return None
    if kind not in {"paper_pdf", "paper_docx", "scheme_pdf", "scheme_docx"}:
        return None
    meta = _cache_meta(cache_path("realistic", seed, None))
    if not meta:
        return None
    path = Path(meta.get("files", {}).get(kind, ""))
    return path if path.exists() else None


manager = JobManager()
