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
from src.app.filenames import download_filename, utc_year
from src.assemble.generic_build import build_paper, build_scheme
from src.planner.planner import build_plan, to_markdown
from src.planner.stem_length import stem_p90_limits
from src.subjects.registry import SubjectNotFound, get_subject
from src.theory.generate import (CostCapExceeded, GenerationCancelled,
                                 generate, report as theory_report)

PIPELINE_VERSION = 1
_MODEL = config.MOCKGEN_MODEL
DEFAULT_SUBJECT = "CSC662"


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
                 public: bool, subject: str = DEFAULT_SUBJECT) -> str:
    return _hash(_config_payload(mode, seed, computed_marks, public,
                                 subject.upper()))


def _legacy_config_hash(mode: str, seed: int, computed_marks: int | None,
                        public: bool) -> str:
    """Pre-Phase-1 key (no subject); used only to find the old flat cache."""
    return _hash(_config_payload(mode, seed, computed_marks, public))


def cache_path(mode: str, seed: int, computed_marks: int | None,
               public: bool | None = None,
               subject: str = DEFAULT_SUBJECT) -> Path:
    """Per-subject cache folder.

    Existing CSC662 caches built before Phase 1 live in flat folders.  They
    remain readable until the migration script copies them into the subject
    folder; new builds always write the per-subject path.
    """
    code = str(subject).upper()
    is_public = config.PUBLIC_BUILD if public is None else bool(public)
    key = _config_hash(mode, seed, computed_marks, is_public, code)
    path = config.WEB_CACHE_DIR / code / key
    if code == DEFAULT_SUBJECT and not path.exists():
        legacy = config.WEB_CACHE_DIR / _legacy_config_hash(
            mode, seed, computed_marks, is_public)
        if legacy.exists():
            return legacy
    return path


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
        "created": time.time(),
        "year": utc_year(job.finished or job.created),
        "topic_marks": job.summary.get("topic_marks", {}),
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
    subject: str = DEFAULT_SUBJECT
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
        by_slot = {e.get("slot", ""): e for e in self.progress}
        rows = []
        for name in order:
            cells = {}
            for part in ("a", "b"):
                slot = f"{name}{part}"
                event = by_slot.get(slot)
                fallback = ("ready" if self.status == "done" else "waiting")
                cells[part] = {
                    "slot": slot,
                    "status": (event.get("status", fallback)
                               if event else fallback),
                    "message": event.get("message", "") if event else "",
                }
            rows.append({"name": name, "a": cells["a"], "b": cells["b"]})
        elapsed = max(0.0, (self.finished or time.time()) - self.created)
        attempts = max((int(e.get("calls", 0)) for e in self.progress),
                       default=0)
        total = 24
        if self.subject == "MAT133":
            names = [f"Q{i}" for i in range(1, 6)]
            by_slot = {e.get("slot", ""): e for e in self.progress}
            latest = {e.get("question", ""): e for e in self.progress}

            def _cell(question: str, part: str) -> dict:
                slot = f"{question}{part}"
                event = by_slot.get(slot)
                fallback = ("ready" if self.status == "done" else "waiting")
                return {
                    "slot": slot,
                    "status": (event.get("status", fallback)
                               if event else fallback),
                    "message": event.get("message", "") if event else "",
                }

            questions = [{
                "name": name,
                "status": (latest.get(name, {}).get("status")
                           or ("ready" if self.status == "done"
                               else "waiting")),
                "slot": "",
                "message": "",
            } for name in names]
            rows = [{
                "name": name,
                "a": _cell(name, "a"),
                "b": _cell(name, "b"),
            } for name in names]
            total = max(1, self.accepted or 15)
        decided = min(total, self.accepted + self.placeholders)
        last_accepted = ""
        for event in self.progress:
            if event.get("status") == "accepted":
                last_accepted = str(event.get("slot", ""))
        filled = int(round(20 * decided / total)) if total else 0
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
               subject: str = DEFAULT_SUBJECT) -> Job:
        code = str(subject).strip().upper()
        try:
            subject_obj = get_subject(code)
        except SubjectNotFound:
            raise ValueError(f"unknown subject: {subject}") from None
        if not subject_obj.available:
            raise ValueError(f"subject {code} is coming soon")
        deterministic = code == "MAT133"
        if code not in {DEFAULT_SUBJECT, "MAT133"}:
            raise ValueError(f"subject {code} has no computed generator plugin")
        if deterministic:
            if mode != "realistic":
                raise ValueError(
                    "MAT133 uses deterministic realistic papers; practice "
                    "mode is not available")
        elif mode not in {"realistic", "practice"}:
            raise ValueError("mode must be realistic or practice")
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
                  computed_marks=computed_marks, subject=code)
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
            job.year = int(meta.get("year") or utc_year(
                meta.get("created") or time.time()))
            job.finished = time.time()
            with self._lock:
                self._jobs[job.id] = job
            return job
        if deterministic:
            with self._lock:
                self._jobs[job.id] = job
            self._pool.submit(self._run_mat133, job, cached)
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
        run_dir = config.WEB_RUNS_DIR / job.subject / job.id
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

    def _run_mat133(self, job: Job, cache_dir: Path) -> None:
        from src.mat133.library import build_seed as build_mat133_seed

        job.status = "running"
        job.message = "Building deterministic MAT133 paper"
        run_dir = config.WEB_RUNS_DIR / job.subject / job.id
        run_dir.mkdir(parents=True, exist_ok=True)
        try:
            result = build_mat133_seed(job.seed, out_dir=run_dir, force=True)
            meta = json.loads((run_dir / "meta.json").read_text(
                encoding="utf-8"))
            job.files = dict(meta.get("files", {}))
            job.summary = dict(meta.get("summary", {}))
            job.progress = list(meta.get("progress", []))
            job.accepted = int(meta.get("accepted", 0))
            job.placeholders = int(meta.get("placeholders", 0))
            job.cost_usd = 0.0
            job.model = str(meta.get("model", "mat133-deterministic"))
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


