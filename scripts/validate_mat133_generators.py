"""Generate, build and validate MAT133 computed-generator groups.

Run:
    uv run python -m scripts.validate_mat133_generators --group 1
    uv run python -m scripts.validate_mat133_generators --group all --seed 7

Each group becomes one mock paper and marking scheme.  The Word COM export and
the DOCX/XML/PDF checks are the acceptance gate; a non-empty failure list is a
non-zero exit.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.mat133.build_docx import build_bundle
from src.mat133.generators.registry import generate_priority
from src.mat133.models import Mat133Paper, Mat133Question

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "mat133_gen_validation"


def make_paper(priority: int, seed: int) -> Mat133Paper:
    groups = generate_priority(priority, seed=seed,
                               out_dir=OUT / f"group{priority}" / "figures")
    questions = []
    for number, (topic, parts) in enumerate(groups.items(), 1):
        for index, part in enumerate(parts):
            part.label = chr(97 + index)
        questions.append(Mat133Question(number=number, parts=parts))
    return Mat133Paper(
        month="NOVEMBER", year=2026, duration="3 HOURS",
        questions=questions, seed=seed,
        generator_notes=[f"Priority {priority} computed generators"],
    )


def check_result(result: dict) -> list[str]:
    failures = []
    for key in ("paper_docx_check", "scheme_docx_check"):
        check = result[key]
        if check.get("forbidden_tokens"):
            failures.append(f"{key}: forbidden {check['forbidden_tokens']}")
        if key == "scheme_docx_check":
            if check.get("part_labels_found") != check.get("expected_parts"):
                failures.append(f"{key}: part label count mismatch")
        elif check.get("question_headings") != check.get("expected_questions"):
            failures.append(f"{key}: heading count mismatch")
        if not check.get("has_crest"):
            failures.append(f"{key}: crest missing")
    for key in ("paper_pdf_check", "scheme_pdf_check"):
        check = result[key]
        for field in ("page1_has_cover", "page1_has_mat133",
                      "body_starts_on_page2", "headings_found",
                      "full_marks", "scheme_heading"):
            if not check.get(field):
                failures.append(f"{key}: {field} false")
        if check.get("forbidden_tokens"):
            failures.append(f"{key}: forbidden {check['forbidden_tokens']}")
        if check.get("right_overflow"):
            failures.append(f"{key}: right overflow {check['right_overflow']}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", choices=["1", "2", "3", "all"], default="1")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--no-pdf", action="store_true")
    args = parser.parse_args()
    groups = [1, 2, 3] if args.group == "all" else [int(args.group)]
    all_failures = []
    for priority in groups:
        paper = make_paper(priority, args.seed)
        out_dir = OUT / f"group{priority}"
        result = build_bundle(
            paper, out_dir, stem=f"MAT133 P{priority} Generator Validation",
            export=not args.no_pdf)
        failures = check_result(result) if not args.no_pdf else []
        all_failures.extend(f"group{priority}: {f}" for f in failures)
        summary = {
            "group": priority,
            "questions": len(paper.questions),
            "parts": sum(len(q.parts) for q in paper.questions),
            "marks": paper.total_marks,
            "failures": failures,
            "paper_pages": result.get("paper_pages"),
            "scheme_pages": result.get("scheme_pages"),
            "paper_pdf_check": result.get("paper_pdf_check"),
            "scheme_pdf_check": result.get("scheme_pdf_check"),
        }
        (out_dir / "validation.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary, indent=2), flush=True)
    if all_failures:
        print("FAILURES:")
        for failure in all_failures:
            print(" -", failure)
        return 1
    print("All requested generator groups passed DOCX/XML/PDF validation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
