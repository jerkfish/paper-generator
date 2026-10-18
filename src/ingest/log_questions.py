"""Step 3 - Log questions.

For every paper (excluding byte-identical "(2)" copies): extract the text
(text layer, or full Windows OCR for scans - cached), split it into question
blocks with code, ask the LLM to propose per-question/sub-part labels while
quoting the ORIGINAL wording verbatim, verify the quotes against the source
text, and write the "Questions" sheet plus a per-paper "Paper marks check"
sheet (computed sum vs official total; mismatches are listed, not hidden).

Run:  uv run python -m src.ingest.log_questions [--only all|text|scanned]
"""
from __future__ import annotations

import argparse
import pathlib
import re

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font
from openpyxl.worksheet.datavalidation import DataValidation
from pydantic import ValidationError

from src import config
from src.ingest import ocr as ocr_mod
from src.ingest.models import PaperQuestions
from src.llm import chat_json

QUESTION_LINE_PAT = re.compile(r"^\s*QUESTION\s+(\d+)\b", re.I)
PART_LINE_PAT = re.compile(r"^\s*(PART\s+([AB]))\b", re.I)
MARKS_PAT = re.compile(r"\((\d+(?:\.\d+)?)\s*marks?\)", re.I)

QUESTION_TYPES = [
    "Objective (MCQ)", "Short answer", "Explanation/Theory", "Calculation",
    "Diagram/Label", "Case study", "Comparison/Discussion", "Other",
]
OCR_MARKERS = [
    re.compile(r"UNIVERSITI", re.I), re.compile(r"\bCSC\s*662\b", re.I),
    re.compile(r"QUESTION", re.I), re.compile(r"MARK", re.I),
]

QUESTIONS_HEADERS = [
    "Paper ID", "Q no.", "Sub-part", "Topic", "Question type", "Marks",
    "Has diagram", "Diagram type", "Machine-verifiable", "Wording note",
    "Original question text", "Confidence",
]
CHECK_HEADERS = ["Paper ID", "Official total", "Computed sum", "Status", "Note"]

SYSTEM_PROMPT = f"""You label past-exam questions. You receive one exam paper split into question blocks.
For every question block, split it into sub-parts (a, b, c... or i, ii...) ONLY when each
sub-part carries its own marks; otherwise one row for the whole question.
Copy the question text VERBATIM from the block into original_text - do not paraphrase,
repair spelling, or translate. Keep every mark figure exactly as printed.
Output exactly one JSON object with this shape:
{{"questions": [{{"q_no": "1", "sub_part": "a", "original_text": "...verbatim...",
"marks": 10, "topic": "short topic e.g. RSA, access control, DES",
"question_type": "one of: {", ".join(QUESTION_TYPES)}",
"has_diagram": false, "diagram_type": "", "machine_verifiable": "Y",
"wording_note": "short note on phrasing style (e.g. 'state and justify')"}}]}}
Rules: q_no is the block number. sub_part is "" for a whole question. marks is a number
or null when no marks are printed for that row. machine_verifiable is "Y" when a program
could compute the exact answer (cipher steps, numeric crypto, fixed-fact MCQ), "Partial"
when only part is computable, "N" for essays/opinions. has_diagram true only if the paper
shows a figure/table/diagram inside this question."""


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", s)


def _full_text(path: pathlib.Path) -> str:
    from pypdf import PdfReader

    parts = []
    try:
        for page in PdfReader(str(path)).pages:
            try:
                parts.append(page.extract_text() or "")
            except Exception:
                pass
    except Exception:
        return ""
    return "\n".join(parts)


def _split_blocks(text: str) -> list[tuple[str, str]]:
    """Split paper text into (q_no, block) pairs, tracking Part A/B where present."""
    has_parts = bool(PART_LINE_PAT.search(text))
    blocks: list[tuple[str, str]] = []
    cur_q: str | None = None
    cur_part = ""
    buf: list[str] = []

    def flush() -> None:
        if cur_q is not None:
            blocks.append((cur_q, "\n".join(buf)))
            buf.clear()

    for line in text.splitlines():
        pm = PART_LINE_PAT.match(line)
        if pm:
            flush()
            cur_part = pm.group(2).upper()
            buf.append(line)
            continue
        qm = QUESTION_LINE_PAT.match(line)
        if qm:
            flush()
            cur_q = (cur_part if has_parts and cur_part else "") + qm.group(1)
        buf.append(line)
    flush()
    if not blocks:  # no "QUESTION n" markers found - hand the whole text to the LLM
        blocks = [("?", text)]
    return blocks


