"""Local FastAPI + HTMX UI for the mock paper generator."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src import config
from src.app.jobs import library_file, library_items, manager

APP_DIR = Path(__file__).resolve().parent
app = FastAPI(title="CSC662 Mock Paper Generator")
app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")),
          name="static")
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))


def _index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request, name="index.html",
        context={"public": config.PUBLIC_BUILD,
                 "cost_cap": config.WEB_COST_CAP_USD,
                 "model": config.MOCKGEN_MODEL,
                 "has_key": bool(config.DEEPSEEK_API_KEY)})


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return _index(request)


@app.post("/jobs", response_class=HTMLResponse)
def create_job(request: Request,
               mode: str = Form("realistic"),
               seed: str = Form(""),
               computed_marks: str = Form("")) -> HTMLResponse:
    try:
        seed_value = int(seed) if str(seed).strip() else None
        cm = int(computed_marks) if str(computed_marks).strip() else None
        job = manager.create(mode, seed_value, cm)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return templates.TemplateResponse(
        request=request, name="_job.html",
        context={"job": job.public(), "cost_cap": config.WEB_COST_CAP_USD})


@app.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_status(request: Request, job_id: str) -> HTMLResponse:
    job = manager.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return templates.TemplateResponse(
        request=request, name="_job.html",
        context={"job": job.public(), "cost_cap": config.WEB_COST_CAP_USD})


@app.post("/jobs/{job_id}/cancel", response_class=HTMLResponse)
def cancel_job(request: Request, job_id: str) -> HTMLResponse:
    if not manager.cancel(job_id):
        raise HTTPException(status_code=404, detail="job not found")
    job = manager.get(job_id)
    return templates.TemplateResponse(
        request=request, name="_job.html",
        context={"job": job.public(), "cost_cap": config.WEB_COST_CAP_USD})


@app.get("/library", response_class=HTMLResponse)
def library(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request, name="_library.html",
        context={"items": library_items(), "public": config.PUBLIC_BUILD})


@app.get("/library/{seed}/{kind}")
def library_download(seed: int, kind: str):
    path = library_file(seed, kind)
    if path is None:
        raise HTTPException(status_code=404, detail="library file not found")
    media = ("application/pdf" if kind.endswith("pdf")
             else "application/vnd.openxmlformats-officedocument."
                  "wordprocessingml.document")
    return FileResponse(str(path), media_type=media, filename=path.name)


@app.get("/downloads/{job_id}/{kind}")
def job_download(job_id: str, kind: str):
    job = manager.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    if kind not in {"paper_docx", "paper_pdf", "scheme_docx", "scheme_pdf"}:
        raise HTTPException(status_code=400, detail="unknown file")
    path = Path(job.files.get(kind, ""))
    if not path.exists():
        raise HTTPException(status_code=404,
                            detail="file unavailable (PDF export may be off)")
    media = ("application/pdf" if kind.endswith("pdf")
             else "application/vnd.openxmlformats-officedocument."
                  "wordprocessingml.document")
    return FileResponse(str(path), media_type=media, filename=path.name)


def run() -> None:
    import uvicorn
    uvicorn.run("src.app.main:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    run()
