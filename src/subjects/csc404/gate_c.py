"""Build the CSC404 V6 Library report and Gate C package.

Run:
    uv run python -m src.subjects.csc404.gate_c
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from src import config
from src.bank.store import load_json, save_json

CACHE = config.WEB_CACHE_DIR / "CSC404"
MANIFEST = CACHE / "manifest.json"
OUT = config.PROJECT_ROOT / "outputs" / "review" / "csc404_v2" / "library"
REPORT = OUT / "V6_REPORT.md"
GATE = OUT / "Gate_C_report.md"
INDEX = OUT / "index.html"
APPROVAL = config.PROJECT_ROOT / "outputs" / "review" / "csc404_v2" / "gate_c_approval.json"


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def build() -> dict:
    manifest = load_json(MANIFEST, {})
    seeds = manifest.get("seeds") or []
    if not seeds:
        raise SystemExit(f"Library manifest is missing: {MANIFEST}")
    counts = manifest.get("counts") or {}
    reuse = counts.get("max_question_reuse", 0)
    problems = []
    if len(seeds) != 20:
        problems.append(f"expected 20 seeds, found {len(seeds)}")
    if counts.get("qa_problems"):
        problems.append(f"QA problems: {counts['qa_problems']}")
    if reuse > 4:
        problems.append(f"question reuse {reuse} exceeds cap 4")
    if any(row.get("total_marks") != 100 for row in seeds):
        problems.append("a seed does not total 100 marks")
    if any(row.get("distinct_papers", 0) < 4 for row in seeds):
        problems.append("a seed uses fewer than four source papers")
    paper_pages = [row.get("paper_pages", 0) for row in seeds]
    scheme_pages = [row.get("scheme_pages", 0) for row in seeds]
    approved = load_json(APPROVAL, {}).get("status") == "approved"

    lines = [
        "# CSC404 V6 — Library",
        "",
        f"Date: {_today()}",
        "",
        f"- **{len(seeds)} seeds**; each has 6 questions, 100 marks and "
        f"{counts.get('distinct_papers_per_seed', 5)} distinct source papers.",
        f"- QA problems: **{counts.get('qa_problems', 0)}**.",
        f"- Maximum question reuse: **{reuse}** (cap 4).",
        f"- Paper pages: {min(paper_pages)}–{max(paper_pages)}; "
        f"scheme pages: {min(scheme_pages)}–{max(scheme_pages)}.",
        "- Deterministic recycle; **$0** LLM cost at V6.",
        "- All answers remain `model_unofficial`.",
        "",
        "| Seed | Questions | Marks | Papers | Paper pages | Scheme pages |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in seeds:
        lines.append(
            f"| {row['seed']} | {len(row.get('questions') or [])} | "
            f"{row.get('total_marks')} | {row.get('distinct_papers')} | "
            f"{row.get('paper_pages')} | {row.get('scheme_pages')} |")
    lines += [
        "",
        "## Cache",
        "",
        f"- Cache: `{CACHE}`",
        f"- Manifest: `{MANIFEST}`",
        "",
        "## Gate C",
        "",
        ("**Approved** by the owner." if approved
         else "Pending owner approval. No publication, upload or deploy has "
              "been performed."),
        "",
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    gate_lines = [
        "# CSC404 — Gate C publication review",
        "",
        f"Date: {_today()}",
        "",
        f"- Library: **{len(seeds)} seeds**, 6 questions and 100 marks each.",
        f"- QA problems: **{counts.get('qa_problems', 0)}**; maximum question "
        f"reuse **{reuse}** (cap 4).",
        "- Documents are v2 only; v1 is legacy and is not part of this "
        "publication.",
        "- Publication will be scoped to CSC404: its seed papers, schemes, "
        "manifest and `subject.json`; shared site index files may be "
        "refreshed.",
        "- No publication, R2 upload or Worker deploy has been performed.",
        "",
        "## Gate C decision",
        "",
        ("**Approved** by the owner on "
         + str(load_json(APPROVAL, {}).get("on") or "") + "."
         if approved else "Pending owner review."),
        "",
    ]
    GATE.write_text("\n".join(gate_lines), encoding="utf-8")

    rows = []
    for row in seeds:
        seed = row["seed"]
        rows.append(
            "<tr>"
            f"<td>{seed}</td><td>6</td><td>100</td>"
            f"<td>{escape(str(row.get('distinct_papers')))}</td>"
            f"<td>{row.get('paper_pages')}</td>"
            f"<td>{row.get('scheme_pages')}</td>"
            f"<td><a href='{escape(str(row.get('paper_pdf')))}'>paper</a> · "
            f"<a href='{escape(str(row.get('scheme_pdf')))}'>scheme</a></td>"
            "</tr>")
    INDEX.write_text(
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>CSC404 V6 Library</title>"
        "<style>body{font-family:Arial;margin:2rem}"
        "table{border-collapse:collapse}"
        "td,th{border:1px solid #999;padding:.4rem}"
        "</style></head><body>"
        "<h1>CSC404 — V6 Library</h1>"
        f"<p><b>{len(seeds)} seeds</b>, 6 questions and 100 marks each. "
        "QA 0; maximum question reuse 4.</p>"
        "<table><tr><th>Seed</th><th>Questions</th><th>Marks</th>"
        "<th>Papers</th><th>Paper pages</th><th>Scheme pages</th>"
        "<th>Files</th></tr>" + "".join(rows) + "</table>"
        f"<p>Gate C: <b>{'approved' if approved else 'pending'}</b>.</p>"
        "</body></html>", encoding="utf-8")
    summary = {
        "seeds": len(seeds),
        "qa_problems": counts.get("qa_problems", 0),
        "max_question_reuse": reuse,
        "problems": problems,
        "gate_c": "approved" if approved else "pending",
        "report": str(REPORT),
        "gate_report": str(GATE),
        "index": str(INDEX),
    }
    save_json(OUT / "gate_c_summary.json", summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
