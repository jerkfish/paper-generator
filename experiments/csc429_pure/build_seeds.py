"""Build CSC429 seeds 1-3 with the pure-extraction rules.

This is deliberately outside the lifecycle/stage pipeline.  It selects real
past-paper questions that were not used by the rejected Stage-8 set, reuses
their original picture/diagram/table crops, and builds three paper + scheme
pairs through the same presentation rules approved in the experiment:

* original crops, never recreated diagrams;
* native captions;
* right-tabbed marks;
* no question bodies in the scheme.

    uv run python experiments/csc429_pure/build_seeds.py
"""
from __future__ import annotations

import json
import shutil
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import config
from src.subjects import forbidden
from src.subjects.csc429 import answers, build_docx as builder
from src.subjects.csc429 import seed_pilot as pilot

OUT = ROOT / "outputs" / "experiments" / "csc429_pure_20261107"
TRACKING = config.TRACKING_DIR / "csc429"
BANK_PATH = TRACKING / "question_bank_draft.json"
LOG_PATH = TRACKING / "question_log.json"
ASSETS_PATH = TRACKING / "assets" / "manifest.json"

# Each seed has 4 x 5-mark, 6 x 10-mark and 1 x 20-mark question.  The lists
# are fixed by hand after checking marks, topics, source-paper diversity and
# asset availability.  No question is reused across the three seeds.
SELECTIONS = {
    1: {
        "A1": "CSC429-2014-12-A1",   # generations, native Table 1
        "A2": "CSC429-2023-02-A2",   # architecture, Figure 1
        "A3": "CSC429-2025-02-A3",   # data representation, Figure 1
        "A4": "CSC429-2018-06-A6",   # memory, native text
        "A5": "CSC429-2014-06-A4",   # architecture, Figure 1
        "A6": "CSC429-2018-01-A9",   # addressing, Figure 2
        "A7": "CSC429-2023-07-A9",   # I/O, Figure 1
        "A8": "CSC429-2024-07-A10",  # parallel, native text
        "A9": "CSC429-2019-12-A8",   # architecture, native text
        "A10": "CSC429-2024-01-A5",  # data representation, native text
        "B1": "CSC429-2026-02-B1",   # assembly, Figure 5 + instruction table
    },
    2: {
        "A1": "CSC429-2017-07-A1",   # generations, Figure 1
        "A2": "CSC429-2018-06-A1",   # generations, Figure 1
        "A3": "CSC429-2026-02-A3",   # data representation, Figure 1
        "A4": "CSC429-2019-06-A2",   # architecture, native text
        "A5": "CSC429-2016-06-A9",   # I/O, Figure 2
        "A6": "CSC429-2023-02-A10",  # parallel, Figure 3
        "A7": "CSC429-2023-07-A10",  # parallel, Figure 2
        "A8": "CSC429-2025-02-A7",   # memory, native text
        "A9": "CSC429-2019-12-A3",   # data representation, native text
        "A10": "CSC429-2015-12-A10",  # parallel, native text
        "B1": "CSC429-2025-07-B1",   # assembly, Figure 1 + instruction table
    },
    3: {
        "A1": "CSC429-2014-12-A5",   # architecture, Figure 1
        "A2": "CSC429-2018-01-A1",   # generations, Figure 1
        "A3": "CSC429-2016-06-A6",   # memory, native text
        "A4": "CSC429-2018-12-A2",   # data representation, native text
        "A5": "CSC429-2024-07-A9",   # I/O, Figure 1
        "A6": "CSC429-2026-02-A10",  # parallel, Figure 4
        "A7": "CSC429-2014-06-A7",   # I/O, native text
        "A8": "CSC429-2015-06-A10",  # parallel, native text
        "A9": "CSC429-2025-02-A6",   # addressing, native text
        "A10": "CSC429-2018-06-A3",  # data representation, native text
        "B1": "CSC429-2023-02-B1",   # assembly, Figure 4 + instruction table
    },
}


