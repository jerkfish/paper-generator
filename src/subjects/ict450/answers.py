"""V4 answer bank for ICT450.

Answers are model-authored from the approved question text and the supplied
source assets.  No official ICT450 marking scheme was supplied, so every answer
is labelled ``model_unofficial``.  The module builds:

* ``bank/answers.json`` — structured answer objects by question id.
* ``bank/answers_report.json`` — provenance, confidence and media report.
* ``bank/answers/media/*.png`` — rendered ERD answer diagrams.
* ``bank/review/answers.html`` — a readable review sheet.
"""
from __future__ import annotations

import argparse
import html
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from src import config
from src.bank.schema import validate_answer
from src.bank.store import BankStore, save_json
from src.subjects.ict450.answers_content import ANSWERS
from src.subjects.ict450.answers_content._blocks import flatten
from src.subjects.ict450.diagrams import erd_svg, render_erd

BANK = config.TRACKING_DIR / "ict450" / "v2" / "bank"
MEDIA = BANK / "answers" / "media"
ANSWERS_PATH = BANK / "answers.json"
REPORT_PATH = BANK / "answers_report.json"
REVIEW_PATH = BANK / "review" / "answers.html"
PROVENANCE = "model_unofficial"


def _walk(blocks: list[dict]):
    for block in blocks or []:
        yield block
        if block.get("type") == "sub":
            yield from _walk(block.get("blocks") or [])


def _sub_marks(blocks: list[dict]) -> int:
    return sum(int(block.get("marks") or 0) for block in blocks or []
               if block.get("type") == "sub")


def _sub_labels(blocks: list[dict]) -> list[str]:
    return [str(block.get("label")) for block in blocks or []
            if block.get("type") == "sub"]


def _check_content(question: dict, content: dict) -> list[str]:
    problems = []
    blocks = content.get("blocks") or []
    labels = _sub_labels(blocks)
    expected = [str(part.get("label")) for part in
                question.get("subparts") or []]
    if expected and labels != expected:
        problems.append(
            f"subpart labels {labels} do not match the question {expected}")
    total = _sub_marks(blocks)
    marks = int(question.get("marks") or 0)
    if total != marks:
        problems.append(f"answer marks {total} do not match question {marks}")
    if not str(flatten(blocks)).strip():
        problems.append("flattened answer is empty")
    return problems


def _render_media(question_id: str, blocks: list[dict]) -> list[str]:
    media = []
    index = 0
    for block in _walk(blocks):
        if block.get("type") != "erd":
            continue
        index += 1
        target = MEDIA / f"{question_id}_{index}.png"
        if not target.exists():
            render_erd(block["spec"], target)
        block["path"] = str(target)
        media.append(str(target.relative_to(config.PROJECT_ROOT)))
    return media


def build(question_ids: list[str] | None = None,
          *, render: bool = True) -> dict:
    store = BankStore(BANK)
    approved = {str(question["id"]): question
                for question in store.approved_questions()}
    selected = sorted(question_ids or ANSWERS)
    payload = {
        "schema_version": 1,
        "subject": "ICT450",
        "official": False,
        "unofficial": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "by_qid": {},
    }
    report_rows = []
    media_all = []
    problems_all = []
    for question_id in selected:
        if question_id not in ANSWERS:
            problems_all.append(f"{question_id}: no authored answer")
            continue
        question = approved.get(question_id)
        if question is None:
            problems_all.append(f"{question_id}: not an approved question")
            continue
        content = ANSWERS[question_id]
        problems = _check_content(question, content)
        if problems:
            problems_all.extend(f"{question_id}: {problem}"
                                for problem in problems)
            continue
        blocks = json.loads(json.dumps(content["blocks"]))
        media = _render_media(question_id, blocks) if render else []
        media_all.extend(media)
        entry = {
            "question_id": question_id,
            "content_hash": question.get("content_hash"),
            "provenance": PROVENANCE,
            "official": False,
            "unofficial": True,
            "confidence": content.get("confidence", "medium"),
            "source": ("Model-authored from the approved question text, the "
                       "supplied source assets and the ICT200/ICT450 knowledge "
                       "base; no official ICT450 marking scheme was supplied."),
            "kb_sources": list(content.get("kb_sources") or []),
            "assumptions": list(content.get("assumptions") or []),
            "notes": str(content.get("notes") or ""),
            "answer": flatten(blocks),
            "blocks": blocks,
            "marking": list(content.get("marking") or []),
            "media": media,
        }
        errors = validate_answer(entry)
        if errors:
            problems_all.extend(f"{question_id}: {error}"
                                for error in errors)
            continue
        payload["by_qid"][question_id] = entry
        report_rows.append({
            "question_id": question_id,
            "provenance": entry["provenance"],
            "confidence": entry["confidence"],
            "marks": int(question.get("marks") or 0),
            "answer_marks": _sub_marks(blocks),
            "media": media,
            "kb_sources": entry.get("kb_sources", []),
        })
    save_json(ANSWERS_PATH, payload)
    missing = sorted(set(approved) - set(payload["by_qid"]))
    report = {
        "schema_version": 1,
        "subject": "ICT450",
        "stage": "V4_answers",
        "generated_at": payload["generated_at"],
        "official_scheme_used": False,
        "provenance": PROVENANCE,
        "approved_questions": len(approved),
        "answered_questions": len(payload["by_qid"]),
        "missing_questions": missing,
        "media": sorted(media_all),
        "problems": problems_all,
        "cost_usd": 0.0,
        "llm_calls": 0,
        "answers": report_rows,
    }
    save_json(REPORT_PATH, report)
    return report