def _block_marks(block: str) -> float | None:
    values = [float(m) for m in MARKS_PAT.findall(block)]
    return sum(values) if values else None


def _label_paper(pid: str, blocks: list[tuple[str, str]]) -> list[dict]:
    """One LLM call per paper: label every block at once."""
    parts = [f"=== QUESTION BLOCK {q_no} ===\n{block[:2500]}" for q_no, block in blocks]
    user = f"Paper {pid}.\n\n" + "\n\n".join(parts)
    try:
        data = chat_json(SYSTEM_PROMPT, user)
        parsed = PaperQuestions(paper_id=pid, questions=data.get("questions", []))
        return [q.model_dump() for q in parsed.questions]
    except (ValidationError, RuntimeError, KeyError) as e:
        print(f"    !! LLM label failed for {pid}: {e}", flush=True)
        return []


def _verify_block(block: str, rows: list[dict]) -> tuple[list[dict], bool]:
    """Check quotes against source; fall back to a whole-block row on failure."""
    norm_block = _norm(block)
    quoted_chars = 0
    all_ok = True
    for row in rows:
        q = _norm(str(row["original_text"]))
        if q and q in norm_block:
            quoted_chars += len(q)
        else:
            all_ok = False
    coverage = quoted_chars / max(len(norm_block), 1)
    if all_ok and coverage >= 0.6:
        return rows, True
    # verbatim check failed - keep the block as one row, labels unreliable
    return [{
        "q_no": rows[0]["q_no"] if rows else "?",
        "sub_part": "",
        "original_text": block.strip(),
        "marks": _block_marks(block),
        "topic": "unsure",
        "question_type": "Other",
        "has_diagram": False,
        "diagram_type": "",
        "machine_verifiable": "N",
        "wording_note": "verbatim check failed; whole block stored",
    }], False


def _load_papers() -> list[dict]:
    ws = load_workbook(config.TRACKING_XLSX)["Papers"]
    headers = [c.value for c in ws[1]]
    rows = [dict(zip(headers, row)) for row in ws.iter_rows(min_row=2, values_only=True)]
    return [r for r in rows if not str(r["Paper ID"]).endswith("-copy")]


def _paper_text(pid: str, file_name: str) -> tuple[str, str]:
    path = config.PAPERS_DIR / file_name
    text = _full_text(path)
    if len(text) >= 200:
        return text, "text layer"
    cache = config.OCR_CACHE_DIR / f"{pid}.txt"
    log = lambda m: print(m, flush=True)
    return ocr_mod.ocr_pdf(path, OCR_MARKERS, cache_path=cache, log=log), "OCR (cached)"


def _write_sheets(question_rows: list[dict], checks: list[dict]) -> None:
    wb = load_workbook(config.TRACKING_XLSX)

    def existing(sheet: str) -> list[dict]:
        if sheet not in wb.sheetnames:
            return []
        ws = wb[sheet]
        headers = [c.value for c in ws[1]]
        return [dict(zip(headers, row)) for row in ws.iter_rows(min_row=2, values_only=True)]

    # merge: keep rows of papers not processed in this run
    seen_q = {r["Paper ID"] for r in question_rows}
    question_rows = [r for r in existing("Questions") if r["Paper ID"] not in seen_q] + question_rows
    seen_c = {r["Paper ID"] for r in checks}
    checks = [r for r in existing("Paper marks check") if r["Paper ID"] not in seen_c] + checks

    def qkey(r: dict):
        m = re.search(r"\d+", str(r["Q no."]))
        return (r["Paper ID"], int(m.group()) if m else 10**6, str(r["Q no."]))

    question_rows.sort(key=qkey)
    checks.sort(key=lambda r: r["Paper ID"])

    for sheet in ("Questions", "Paper marks check"):
        if sheet in wb.sheetnames:
            del wb[sheet]
    ws = wb.create_sheet("Questions")
    ws.append(QUESTIONS_HEADERS)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for row in question_rows:
        ws.append([row[h] for h in QUESTIONS_HEADERS])
    widths = [16, 6, 8, 26, 20, 7, 12, 14, 18, 34, 80, 28]
    for col, width in zip("ABCDEFGHIJKL", widths):
        ws.column_dimensions[col].width = width
    dv = DataValidation(type="list", formula1='"' + ",".join(QUESTION_TYPES) + '"',
                        allow_blank=True)
    dv.add(f"E2:E{ws.max_row}")
    ws.add_data_validation(dv)

    wc = wb.create_sheet("Paper marks check")
    wc.append(CHECK_HEADERS)
    for cell in wc[1]:
        cell.font = Font(bold=True)
    for row in checks:
        wc.append([row[h] for h in CHECK_HEADERS])
    for col, width in zip("ABCDE", (16, 14, 13, 42, 60)):
        wc.column_dimensions[col].width = width
    wb.save(config.TRACKING_XLSX)