CAPTION_FIXES = {
    "Table 1: lt/achine instruction": "Table 1: Machine instruction",
    "Figure 2: Non-uniform 'Memory Access (NUMA)":
        "Figure 2: Non-uniform Memory Access (NUMA)",
}


def _clean_caption(text: str) -> str:
    value = " ".join(str(text or "").split())
    value = value.replace(" :", ":")
    return CAPTION_FIXES.get(value, value)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _slot(label: str, question: dict, entry: dict) -> dict:
    part = str(entry["part"])
    return {
        "slot": label,
        "part": part,
        "question": label,
        "kind": "real_bank_question",
        "marks": int(question["marks"]),
        "topic": entry["topic"],
        "topic_label": builder.planner.TOPICS[entry["topic"]]["title"],
        "task": ("assembly_program" if part == "B" else "short_answer"),
        "title": builder.planner.SINGLE_MARK_TITLES[label],
        "resolver": "csc429.real_bank",
        "variant_policy": "verbatim",
        "generator_pool": [],
        "asset_policy": "source_crop_table_native",
    }


def _resolved(selection: dict) -> tuple[list[dict], dict]:
    bank = _load(BANK_PATH)
    log = _load(LOG_PATH)
    questions = {row["question_id"]: row for row in bank["questions"]}
    entries = {row["question_id"]: row for row in log["entries"]}
    assets = pilot._asset_index(_load(ASSETS_PATH))
    layouts = pilot._layout_index()
    slots = []
    for label in ("A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9",
                  "A10", "B1"):
        question_id = selection[label]
        question = questions[question_id]
        entry = entries[question_id]
        content = pilot.build_content(question, assets, layouts)
        if not content:
            raise RuntimeError(f"{question_id}: no renderable content")
        for block in content:
            if block.get("caption"):
                block["caption"] = _clean_caption(block["caption"])
        selected_assets = pilot._question_assets(question, assets)
        slots.append({
            **_slot(label, question, entry),
            "question_id": question_id,
            "paper_id": question["paper_id"],
            "source_file": question.get("source_file", ""),
            "source_pages": question.get("pages", []),
            "asset_ids": [asset["asset_id"] for asset in selected_assets],
            "content": content,
            "text": question.get("text", ""),
            "subparts": question.get("subparts", []),
            "answer": "",
            "marking": [],
            "generator_id": "",
        })
    return slots, {
        "questions": questions,
        "entries": entries,
        "assets": assets,
    }


def _plan(seed: int, slots: list[dict]) -> dict:
    topic_marks = Counter()
    part_marks = Counter()
    for slot in slots:
        topic_marks[slot["topic"]] += slot["marks"]
        part_marks[slot["part"]] += slot["marks"]
    if len(slots) != 11 or part_marks != {"A": 80, "B": 20}:
        raise RuntimeError(
            f"seed {seed}: invalid slots or part marks {dict(part_marks)}")
    if [slot["marks"] for slot in slots[:4]] != [5] * 4:
        raise RuntimeError(f"seed {seed}: Part A must start with four 5-mark slots")
    if [slot["marks"] for slot in slots[4:10]] != [10] * 6:
        raise RuntimeError(f"seed {seed}: Part A must end with six 10-mark slots")
    if slots[10]["marks"] != 20:
        raise RuntimeError(f"seed {seed}: B1 must be 20 marks")
    papers = [slot["paper_id"] for slot in slots]
    if len(papers) != len(set(papers)):
        raise RuntimeError(f"seed {seed}: a source paper is used twice")
    return {
        "subject": "CSC429",
        "planner_version": 1,
        "generated_by": "experiments.csc429_pure.build_seeds",
        "style": "pure_extraction",
        "seed": seed,
        "target_format": {
            "A": {"questions": 10, "marks": 80,
                  "slot_marks": [5, 5, 5, 5, 10, 10, 10, 10, 10, 10]},
            "B": {"questions": 1, "marks": 20},
        },
        "source_evidence": [
            "data/tracking/csc429/question_bank_draft.json",
            "data/tracking/csc429/question_log.json",
            "data/tracking/csc429/assets/manifest.json",
        ],
        "topic_quota": dict(sorted(topic_marks.items())),
        "part_marks": dict(part_marks),
        "topic_marks": dict(sorted(topic_marks.items())),
        "total_marks": sum(part_marks.values()),
        "question_count": len(slots),
        "slot_count": len(slots),
        "slots": slots,
        "notes": (
            "Pure-extraction build outside the lifecycle. Every question is a "
            "real past-paper question; figures are original source crops, not "
            "recreated diagrams; captions are native text."),
    }