def _render_block(block: dict) -> str:
    kind = block.get("type")
    if kind == "p":
        return f"<p>{html.escape(str(block.get('text') or ''))}</p>"
    if kind == "h":
        return f"<h4>{html.escape(str(block.get('text') or ''))}</h4>"
    if kind == "callout":
        return (f"<div class='callout'>"
                f"{html.escape(str(block.get('text') or ''))}</div>")
    if kind == "bullets":
        items = "".join(f"<li>{html.escape(str(item))}</li>"
                        for item in block.get("items") or [])
        return f"<ul>{items}</ul>"
    if kind == "sub":
        label = html.escape(str(block.get("label") or ""))
        marks = block.get("marks")
        head = f"<div class='subhead'><span>({label})</span>"
        if block.get("text"):
            head += f"<span class='subtext'>{html.escape(str(block['text']))}"
            head += "</span>"
        if marks:
            head += f"<span class='marks'>({marks} marks)</span>"
        head += "</div>"
        body = _render_block({"type": "bullets",
                              "items": block.get("items") or []})
        nested = "".join(_render_block(item)
                         for item in block.get("blocks") or [])
        return head + body + nested
    if kind == "sql":
        caption = (f"<div class='caption'>{html.escape(str(block['caption']))}"
                   "</div>" if block.get("caption") else "")
        return (f"{caption}<pre class='sql'><code>"
                f"{html.escape(str(block.get('code') or ''))}</code></pre>")
    if kind == "schema":
        caption = (f"<div class='caption'>{html.escape(str(block['caption']))}"
                   "</div>" if block.get("caption") else "")
        text = "\n".join(str(line) for line in block.get("lines") or [])
        return f"{caption}<pre class='schema'>{html.escape(text)}</pre>"
    if kind == "table":
        head = "".join(f"<th>{html.escape(str(col))}</th>"
                       for col in block.get("columns") or [])
        rows = "".join(
            "<tr>" + "".join(f"<td>{html.escape(str(cell))}</td>"
                             for cell in row) + "</tr>"
            for row in block.get("rows") or [])
        caption = (f"<div class='caption'>{html.escape(str(block['caption']))}"
                   "</div>" if block.get("caption") else "")
        return (f"{caption}<table><thead><tr>{head}</tr></thead>"
                f"<tbody>{rows}</tbody></table>")
    if kind == "erd":
        svg, width, height = erd_svg(block["spec"])
        caption = html.escape(str(block.get("caption") or ""))
        return (f"<div class='erd' style='max-width:{width}px'>{svg}</div>"
                f"<div class='caption'>{caption}</div>")
    return ""


def render_review() -> Path:
    store = BankStore(BANK)
    answers = store.answers_by_question()
    questions = {str(question["id"]): question
                 for question in store.approved_questions()}
    blocks = []
    for qid in sorted(answers):
        answer = answers[qid]
        question = questions.get(qid) or store.load_question(qid)
        text = str((question.get("native_text_blocks") or [{}])[0]
                   .get("text") or "")
        blocks.append(
            "<section class='answer'>"
            f"<h2>{html.escape(qid)} "
            f"<span class='meta'>{html.escape(question.get('source_paper', ''))}"
            f" · {question.get('marks')} marks</span></h2>"
            f"<div class='question'>{html.escape(text)}</div>"
            f"<div class='provenance'>Provenance: {answer['provenance']} · "
            f"confidence {answer['confidence']}</div>"
            f"{_render_block({'type': 'p', 'text': answer.get('source', '')})}"
            + "".join(_render_block(block)
                      for block in answer.get("blocks") or [])
            + "<div class='marking'><h3>Marking guide</h3><ul>"
            + "".join(f"<li>{html.escape(str(point))}</li>"
                      for point in answer.get("marking") or [])
            + "</ul></div>"
            + ("<div class='assumptions'><h3>Assumptions</h3><ul>"
               + "".join(f"<li>{html.escape(str(item))}</li>"
                         for item in answer.get("assumptions") or [])
               + "</ul></div>" if answer.get("assumptions") else "")
            + "</section>")
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>ICT450 V4 answers — review</title>
<style>
:root {{ color-scheme: light; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: #eef2f7; color: #0f172a;
       font-family: Arial, Helvetica, sans-serif; }}
