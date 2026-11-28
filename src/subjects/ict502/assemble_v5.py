"""V5 assembly for ICT502 seeds 1-3.

Five approved questions per seed, 20 marks each, 100 marks total.  Every
question is a real approved past-paper question; no question repeats inside a
seed, reuse is capped at four across the three seeds, and seeds prefer five
distinct source papers and broad topic coverage.

Run:
    uv run python -m src.subjects.ict502.assemble_v5 --seeds 1-3
"""
from __future__ import annotations

import argparse
import html
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import docx
import pymupdf
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.shared import Cm, Pt

import src.subjects.csc404.assemble_v5 as render
from src import config
from src.assemble.pdf_export import export_pdf
from src.bank.store import BankStore, load_json, save_json
from src.subjects.mat133.render_v5 import (
    _add_rich_text,
    _marks_line,
    _set_run_font,
)

SUBJECT = "ICT502"
TRACKING = config.TRACKING_DIR / "ict502"
BANK = TRACKING / "bank"
PAPER_TEMPLATE = config.subject_reference_dir("ICT502") / "ICT502 TEMPLATE.docx"
SCHEME_TEMPLATE = config.subject_reference_dir("ICT502") / "ICT502 SCHEME.docx"
OUT = config.PROJECT_ROOT / "outputs" / "review" / "ict502_v2" / "seeds"
CACHE = OUT / "_math"
ROLES = ("Q1", "Q2", "Q3", "Q4", "Q5")
REUSE_CAP = 4
TARGET_MARKS = 100
MIN_DISTINCT_PAPERS = 5