TOPIC_SHORT = {
    "attacks/malware": "ATK",
    "authentication/biometrics": "AUT",
    "access control models": "ACC",
    "trusted computing/blockchain": "TRU",
    "software/OS security": "SWS",
    "network security": "NET",
    "risk/management (ethics)": "ETH",
    "classical ciphers": "CIP",
    "general cryptography": "CRY",
    "block ciphers": "BLK",
    "hashing/signatures": "HSH",
    "public-key": "PKI",
    "functions": "FUN",
    "inequalities": "INQ",
    "absolute_value": "ABS",
    "lines": "LIN",
    "circles": "CIR",
    "parabolas": "PAR",
    "complex_numbers": "CPX",
    "systems_of_equations": "SYS",
    "systems_of_inequalities": "SIQ",
    "polynomials": "POL",
    "exponential_logarithmic": "EXP",
    "trigonometry": "TRG",
    "circular_measure": "CME",
    "triangle_geometry": "TRI",
    "other": "OTH",
}


def topic_mix_text(topic_marks: dict) -> str:
    parts = sorted(((str(k), int(v)) for k, v in (topic_marks or {}).items()
                    if int(v) > 0), key=lambda kv: (-kv[1], kv[0]))
    return " ".join(f"{TOPIC_SHORT.get(name, name[:3].upper())} {marks}"
                    for name, marks in parts)


def topic_legend(subject: str = DEFAULT_SUBJECT) -> str:
    """Short abbreviation legend for the Library table."""
    code = str(subject).upper()
    if code == "MAT133":
        return ("Topic abbreviations: FUN functions, INQ inequalities, "
                "ABS absolute value, LIN lines, CIR circles, PAR parabolas, "
                "CPX complex numbers, SYS systems, SIQ inequalities systems, "
                "POL polynomials, EXP exponential/log, TRG trigonometry, "
                "CME circular measure, TRI triangle geometry. Numbers are "
                "marks. Click a column title to sort ascending/descending.")
    return ("Topic abbreviations: ATK attacks/malware, AUT authentication, "
            "ACC access control, TRU trusted computing, SWS software/OS, "
            "NET network, ETH ethics, CIP classical ciphers. Numbers are "
            "accepted marks. Click a column title to sort ascending/"
            "descending.")


