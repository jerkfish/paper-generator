"""Local FastAPI + HTMX UI for the mock paper generator."""
from __future__ import annotations

import html
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src import config
from src.app.filenames import content_disposition
from src.app.jobs import (filter_library, library_count, library_file,
                          library_item, library_items, manager)
from src.app.safety import (ForbiddenPathError, assert_no_secret_leaks,
                            ensure_servable)
from src.planner.planner import TYPE_LABEL
from src.subjects.registry import (Subject, SubjectNotFound, get_subject,
                                   load_subjects)

APP_DIR = Path(__file__).resolve().parent
app = FastAPI(title=config.SITE_NAME)


@app.on_event("startup")
def _phase0_startup_check() -> None:
    assert_no_secret_leaks()


app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")),
          name="static")
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))


def _context(request: Request, **extra) -> dict:
    context = {
        "request": request,
        "site_name": config.SITE_NAME,
        "subjects": list(load_subjects().values()),
        "public": config.PUBLIC_BUILD,
        "library_disabled": config.PUBLIC_BUILD,
        "generate_disabled": False,
        "static_bundle": False,
        "asset_base": "/static",
        "contact_email": config.CONTACT_EMAIL,
        "repo_url": config.REPO_URL,
        "cost_cap": config.WEB_COST_CAP_USD,
        "model": config.MOCKGEN_MODEL,
        "has_key": bool(config.DEEPSEEK_API_KEY),
    }
    context.update(extra)
    return context


def _subject_or_404(code: str) -> Subject:
    try:
        return get_subject(code)
    except SubjectNotFound:
        raise HTTPException(status_code=404, detail="subject not found") from None


def _require_subject_page(code: str) -> Subject:
    subject = _subject_or_404(code)
    if not subject.available:
        raise HTTPException(status_code=404, detail="subject is coming soon")
    return subject


def _media_type(kind: str) -> str:
    return ("application/pdf" if kind.endswith("pdf")
            else "application/vnd.openxmlformats-officedocument."
                 "wordprocessingml.document")


def _download(path: Path, kind: str, name: str) -> FileResponse:
    try:
        path = ensure_servable(path)
    except ForbiddenPathError as e:
        raise HTTPException(status_code=403, detail=str(e)) from None
    return FileResponse(str(path), media_type=_media_type(kind),
                        headers={"Content-Disposition": content_disposition(name)})


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    subjects = list(load_subjects().values())
    counts = {s.code: library_count(s.code) for s in subjects
              if s.available}
    return templates.TemplateResponse(
        request=request, name="index.html",
        context=_context(request, subjects=subjects, counts=counts))


@app.get("/gallery", response_class=HTMLResponse)
def gallery(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request, name="gallery.html",
        context=_context(request, items=[]))


@app.get("/paused", response_class=HTMLResponse)
def paused(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request, name="paused.html", context=_context(request))


@app.get("/{code}", response_class=HTMLResponse)
def subject_page(request: Request, code: str) -> HTMLResponse:
    subject = _subject_or_404(code)
    paper_count = library_count(subject.code) if subject.available else 0
    registry = ""
    if subject.registry_path is not None:
        try:
            registry = subject.registry_path.relative_to(
                config.PROJECT_ROOT).as_posix()
        except ValueError:
            registry = str(subject.registry_path)
    labels = [TYPE_LABEL.get(g, g) for g in subject.enabled_computed_generators]
    return templates.TemplateResponse(
        request=request, name="subject.html",
        context=_context(request, subject=subject, paper_count=paper_count,
                         registry_display=registry, generator_labels=labels))


@app.get("/{code}/library", response_class=HTMLResponse)
def library(request: Request, code: str, q: str = "", computed: str = "any",
            topic: str = "any", placeholders: str = "any") -> HTMLResponse:
    subject = _require_subject_page(code)
    items = library_items(subject.code)
    filtered = filter_library(items, q=q, computed=computed, topic=topic,
                              placeholders=placeholders)
    topics = sorted({name for item in items
                     for name, marks in (item["topic_marks"] or {}).items()
                     if int(marks) > 0})
    computed_options = sorted({int(item["computed_display"]) for item in items})
    context = _context(request, subject=subject, items=filtered,
                       total=len(items), q=q, computed=computed, topic=topic,
                       placeholders=placeholders, topics=topics,
                       computed_options=computed_options)
    name = ("_library.html"
            if request.headers.get("HX-Request") == "true" else "library.html")
    return templates.TemplateResponse(request=request, name=name,
                                      context=context)


@app.get("/{code}/library/{seed}/{kind}")
def library_download(code: str, seed: int, kind: str) -> FileResponse:
    subject = _require_subject_page(code)
    path = library_file(seed, kind, subject.code)
    if path is None:
        raise HTTPException(status_code=404, detail="library file not found")
    item = library_item(seed, subject.code)
    if item is None or kind not in item["downloads"]:
        raise HTTPException(status_code=404, detail="library file not found")
    return _download(path, kind, item["downloads"][kind])


@app.get("/{code}/generate", response_class=HTMLResponse)
def generate_page(request: Request, code: str) -> HTMLResponse:
    subject = _require_subject_page(code)
    return templates.TemplateResponse(
        request=request, name="generate.html",
        context=_context(request, subject=subject))


@app.post("/{code}/generate", response_class=HTMLResponse)
def create_job(request: Request, code: str, mode: str = Form("realistic"),
               seed: str = Form(""), computed_marks: str = Form("")) -> HTMLResponse:
    subject = _require_subject_page(code)
    try:
        seed_value = int(seed) if str(seed).strip() else None
        cm = int(computed_marks) if str(computed_marks).strip() else None
        job = manager.create(mode, seed_value, cm, subject=subject.code)
    except ValueError as e:
        return HTMLResponse(
            f'<div id="job" class="error">{html.escape(str(e))}</div>',
            status_code=200)
    return templates.TemplateResponse(
        request=request, name="_job.html",
        context={"job": job.public()})


def _job_for(code: str, job_id: str):
    job = manager.get(job_id)
    if job is None or job.subject != code.upper():
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.get("/{code}/jobs/{job_id}", response_class=HTMLResponse)
def job_status(request: Request, code: str, job_id: str) -> HTMLResponse:
    subject = _require_subject_page(code)
    job = _job_for(subject.code, job_id)
    return templates.TemplateResponse(
        request=request, name="_job.html", context={"job": job.public()})


@app.post("/{code}/jobs/{job_id}/cancel", response_class=HTMLResponse)
def cancel_job(request: Request, code: str, job_id: str) -> HTMLResponse:
    subject = _require_subject_page(code)
    job = _job_for(subject.code, job_id)
    manager.cancel(job.id)
    return templates.TemplateResponse(
        request=request, name="_job.html", context={"job": job.public()})


@app.get("/{code}/downloads/{job_id}/{kind}")
def job_download(code: str, job_id: str, kind: str) -> FileResponse:
    subject = _require_subject_page(code)
    job = _job_for(subject.code, job_id)
    if kind not in {"paper_docx", "paper_pdf", "scheme_docx", "scheme_pdf"}:
        raise HTTPException(status_code=400, detail="unknown file")
    path = Path(job.files.get(kind, ""))
    if not path.exists():
        raise HTTPException(status_code=404,
                            detail="file unavailable (PDF export may be off)")
    return _download(path, kind, job.download_names()[kind])


def run() -> None:
    import uvicorn
    uvicorn.run("src.app.main:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    run()