def process_papers(papers: list[dict], tag: str) -> tuple[list[dict], list[dict]]:
    question_rows: list[dict] = []
    checks: list[dict] = []
    for paper in papers:
        pid = paper["Paper ID"]
        file_name = paper["File name"]
        official = paper["Official total marks"]
        official_int = official if isinstance(official, int) else None
        print(f"[{tag}] {pid} ({file_name})", flush=True)
        text, source = _paper_text(pid, file_name)
        conf = "LLM-proposed labels (unverified)" if source == "text layer" \
            else "LLM-proposed labels on OCR text (unverified)"
        blocks = _split_blocks(text)
        print(f"    {len(blocks)} blocks, labelling via LLM...", flush=True)
        by_q: dict[str, list[dict]] = {}
        for row in _label_paper(pid, blocks):
            by_q.setdefault(str(row["q_no"]), []).append(row)
        regex_total = 0.0
        known = 0.0
        any_unknown = False
        for q_no, block in blocks:
            bm = _block_marks(block)
            if bm is not None:
                regex_total += bm
            rows, ok = _verify_block(block, by_q.get(q_no, []))
            if not ok:
                print(f"    !! verbatim check failed for Q{q_no} - stored whole block",
                      flush=True)
            for row in rows:
                if row["marks"] is None:
                    any_unknown = True
                else:
                    known += float(row["marks"])
                question_rows.append({
                    "Paper ID": pid, "Q no.": row["q_no"], "Sub-part": row["sub_part"],
                    "Topic": row["topic"], "Question type": row["question_type"],
                    "Marks": row["marks"], "Has diagram": row["has_diagram"],
                    "Diagram type": row["diagram_type"],
                    "Machine-verifiable": row["machine_verifiable"],
                    "Wording note": row["wording_note"],
                    "Original question text": row["original_text"], "Confidence": conf,
                })
        if official_int is not None:
            if not any_unknown and abs(known - official_int) < 0.01:
                status, note = "match", f"logged {known} == official {official_int}"
            else:
                extra = " (+ some rows without printed marks)" if any_unknown else ""
                status = "mismatch"
                note = f"official {official_int} vs logged {known}{extra}"
        else:
            status = "official total unsure"
            extra = " (+ some rows without printed marks)" if any_unknown else ""
            note = f"computed sum = {known}{extra}"
        if abs(regex_total - known) >= 0.01:
            note += f"; regex-found marks total {regex_total}"
        checks.append({"Paper ID": pid, "Official total": official,
                       "Computed sum": known, "Status": status, "Note": note})
        print(f"    {len(blocks)} blocks, logged {known} marks ({status})", flush=True)
    return question_rows, checks


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["all", "text", "scanned"], default="all")
    args = ap.parse_args()

    papers = _load_papers()
    if args.only == "text":
        papers = [p for p in papers if len(_full_text(config.PAPERS_DIR / p["File name"])) >= 200]
    elif args.only == "scanned":
        papers = [p for p in papers if len(_full_text(config.PAPERS_DIR / p["File name"])) < 200]
    print(f"logging questions for {len(papers)} papers ({args.only})")
    q_rows, checks = process_papers(papers, args.only)
    _write_sheets(q_rows, checks)
    print(f"\nwrote {len(q_rows)} question rows and {len(checks)} check rows -> "
          f"{config.TRACKING_XLSX}")


if __name__ == "__main__":
    main()