def _planner_data(seed: int) -> dict:
    path = (config.OUTPUTS_DIR / "eval_final_deepseek" /
            f"seed_{seed:02d}_planner.json")
    if not path.exists():
        return {}
    try:
        return dict(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return {}


def _library_seeds(subject: str) -> list[int]:
    """CSC662's Library is the fixed 20-seed accepted set.

    Other available subjects discover seeds from their own cache folder.
    """
    code = subject.upper()
    if code == DEFAULT_SUBJECT:
        seeds: set[int] = set()
        for p in config.OUTPUTS_DIR.glob("eval_final_deepseek/"
                                         "seed_*_theory.json"):
            try:
                seeds.add(int(p.stem.split("_")[1]))
            except Exception:
                continue
        return sorted(s for s in seeds if s > 0)
    seeds = set()
    cache_dir = config.WEB_CACHE_DIR / code
    if cache_dir.exists():
        for meta_path in cache_dir.glob("*/meta.json"):
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                seeds.add(int(meta.get("seed")))
            except Exception:
                continue
    return sorted(s for s in seeds if s > 0)


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


def library_item(seed: int, subject: str = DEFAULT_SUBJECT) -> dict | None:
    if config.PUBLIC_BUILD:
        return None
    code = str(subject).upper()
    entry = _cache_entry(seed, code)
    if entry is None:
        return None
    meta = entry[1]
    mode = str(meta.get("mode") or "realistic")
    plan = _planner_data(seed) if code == DEFAULT_SUBJECT else {}
    computed = meta.get("computed_marks")
    if computed is None:
        computed = plan.get("computed_marks")
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
        "computed_display": 0 if computed is None else int(computed),
        "year": year,
        "accepted": meta.get("accepted", 0),
        "placeholders": meta.get("placeholders", 0),
        "cost_usd": meta.get("cost_usd", 0),
        "model": meta.get("model", ""),
        "topic_marks": topic_marks,
        "topic_keys": "|".join(str(k) for k in topic_marks),
        "topic_mix": topic_mix_text(topic_marks),
        "files": files,
        "downloads": names,
    }


def library_count(subject: str = DEFAULT_SUBJECT) -> int:
    """Count cached papers even when PUBLIC_BUILD disables browsing."""
    code = str(subject).upper()
    count = 0
    for seed in _library_seeds(code):
        if _cache_meta(cache_path("realistic", seed, None, public=False,
                                  subject=code)):
            count += 1
    return count


def library_items(subject: str = DEFAULT_SUBJECT) -> list[dict]:
    if config.PUBLIC_BUILD:
        return []
    code = str(subject).upper()
    try:
        if not get_subject(code).available:
            return []
    except SubjectNotFound:
        return []
    items = [item for seed in _library_seeds(code)
             if (item := library_item(seed, code)) is not None]
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
                if int(item.get("computed_display", 0)) != int(computed):
                    continue
            except ValueError:
                continue
        if topic not in ("", "any"):
            if not int((item.get("topic_marks") or {}).get(topic, 0)):
                continue
        if placeholders == "0" and int(item.get("placeholders", 0)) != 0:
            continue
        if placeholders == "1+" and int(item.get("placeholders", 0)) < 1:
            continue
        out.append(item)
    return out


def library_file(seed: int, kind: str,
                 subject: str = DEFAULT_SUBJECT) -> Path | None:
    if config.PUBLIC_BUILD:
        return None
    if kind not in {"paper_pdf", "paper_docx", "scheme_pdf", "scheme_docx"}:
        return None
    entry = _cache_entry(seed, str(subject).upper())
    if entry is None:
        return None
    path = Path(entry[1].get("files", {}).get(kind, ""))
    return path if path.exists() else None


manager = JobManager()