main {{ max-width: 1100px; margin: 0 auto; padding: 28px 22px 60px; }}
header {{ background: #1f3864; color: #fff; padding: 26px 30px;
          border-radius: 12px; margin-bottom: 22px; }}
header h1 {{ margin: 0 0 6px; font-size: 24px; }}
header p {{ margin: 4px 0; color: #dbe5f3; font-size: 13px; }}
.answer {{ background: #fff; padding: 22px 26px 26px; margin: 20px 0;
           border-radius: 10px; border: 1px solid #d7dfeb; }}
h2 {{ font-size: 17px; margin: 0 0 10px; color: #1f3864; }}
h2 .meta {{ font-size: 12px; color: #64748b; font-weight: normal; }}
h3 {{ font-size: 13px; margin: 16px 0 6px; color: #1f3864; }}
h4 {{ font-size: 13px; margin: 12px 0 4px; color: #1f3864; }}
.question {{ background: #f8fafc; border-left: 4px solid #94a3b8;
             padding: 10px 14px; margin: 8px 0 12px; white-space: pre-wrap;
             font-size: 12px; color: #334155; }}
.provenance {{ font-size: 11px; color: #64748b; margin: 8px 0; }}
p {{ font-size: 13px; line-height: 1.55; margin: 7px 0; }}
ul {{ margin: 4px 0 8px 20px; padding: 0; }}
li {{ font-size: 13px; line-height: 1.5; margin: 3px 0; }}
.subhead {{ display: flex; gap: 8px; align-items: baseline; margin: 14px 0 4px;
            font-size: 13px; font-weight: 700; color: #1f3864; }}
.subtext {{ font-weight: 600; }}
.marks {{ margin-left: auto; font-size: 11px; color: #b45309; font-weight: 700; }}
.caption {{ font-size: 11px; color: #64748b; text-align: center;
            margin: 8px 0 4px; }}
pre.sql {{ background: #0f172a; color: #e2e8f0; padding: 14px 16px;
           border-radius: 8px; overflow-x: auto; font-size: 12px;
           line-height: 1.45; font-family: Consolas, "Courier New", monospace; }}
pre.schema {{ background: #f1f5f9; color: #0f172a; padding: 12px 14px;
              border-radius: 6px; font-size: 12px; line-height: 1.55;
              font-family: Consolas, "Courier New", monospace;
              white-space: pre-wrap; }}
table {{ border-collapse: collapse; width: 100%; margin: 6px 0 12px;
         font-size: 11px; }}
th, td {{ border: 1px solid #cbd5e1; padding: 5px 7px; text-align: left;
          vertical-align: top; }}
th {{ background: #1f3864; color: #fff; font-weight: 700; }}
tr:nth-child(even) td {{ background: #f8fafc; }}
.erd {{ background: #fff; border: 1px solid #cbd5e1; border-radius: 8px;
        padding: 8px; margin: 10px 0 4px; overflow: auto; }}
.erd svg {{ display: block; width: 100%; height: auto; }}
.callout {{ background: #fff7ed; border-left: 4px solid #f59e0b;
            padding: 10px 14px; font-size: 12px; margin: 10px 0; }}
.marking, .assumptions {{ margin-top: 14px; padding-top: 10px;
                          border-top: 1px solid #e2e8f0; }}
.marking li {{ color: #334155; font-style: italic; }}
.assumptions li {{ color: #7c2d12; }}
</style></head><body><main>
<header>
<h1>ICT450 — V4 model answers</h1>
<p>Unofficial reference answers for the 15 distinct questions used in seeds 1–3.</p>
<p>Provenance: model_unofficial. Generated from the approved question text and
supplied source assets. No official marking scheme was supplied.</p>
<p>LLM cost: $0.00 · {len(answers)} answered questions</p>
</header>
{''.join(blocks)}
</main></body></html>"""
    REVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    REVIEW_PATH.write_text(page, encoding="utf-8")
    return REVIEW_PATH


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", nargs="*", default=None)
    parser.add_argument("--no-render", action="store_true")
    args = parser.parse_args()
    report = build(args.questions, render=not args.no_render)
    path = render_review()
    print(json.dumps({
        "answered": report["answered_questions"],
        "missing": len(report["missing_questions"]),
        "problems": report["problems"],
        "review": str(path),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