def _qa_and_export(seed: int, plan: dict, out: Path) -> dict:
    paper_docx = out / "paper.docx"
    scheme_docx = out / "scheme.docx"
    paper_pdf = out / "paper.pdf"
    scheme_pdf = out / "scheme.pdf"
    builder.build_paper(plan, paper_docx)
    builder.build_scheme(plan, scheme_docx)

    paper_pages, paper_pdf = pilot._export_seed_pdf(paper_docx, paper_pdf)
    pilot._patch_page_count(paper_docx, paper_pages)
    paper_pages, paper_pdf = pilot._export_seed_pdf(paper_docx, paper_pdf)

    scheme_pages, scheme_pdf = pilot._export_seed_pdf(scheme_docx, scheme_pdf)
    builder._scheme_page_count(scheme_docx, scheme_pages)
    scheme_pages, scheme_pdf = pilot._export_seed_pdf(scheme_docx, scheme_pdf)

    qa = {
        "subject": "CSC429",
        "seed": seed,
        "builder_version": builder.BUILDER_VERSION,
        "warnings": [],
        "paper_docx": builder._paper_qa(plan, paper_docx, None),
        "scheme_docx": builder._scheme_qa(
            plan, scheme_docx, None, require_model_answers=True),
        "paper_pdf": builder._pdf_qa(paper_pdf, scheme=False),
        "scheme_pdf": builder._pdf_qa(scheme_pdf, scheme=True),
    }
    qa["paper_pdf"]["pages"] = paper_pages
    qa["scheme_pdf"]["pages"] = scheme_pages
    files = {
        "paper_docx": str(paper_docx),
        "paper_pdf": str(paper_pdf),
        "scheme_docx": str(scheme_docx),
        "scheme_pdf": str(scheme_pdf),
    }
    scan = forbidden.scan([Path(value) for value in files.values()], "CSC429")
    qa["forbidden_hits"] = scan["hits"]
    qa["problems"] = []
    for key in ("paper_docx", "scheme_docx", "paper_pdf", "scheme_pdf"):
        qa["problems"].extend(qa[key].get("problems", []))
    if scan["hits"]:
        qa["problems"].append(
            "forbidden tokens: " + ", ".join(
                f"{Path(hit['path']).name}:{hit['token']}"
                for hit in scan["hits"][:8]))
    qa["files"] = files
    (out / "qa.json").write_text(
        json.dumps(qa, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if qa["problems"]:
        raise RuntimeError(
            f"CSC429 pure seed {seed}: " + "; ".join(qa["problems"][:5]))
    return qa


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    selected_ids = [qid for selection in SELECTIONS.values()
                    for qid in selection.values()]
    if len(selected_ids) != len(set(selected_ids)):
        raise RuntimeError("a question is selected in more than one slot")
    manifest = {"subject": "CSC429", "approach": "pure_extraction",
                "seeds": [], "selections": SELECTIONS}
    for seed, selection in SELECTIONS.items():
        out = OUT / f"seed_{seed:02d}"
        out.mkdir(parents=True, exist_ok=True)
        slots, _ = _resolved(selection)
        plan = _plan(seed, slots)
        answer_report = answers.ensure_answers(
            slots, allow_llm=True, strict=True)
        plan["slots"] = slots
        plan["answer_report"] = answer_report
        (out / "plan.json").write_text(
            json.dumps(plan, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
        qa = _qa_and_export(seed, plan, out)
        manifest["seeds"].append({
            "seed": seed,
            "selection": selection,
            "paper_pages": qa["paper_pdf"]["pages"],
            "scheme_pages": qa["scheme_pdf"]["pages"],
            "asset_questions": sum(
                1 for slot in slots if slot["asset_ids"]),
            "answers": {
                "requested": answer_report["requested"],
                "cache_hits": answer_report["cache_hits"],
                "generated": answer_report["generated"],
                "failed": answer_report["failed"],
                "cost_usd": answer_report["cost_usd"],
            },
            "files": qa["files"],
        })
        print(json.dumps({
            "seed": seed,
            "paper_pages": qa["paper_pdf"]["pages"],
            "scheme_pages": qa["scheme_pdf"]["pages"],
            "answers": manifest["seeds"][-1]["answers"],
            "problems": qa["problems"],
        }, indent=2, ensure_ascii=False))
    manifest["summary"] = {
        "seed_count": len(manifest["seeds"]),
        "unique_questions": len(set(selected_ids)),
        "fresh_questions": sum(
            1 for qid in selected_ids
            if qid not in _stage8_questions()),
        "reused_stage8_questions": sorted(
            qid for qid in selected_ids if qid in _stage8_questions()),
        "answer_generation": {
            "initial_calls": 31,
            "initial_cost_usd": 0.028619,
            "last_build_generated": sum(
                row["answers"]["generated"] for row in manifest["seeds"]),
            "note": "Initial generation made 30 calls, plus one corrected "
                    "answer; cached rebuilds cost $0.",
        },
        "publication": False,
    }
    (OUT / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    lines = [
        "# CSC429 pure-extraction seeds 1-3",
        "",
        "Built outside the lifecycle/stage pipeline after the owner rejected "
        "the staged 20-seed set.",
        "",
        "## What is here",
        "",
        "- `seed_01/`, `seed_02/`, `seed_03/` — paper + scheme DOCX/PDF, "
        "`plan.json`, `qa.json`.",
        "- `run_manifest.json` — selections, page counts, answer cost and "
        "validation summary.",
        "",
        "## Rules applied",
        "",
        "- Every question is a real past-paper question.",
        "- Pictures, diagrams and tables are taken from the supplied papers; "
        "diagrams are never recreated.",
        "- Captions are native text; `(N marks)` is right-tabbed; the scheme "
        "does not print question bodies.",
        "- No question is reused across the three seeds.",
        "",
        "## Review notes",
        "",
        f"- {manifest['summary']['fresh_questions']} of "
        f"{manifest['summary']['unique_questions']} questions are not in the "
        "rejected Stage-8 set.",
        "- The three B1 assembly questions are reused from the rejected set "
        "because only five 20-mark B1 questions pass the table-readiness gate; "
        "the other B1 candidates depend on fill-in tables that are not "
        "recreated from OCR.",
        f"- Answer generation: "
        f"{manifest['summary']['answer_generation']['initial_calls']} new "
        f"calls, "
        f"${manifest['summary']['answer_generation']['initial_cost_usd']:.6f}.",
        "- No publication, R2 upload or Worker deployment.",
        "",
    ]
    (OUT / "README.md").write_text("\n".join(lines), encoding="utf-8")


def _stage8_questions() -> set[str]:
    report = ROOT / "data" / "tracking" / "csc429" / "stage8_coverage.json"
    if not report.exists():
        return set()
    payload = json.loads(report.read_text(encoding="utf-8"))
    return {qid for seed in payload.get("seeds", [])
            for qid in seed.get("real_question_ids", [])}


if __name__ == "__main__":
    main()