ROLE_TOPICS = {
    "Q1": ({"database_concepts", "data_warehouse", "file_system"},
           {"database_concepts", "data_warehouse"}),
    "Q2": ({"relational_model", "erd", "sql"},
           {"relational_model", "erd"}),
    "Q3": ({"transaction", "recovery", "concurrency_control"},
           {"transaction", "recovery"}),
    "Q4": ({"query_processing", "distributed_db"},
           {"distributed_db", "query_processing"}),
    "Q5": ({"database_development", "erd", "normalization", "data_warehouse"},
           {"database_development", "normalization"}),
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _questions() -> dict[str, dict]:
    store = BankStore(BANK)
    assets = {str(row["id"]): row for row in store.assets()}
    answers = store.answers_by_question()
    rows = {}
    for question in store.questions():
        if question.get("status") != "approved":
            continue
        question = dict(question)
        question["_assets"] = [
            assets[aid] for aid in question.get("assets") or []
            if aid in assets and assets[aid].get("verdict") == "approved"]
        question["_answer"] = answers.get(question["id"])
        rows[question["id"]] = question
    return rows


def _candidate_pool(role: str, questions: dict[str, dict]) -> list[str]:
    strong, weak = ROLE_TOPICS[role]
    strong_ids = [qid for qid, q in questions.items()
                  if set(q.get("topic_tags") or []) & strong
                  and (q.get("_answer") or {}).get("usable")]
    weak_ids = [qid for qid, q in questions.items()
                if set(q.get("topic_tags") or []) & weak
                and (q.get("_answer") or {}).get("usable")]
    if strong_ids:
        return strong_ids
    if weak_ids:
        return weak_ids
    return [qid for qid, q in questions.items()
            if (q.get("_answer") or {}).get("usable")]


def build_plans(seed_count: int = 3) -> list[dict]:
    questions = _questions()
    uses: Counter[str] = Counter()
    paper_uses: Counter[str] = Counter()
    previous: set[str] = set()
    used_any: set[str] = set()
    plans = []
    for seed in range(1, seed_count + 1):
        pools = {role: _candidate_pool(role, questions) for role in ROLES}
        best: list[tuple] = []

        def search(index: int, chosen: list[tuple[str, str]],
                   papers: set[str], topics: set[str]) -> None:
            if index == len(ROLES):
                if len(papers) < MIN_DISTINCT_PAPERS:
                    return
                score = (
                    len(topics),
                    len(papers),
                    -sum(uses[qid] for _, qid in chosen),
                    -len(previous & {qid for _, qid in chosen}),
                    tuple(qid for _, qid in chosen),
                )
                if not best or score > best[0][0]:
                    best[:] = [(score, list(chosen))]
                return
            role = ROLES[index]
            for qid in sorted(
                    pools[role],
                    key=lambda value: (
                        uses[value],
                        paper_uses[questions[value]["source_paper"]],
                        1 if value in previous else 0,
                        value)):
                question = questions.get(qid)
                if question is None:
                    continue
                if uses[qid] >= REUSE_CAP:
                    continue
                if qid in used_any:
                    continue
                if any(qid == chosen_id for _, chosen_id in chosen):
                    continue
                if str(question["source_paper"]) in papers:
                    continue
                search(index + 1,
                       chosen + [(role, qid)],
                       papers | {str(question["source_paper"])},
                       topics | set(question.get("topic_tags") or []))
                if best and len(best[0][1]) == len(ROLES):
                    # keep searching for a better score but bound the work
                    pass

        search(0, [], set(), set())
        if not best:
            break
        chosen = best[0][1]
        slots = []
        for role, qid in chosen:
            question = questions[qid]
            uses[qid] += 1
            paper_uses[str(question["source_paper"])] += 1
            slots.append({
                "slot": role,
                "question_id": qid,
                "marks": int(question.get("marks") or 0),
                "source_paper": question["source_paper"],
                "topic_tags": question.get("topic_tags") or [],
            })
        plans.append({
            "schema_version": 3,
            "subject": SUBJECT,
            "seed": seed,
            "slots": slots,
            "total_marks": sum(slot["marks"] for slot in slots),
            "distinct_papers": len({slot["source_paper"] for slot in slots}),
            "topic_coverage": sorted({topic for slot in slots
                                      for topic in slot["topic_tags"]}),
            "reuse_cap": REUSE_CAP,
        })
        previous = {qid for _, qid in chosen}
        used_any |= previous
    return plans


def _asset_visible_lines(asset: dict) -> set[str]:
    name = str(asset.get("owner_recreation_html") or "")
    if not name:
        return set()
    path = BANK / "review" / "owner_recreations" / name
    if not path.is_file():
        return set()
    raw = path.read_text(encoding="utf-8")
    raw = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    raw = re.sub(r"(?i)</t[dh]>", " | ", raw)
    raw = re.sub(r"(?i)</tr>", "\n", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    text = html.unescape(raw)
    return {" ".join(line.split()) for line in text.splitlines()
            if line.strip()}


def _stem_without_asset_duplicates(stem: str, assets: list[dict]) -> str:
    duplicate = set()
    for asset in assets:
        duplicate |= _asset_visible_lines(asset)
    kept = []
    for line in str(stem or "").splitlines():
        normalised = " ".join(line.split())
        if not normalised:
            kept.append(line)
            continue
        if normalised in duplicate:
            continue
        kept.append(line)
    return "\n".join(kept).strip()


def _asset_key(asset: dict) -> tuple[str, str]:
    text = " ".join([str(asset.get("label") or ""),
                     str(asset.get("caption") or "")])
    match = re.search(r"\b(Table|Figure)\s+(\d+(?:\.\d+)?)", text, re.I)
    if match:
        return match.group(1).title(), re.sub(r"\.0$", "", match.group(2))
    return "", ""


def _asset_matches_text(asset: dict, text: str) -> bool:
    kind, number = _asset_key(asset)
    if kind and re.search(
            rf"\b{kind}\s*{re.escape(number)}\b", text, re.I):
        return True
    label = str(asset.get("label") or "")
    if label and label.lower() in text.lower():
        return True
    caption = " ".join(str(asset.get("caption") or "").split())
    if caption:
        words = [word for word in re.findall(r"[A-Za-z]{4,}", caption)][:3]
        if words and all(word.lower() in text.lower() for word in words):
            return True
    return False


def _add_picture(doc, asset: dict, number: int) -> None:
    path = Path(str(asset.get("path") or ""))
    if not path.is_file():
        return
    try:
        from PIL import Image
        with Image.open(path) as image:
            width_px, height_px = image.size
        width_cm = 14.0
        height_cm = width_cm * height_px / max(1, width_px)
        if height_cm > 18.0:
            height_cm = 18.0
            width_cm = height_cm * width_px / max(1, height_px)
    except Exception:
        width_cm, height_cm = 14.0, None
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    if height_cm:
        p.add_run().add_picture(str(path), width=Cm(width_cm),
                                height=Cm(height_cm))
    else:
        p.add_run().add_picture(str(path), width=Cm(width_cm))
    label = str(asset.get("label") or asset.get("caption") or "").strip()
    if (not label or label == str(asset.get("id"))
            or label.startswith("A-ICT")
            or not re.match(r"^(Figure|Table)\s+\d", label, re.I)):
        return
    visible = _asset_visible_lines(asset)
    if visible and any(label.lower() in line.lower() for line in visible):
        return
    if not asset.get("owner_recreation_html"):
        # Original source crops usually include their printed caption.
        return
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_before = Pt(4)
    cap.paragraph_format.space_after = Pt(8)
    cap.paragraph_format.keep_together = True
    run = cap.add_run(label)
    _set_run_font(run, 8.5, italic=True)


def _add_question(doc, question: dict, number: int, cache: Path) -> None:
    heading = doc.add_paragraph()
    heading.paragraph_format.space_before = Pt(8)
    heading.paragraph_format.space_after = Pt(2)
    heading.paragraph_format.keep_with_next = True
    run = heading.add_run(f"QUESTION {number}")
    _set_run_font(run, 11, bold=True)
    parts = question.get("parts") or []
    assets = list(question.get("_assets") or [])
    stem = str(question.get("stem") or "")
    stem_lower = stem.lower()
    stem_assets = [asset for asset in assets
                   if _asset_matches_text(asset, stem)]
    if "schema" in stem_lower or "table" in stem_lower:
        for asset in assets:
            if asset in stem_assets:
                continue
            label = str(asset.get("label") or asset.get("caption") or "")
            if (asset.get("kind") == "table"
                    and (not label or label == str(asset.get("id"))
                         or label.startswith("A-ICT"))):
                stem_assets.append(asset)
            elif asset.get("kind") == "table" and "schema" in stem_lower:
                stem_assets.append(asset)
    stem = _stem_without_asset_duplicates(stem, stem_assets)
    stem = re.sub(r"\(\s*\d{1,3}\s*marks?\s*\)", "",
                  render._prep_text(stem), flags=re.I)
    if stem:
        render._para(doc, stem, cache=cache, key=question["id"], keep=True)
    for figure, asset in enumerate(stem_assets, start=1):
        _add_picture(doc, asset, figure)
    by_part: dict[int, list[dict]] = {}
    for asset in assets:
        if asset in stem_assets:
            continue
        target = None
        for index, part in enumerate(parts):
            if _asset_matches_text(asset, str(part.get("text") or "")):
                target = index
                break
        if target is None:
            for index, part in enumerate(parts):
                if re.search(r"\b(table|figure|schedule|timeline|schema"
                             r"|chart|diagram|graph|tree|cube)\b",
                             str(part.get("text") or ""), re.I):
                    target = index
                    break
        by_part.setdefault(target if target is not None else len(parts) - 1,
                           []).append(asset)
    for index, part in enumerate(parts):
        part = dict(part)
        part_assets = by_part.get(index, [])
        text = _stem_without_asset_duplicates(
            str(part.get("text") or ""), part_assets)
        text = re.sub(r"\(\s*\d{1,3}\s*marks?\s*\)", "",
                      render._prep_text(text), flags=re.I)
        part["text"] = text.strip()
        render._add_part_text_code(doc, part, cache, question["id"],
                                   str(part.get("label") or ""),
                                   keep_next=bool(part_assets))
        for figure, asset in enumerate(part_assets, start=1):
            _add_picture(doc, asset, figure)


SQL_RE = re.compile(
    r"\b(?:SELECT|FROM|WHERE|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|"
    r"JOIN|GROUP\s+BY|ORDER\s+BY|HAVING|VALUES|COMMIT|ROLLBACK|GRANT|"
    r"REVOKE|UNION|INTO|SET)\b", re.I)
SQL_START_RE = re.compile(
    r"^\s*(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|WITH)\b", re.I)
SQL_CONT_RE = re.compile(
    r"\b(?:FROM|WHERE|JOIN|GROUP\s+BY|ORDER\s+BY|HAVING|VALUES|SET|INTO|"
    r"ON|TABLE|COMMIT|ROLLBACK)\b", re.I)


def _is_code_line(line: str) -> bool:
    text = line.strip()
    if not text:
        return False
    if text.startswith((" ", "\t")) and re.search(r"[|+→⋈σπγ]", text):
        return True
    if text.endswith(";") and SQL_RE.search(text):
        return True
    start = SQL_START_RE.match(text)
    if start:
        rest = text[start.end():]
        if re.search(r"\w\.\w|[*()]", rest) or SQL_CONT_RE.search(rest):
            return True
    if text.endswith(";") and re.search(r"[=<>()]", text):
        return True
    return False


def _is_code_continuation(line: str) -> bool:
    text = line.strip()
    if not text:
        return True
    if text in {")", ");", ")", "}", "},", "};", "("}:
        return True
    if text.startswith((")", "}", ",")) or text.startswith(("    ", "\t")):
        return True
    if re.match(r"^(FROM|WHERE|JOIN|GROUP\s+BY|ORDER\s+BY|HAVING|"
                r"VALUES|SET|INTO|ON|AND|OR|AS|DISTINCT|UNION)\b",
                text, re.I):
        return True
    return False


def _add_answer_lines(doc, text: str, cache: Path, key: str,
                      label: str = "", size: float = 9.5) -> None:
    lines = str(text or "").splitlines() or [""]
    index = 0
    first = True
    while index < len(lines):
        line = lines[index]
        if _is_code_line(line):
            block = []
            while index < len(lines):
                candidate = lines[index]
                if not candidate.strip():
                    look = index + 1
                    while look < len(lines) and not lines[look].strip():
                        look += 1
                    if look < len(lines) and (
                            _is_code_line(lines[look])
                            or _is_code_continuation(lines[look])):
                        block.append("")
                        index += 1
                        continue
                    break
                if _is_code_line(candidate) or _is_code_continuation(
                        candidate):
                    block.append(candidate)
                    index += 1
                    continue
                break
            render._add_code_block(doc, block)
            first = False
            continue
        if line.strip():
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.5)
            p.paragraph_format.space_before = Pt(2 if first else 0)
            p.paragraph_format.space_after = Pt(0)
            if first and label:
                run = p.add_run(f"{label}) ")
                _set_run_font(run, 10, bold=True)
            _add_rich_text(p, render._prep_text(line), cache, key, size=size)
            first = False
        index += 1


def _add_scheme_question(doc, question: dict, number: int,
                         cache: Path) -> None:
    heading = doc.add_paragraph()
    heading.paragraph_format.space_before = Pt(8)
    heading.paragraph_format.space_after = Pt(2)
    heading.paragraph_format.keep_with_next = True
    run = heading.add_run(f"QUESTION {number}")
    _set_run_font(run, 11, bold=True)
    source = doc.add_paragraph()
    run = source.add_run(
        f"Source: {question['source_paper']}  |  "
        f"{question.get('marks')} marks  |  model_unofficial")
    _set_run_font(run, 8.5, italic=True)
    answer = question.get("_answer") or {}
    subparts = {str(row.get("label") or "").lower(): row
                for row in answer.get("subparts") or []}
    for part in question.get("parts") or []:
        label = str(part.get("label") or "")
        sub = subparts.get(label.lower()) or {}
        _add_answer_lines(doc, str(sub.get("answer") or "No answer."),
                          cache, question["id"], label=label)
        _marks_line(doc, int(part.get("marks") or 0))
        for line in sub.get("working") or []:
            _add_answer_lines(doc, str(line), cache, question["id"])
    points = answer.get("marking_points") or []
    if points:
        p = doc.add_paragraph()
        run = p.add_run(
            "Marking points"
            + (" (part allocation)" if answer.get("marking_points_source")
               == "part_allocation" else "") + ":")
        _set_run_font(run, 9, bold=True)
        for point in points:
            bp = doc.add_paragraph()
            bp.paragraph_format.left_indent = Cm(0.5)
            bp.paragraph_format.space_before = Pt(0)
            bp.paragraph_format.space_after = Pt(0)
            run = bp.add_run("• ")
            _set_run_font(run, 9)
            _add_rich_text(bp, str(point), cache, question["id"], size=9)


def _page_break(doc) -> None:
    paragraph = doc.add_paragraph()
    paragraph.add_run().add_break(WD_BREAK.PAGE)


def build_paper(plan: dict, out_dir: Path) -> Path:
    questions = _questions()
    target = out_dir / "paper.docx"
    document = docx.Document(str(PAPER_TEMPLATE))
    _page_break(document)
    for number, slot in enumerate(plan["slots"], start=1):
        _add_question(document, questions[slot["question_id"]], number, CACHE)
    document.save(str(target))
    return target


def build_scheme(plan: dict, out_dir: Path) -> Path:
    questions = _questions()
    target = out_dir / "scheme.docx"
    document = docx.Document(str(SCHEME_TEMPLATE))
    _page_break(document)
    for number, slot in enumerate(plan["slots"], start=1):
        _add_scheme_question(document, questions[slot["question_id"]],
                             number, CACHE)
    document.save(str(target))
    return target


def _set_page_count(path: Path, marker: str, pages: int) -> bool:
    document = docx.Document(str(path))
    changed = False
    for paragraph in document.paragraphs:
        if marker in paragraph.text:
            paragraph.text = f"{marker} {pages} printed pages"
            changed = True
            break
    if changed:
        document.save(str(path))
    return changed


def qa_seed(plan: dict, out_dir: Path) -> dict:
    questions = _questions()
    problems = []
    slots = plan.get("slots") or []
    if len(slots) != 5:
        problems.append(f"expected 5 slots, found {len(slots)}")
    if len({row["question_id"] for row in slots}) != len(slots):
        problems.append("question repeated inside the seed")
    if len({row["source_paper"] for row in slots}) < MIN_DISTINCT_PAPERS:
        problems.append("fewer than five distinct source papers")
    total = sum(int(row.get("marks") or 0) for row in slots)
    if total != TARGET_MARKS:
        problems.append(f"marks total {total}, expected {TARGET_MARKS}")
    for row in slots:
        question = questions.get(row["question_id"])
        if question is None:
            problems.append(f"{row['question_id']} is missing")
            continue
        if question.get("status") != "approved":
            problems.append(f"{row['question_id']} is not approved")
        if not (question.get("_answer") or {}).get("usable"):
            problems.append(f"{row['question_id']} has no usable answer")
        if int(question.get("marks") or 0) != int(row["marks"]):
            problems.append(f"{row['question_id']} mark mismatch")
        if sum(int(part.get("marks") or 0)
               for part in question.get("parts") or []) != int(
                   question.get("marks") or 0):
            problems.append(f"{row['question_id']} part marks do not sum")
    paper = out_dir / "paper.docx"
    scheme = out_dir / "scheme.docx"
    for path in (paper, scheme):
        if not path.is_file():
            problems.append(f"{path.name} is missing")
    if paper.is_file():
        xml = docx.Document(str(paper)).element.xml
        if xml.count("QUESTION ") < 5:
            problems.append("paper has fewer than 5 QUESTION headings")
    if scheme.is_file():
        xml = docx.Document(str(scheme)).element.xml
        if "model_unofficial" not in xml:
            problems.append("scheme lacks the model_unofficial label")
    paper_pdf = out_dir / "paper.pdf"
    scheme_pdf = out_dir / "scheme.pdf"
    for path in (paper_pdf, scheme_pdf):
        if not path.is_file():
            continue
        with pymupdf.open(str(path)) as pdf:
            text = "\n".join(page.get_text() for page in pdf)
            if text.count("QUESTION ") < 5:
                problems.append(f"{path.name} has fewer than 5 questions")
            if path == paper_pdf and "model_unofficial" in text:
                problems.append("paper leaks the model provenance label")
            if path == scheme_pdf and "Marking points" not in text:
                problems.append("scheme has no marking points")
            for page_number, page in enumerate(pdf, start=1):
                width, height = page.rect.width, page.rect.height
                for block in page.get_text("blocks"):
                    x0, y0, x1, y1 = block[:4]
                    if x1 > width - 12 or y1 > height - 12:
                        problems.append(
                            f"{path.name} page {page_number} has text "
                            "outside the printable area")
                        break
    if paper.is_file():
        document = docx.Document(str(paper))
        expected_assets = sum(len(questions[row["question_id"]].get(
            "_assets") or []) for row in slots)
        if len(document.inline_shapes) < expected_assets:
            problems.append(
                f"paper inserted {len(document.inline_shapes)} images for "
                f"{expected_assets} assets")
    return {
        "seed": plan["seed"],
        "slots": len(slots),
        "total_marks": total,
        "distinct_papers": len({row["source_paper"] for row in slots}),
        "topic_coverage": plan.get("topic_coverage") or [],
        "problems": problems,
    }


def build_seed(seed: int, out_dir: Path | None = None) -> dict:
    plans = build_plans(seed_count=seed)
    if len(plans) < seed:
        raise ValueError(f"only {len(plans)} seeds are feasible")
    plan = plans[seed - 1]
    target = Path(out_dir) if out_dir else OUT / f"seed_{seed:02d}"
    target.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    save_json(target / "plan.json", plan)
    paper = build_paper(plan, target)
    scheme = build_scheme(plan, target)
    paper_pdf = target / "paper.pdf"
    scheme_pdf = target / "scheme.pdf"
    export_pdf(paper, paper_pdf)
    paper_pages = len(pymupdf.open(str(paper_pdf)))
    if _set_page_count(paper, "This examination paper consists of",
                       paper_pages):
        export_pdf(paper, paper_pdf)
        paper_pages = len(pymupdf.open(str(paper_pdf)))
    export_pdf(scheme, scheme_pdf)
    scheme_pages = len(pymupdf.open(str(scheme_pdf)))
    if _set_page_count(scheme, "This marking scheme consists of",
                       scheme_pages):
        export_pdf(scheme, scheme_pdf)
        scheme_pages = len(pymupdf.open(str(scheme_pdf)))
    qa = qa_seed(plan, target)
    save_json(target / "qa.json", qa)
    meta = {
        "subject": SUBJECT,
        "seed": seed,
        "mode": "recycle",
        "model": "ict502-v3-role-recycle",
        "cost_usd": 0.0,
        "accepted": len(plan["slots"]),
        "placeholders": 0,
        "total_slots": len(plan["slots"]),
        "total_marks": plan["total_marks"],
        "has_practice_mode": False,
        "has_placeholders": False,
        "created": _now(),
        "year": 2026,
        "topic_marks": {},
        "summary": {"total_marks": plan["total_marks"]},
        "files": {
            "paper_docx": str(paper),
            "paper_pdf": str(paper_pdf),
            "scheme_docx": str(scheme),
            "scheme_pdf": str(scheme_pdf),
        },
    }
    save_json(target / "meta.json", meta)
    save_json(target / "evidence.json", {
        "plan": plan,
        "qa": qa,
        "paper_pages": paper_pages,
        "scheme_pages": scheme_pages,
    })
    return {"seed": seed, "path": str(target), "qa": qa,
            "paper_pages": paper_pages,
            "scheme_pages": scheme_pages}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", default="1-3")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    if "-" in args.seeds:
        first, last = args.seeds.split("-", 1)
        seeds = list(range(int(first), int(last) + 1))
    else:
        seeds = [int(value) for value in args.seeds.split(",")]
    results = [build_seed(seed, args.out) for seed in seeds]
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
