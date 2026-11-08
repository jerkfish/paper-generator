"""P1: build the asset-first CSC429 bank from source papers and layout.

The extractor is deterministic.  It reads the preserved page/layout/OCR cache,
never the archived question bank, planner, generators or rejected seeds.  It
writes the data contracts under ``data/tracking/csc429/bank/``:

  questions/<QID>.json
  assets/<AID>.png
  assets/<AID>.json
  corrections.json
  approvals.json
  unsure.json / unsure.md
  index.json

Run:
    uv run python -m src.subjects.csc429.pure_bank
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from collections import Counter
from pathlib import Path

from src import config
from src.subjects.csc429 import pure_config, tables

SUBJECT = "CSC429"
TRACKING = config.TRACKING_DIR / "csc429"
RAW_ASSETS = TRACKING / "assets"
BANK = TRACKING / "bank"
QUESTIONS = BANK / "questions"
ASSETS = BANK / "assets"

TOPIC_RULES: list[tuple[str, re.Pattern]] = [
    ("data_representation", re.compile(
        r"\b(binary|hex(adecimal)?|decimal|ieee|floating.?point|"
        r"complement|sign and magnitude|bit|byte|base|octal)\b", re.I)),
    ("assembly_programming", re.compile(
        r"\b(assembly|machine instruction|opcode|program|addressing mode|"
        r"register|instruction)\b", re.I)),
    ("memory_system", re.compile(
        r"\b(cache|dram|sram|memory|mapping|virtual memory|page)\b", re.I)),
    ("io_system", re.compile(
        r"\b(interrupt|i/o|input|output|dma|interface|usb|bus|"
        r"external device)\b", re.I)),
    ("parallel_architecture", re.compile(
        r"\b(pipeline|parallel|multiprocessor|numa|smp|sisd|simd|mimd|"
        r"taxonomy|multiple processor)\b", re.I)),
    ("instruction_set_addressing", re.compile(
        r"\b(addressing|opcode|instruction format|immediate|direct|"
        r"indirect|register indirect)\b", re.I)),
    ("computer_generations", re.compile(
        r"\b(generation|vacuum|transistor|integrated circuit|microprocessor|"
        r"mechanical|calculator|eniac|edsac|abc|difference engine)\b", re.I)),
    ("computer_architecture", re.compile(
        r"\b(von neumann|architecture|machine cycle|register|control unit|"
        r"alu|instruction cycle|system interconnection)\b", re.I)),
]
TOPIC_ORDER = [name for name, _ in TOPIC_RULES]
DIAGRAM_WORDS = re.compile(
    r"\b(diagram|architecture|taxonomy|interrupt|pipeline|cycle|"
    r"sisd|simd|mimd|numa|smp|memory|cache|bus|network|flow)\b", re.I)
PICTURE_WORDS = re.compile(
    r"\b(photo|photograph|portrait|inventor|snippet|excerpt|web page|"
    r"newspaper|icon|logo|image)\b", re.I)
FORMULA_WORDS = re.compile(r"\b(formula|equation|expression)\b", re.I)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _save(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def _norm(text: str) -> str:
    return " ".join(str(text or "").split())


def _rel(path: Path) -> str:
    return path.relative_to(config.PROJECT_ROOT).as_posix()


def classify_topics(text: str) -> list[str]:
    scores = {}
    for name, pattern in TOPIC_RULES:
        score = len(pattern.findall(text or ""))
        if score:
            scores[name] = score
    return sorted(scores, key=lambda name: (-scores[name],
                                            TOPIC_ORDER.index(name)))


def _asset_kind(raw: dict, question_text: str) -> str:
    if str(raw.get("kind", "")).lower() == "table":
        return "table"
    caption = str(raw.get("caption", ""))
    label = str(raw.get("label", ""))
    text = f"{caption} {label} {question_text}"
    if FORMULA_WORDS.search(text):
        return "formula"
    if DIAGRAM_WORDS.search(text):
        return "diagram"
    if PICTURE_WORDS.search(text):
        return "picture"
    return "figure"


def _question_topic(question: dict) -> tuple[list[str], str]:
    text = " ".join([
        str(question.get("text", "")),
        " ".join(str(part.get("text", ""))
                 for part in question.get("subparts") or []),
    ])
    if question.get("part") == "B":
        return ["assembly_programming"], "assembly_programming"
    tags = classify_topics(text)
    if not tags:
        tags = ["computer_architecture"]
    return tags, tags[0]


def _layout_index() -> dict[str, dict]:
    index = {}
    for path in sorted((TRACKING / "layout").glob("*.json")):
        payload = _load(path, {})
        if isinstance(payload, dict) and payload.get("paper_id"):
            index[payload["paper_id"]] = payload
    return index


def _page(layout: dict, page_no: int) -> dict:
    pages = layout.get("pages") or []
    if 1 <= int(page_no) <= len(pages):
        return pages[int(page_no) - 1]
    return {}


def _native_table(raw: dict, layout: dict) -> dict | None:
    if str(raw.get("kind", "")).lower() != "table":
        return None
    page = _page(layout, int(raw.get("page", 0)))
    if not page:
        return None
    try:
        return tables.extract_table(raw, page)
    except Exception:
        return None


def _asset_record(raw: dict, question_text: str, layout: dict | None,
                  seen_hashes: dict[str, str]) -> dict:
    source = config.PROJECT_ROOT / str(raw.get("path", ""))
    if not source.is_file():
        raise RuntimeError(f"missing source crop: {source}")
    aid = str(raw["asset_id"])
    target = ASSETS / f"{aid}.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists() or _sha256_file(target) != _sha256_file(source):
        shutil.copy2(source, target)
    digest = _sha256_file(target)
    if digest in seen_hashes and seen_hashes[digest] != aid:
        duplicate_of = seen_hashes[digest]
    else:
        duplicate_of = ""
    seen_hashes.setdefault(digest, aid)
    kind = _asset_kind(raw, question_text)
    native = _native_table(raw, layout or {})
    treatment = "crop"
    return {
        "id": aid,
        "question_ids": [],
        "source_paper": raw.get("paper_id", ""),
        "source_file": raw.get("source_file", ""),
        "page": int(raw.get("page", 0)),
        "label": raw.get("label", ""),
        "caption": raw.get("caption", ""),
        "kind": kind,
        "bbox": raw.get("bbox_pdf") or raw.get("content_bbox") or [],
        "content_bbox": raw.get("content_bbox") or raw.get("bbox_pdf") or [],
        "caption_bbox": raw.get("caption_bbox"),
        "path": _rel(target),
        "sha256": digest,
        "width_px": int(raw.get("width_px", 0)),
        "height_px": int(raw.get("height_px", 0)),
        "dpi": int(raw.get("dpi", 300)),
        "treatment": treatment,
        "native_table": native,
        "compare": {"status": "pending", "method": "not_run"},
        "verdict": "pending",
        "duplicate_of": duplicate_of,
        "review_flags": list(raw.get("review_flags") or []),
    }


def _question_record(question: dict, raw_assets: dict[str, dict],
                     asset_records: dict[str, dict],
                     layouts: dict[str, dict], paper: dict) -> dict:
    qid = str(question["question_id"])
    paper_id = str(question["paper_id"])
    layout = layouts.get(paper_id)
    refs = [str(value) for value in question.get("figure_refs") or []]
    asset_ids = [str(value) for value in question.get("asset_ids") or []]
    topic_tags, topic_primary = _question_topic(question)
    text = _norm(question.get("text", ""))
    subparts = []
    for part in question.get("subparts") or []:
        subparts.append({
            "label": part.get("label", ""),
            "text": _norm(part.get("text", "")),
            "marks": part.get("marks"),
            "marks_source": part.get("marks_source", ""),
            "bbox": part.get("bbox"),
        })
    linked_assets = []
    integrity = []
    for aid in asset_ids:
        raw = raw_assets.get(aid)
        if raw is None:
            integrity.append(f"asset {aid} is not in the asset manifest")
            continue
        if str(raw.get("paper_id", "")) != paper_id:
            integrity.append(
                f"asset {aid} belongs to {raw.get('paper_id')}, not {paper_id}")
        if aid in asset_records:
            linked_assets.append(asset_records[aid])
    labels = {str(asset.get("label", "")).lower() for asset in linked_assets}
    dangling = [ref for ref in refs
                if ref.lower() not in labels and not any(
                    ref.lower() == str(part.get("label", "")).lower()
                    for part in linked_assets)]
    if dangling:
        integrity.append("dangling reference: " + ", ".join(dangling))
    flags = list(question.get("review_flags") or [])
    if paper.get("source_kind") == "ocr":
        flags.append("ocr_source")
    status = "needs_fix" if integrity else "extracted"
    native_tables = {}
    for asset in linked_assets:
        if asset.get("kind") == "table" and asset.get("native_table"):
            native_tables[asset["id"]] = asset["native_table"]
    content_hash = _sha256_bytes(json.dumps({
        "text": text,
        "marks": question.get("marks"),
        "subparts": subparts,
        "refs": refs,
        "assets": [asset.get("sha256") for asset in linked_assets],
    }, sort_keys=True, ensure_ascii=False).encode("utf-8"))
    record = {
        "id": qid,
        "source_paper": paper_id,
        "source_file": question.get("source_file", ""),
        "pages": question.get("pages") or [],
        "part": question.get("part", ""),
        "question_no": question.get("question_no"),
        "slot": question.get("slot", ""),
        "marks": int(question.get("marks") or 0),
        "marks_source": question.get("marks_source", ""),
        "subpart_marks": [
            {"label": part["label"], "marks": part["marks"],
             "marks_source": part["marks_source"]}
            for part in subparts
        ],
        "native_text_blocks": [{
            "kind": ("ocr" if "ocr_source" in flags else "text"),
            "text": question.get("text", ""),
            "normalised": text,
            "spans": question.get("source_spans") or [],
        }],
        "native_tables": native_tables,
        "refs": refs,
        "assets": [asset["id"] for asset in linked_assets],
        "topic_tags": topic_tags,
        "topic_primary": topic_primary,
        "status": status,
        "content_hash": content_hash,
        "notes": "; ".join(integrity),
        "review_flags": sorted(set(flags)),
    }
    for asset in linked_assets:
        if qid not in asset["question_ids"]:
            asset["question_ids"].append(qid)
    return record


def build() -> dict:
    BANK.mkdir(parents=True, exist_ok=True)
    QUESTIONS.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)
    pure_config.ensure()

    bank_draft = _load(TRACKING / "question_bank_draft.json", {})
    manifest = _load(RAW_ASSETS / "manifest.json", {})
    register = _load(TRACKING / "papers_register.json", [])
    layouts = _layout_index()
    paper_index = {str(row.get("source", "")): row for row in register}
    raw_assets = {str(row["asset_id"]): row
                  for row in manifest.get("assets", [])}
    questions = bank_draft.get("questions") or []
    if not questions:
        raise RuntimeError("no extracted questions; run the extractor first")
    if not raw_assets:
        raise RuntimeError("no extracted assets; run the extractor first")

    # Preserve human decisions across re-extraction.
    old_questions = {path.stem: _load(path, {})
                     for path in QUESTIONS.glob("*.json")}
    old_assets = {path.stem: _load(path, {})
                  for path in ASSETS.glob("*.json")}
    previous_approvals = _load(BANK / "approvals.json", {}).get("by_qid", {})
    # Clear only generated question/asset records; never touch corrections or
    # approvals.
    for old in QUESTIONS.glob("*.json"):
        old.unlink()
    for old in ASSETS.glob("*.json"):
        old.unlink()

    asset_records: dict[str, dict] = {}
    seen_hashes: dict[str, str] = {}
    layout_by_qid_text: dict[str, str] = {}
    for question in questions:
        layout_by_qid_text[str(question["question_id"])] = str(
            question.get("text", ""))
    for aid, raw in raw_assets.items():
        layout = layouts.get(str(raw.get("paper_id", "")))
        record = _asset_record(
            raw, layout_by_qid_text.get("", ""), layout, seen_hashes)
        asset_records[aid] = record

    question_records = []
    for question in questions:
        paper_id = str(question["paper_id"])
        paper = paper_index.get(str(question.get("source_file", "")), {})
        record = _question_record(
            question, raw_assets, asset_records, layouts, paper)
        old = old_questions.get(record["id"])
        approval = previous_approvals.get(record["id"])
        if old and old.get("content_hash") == record["content_hash"]:
            if old.get("status") in {"approved", "rejected", "needs_fix"}:
                record["status"] = old["status"]
            if old.get("notes"):
                record["notes"] = old["notes"]
        elif approval and old:
            record["review_flags"] = sorted(set(
                record.get("review_flags", []) + ["stale_approval"]))
            record["notes"] = (
                (record.get("notes", "") + "; " if record.get("notes") else "")
                + "previous approval hash does not match re-extracted content")
        question_records.append(record)

    # Write question and asset records.
    for question in question_records:
        _save(QUESTIONS / f"{question['id']}.json", question)
    for asset in asset_records.values():
        old = old_assets.get(asset["id"])
        if old and old.get("sha256") == asset.get("sha256"):
            for key in ("treatment", "compare", "verdict", "verdict_note"):
                if key in old:
                    asset[key] = old[key]
        _save(ASSETS / f"{asset['id']}.json", asset)

    # Preserve human decisions across re-extraction.
    corrections = BANK / "corrections.json"
    approvals = BANK / "approvals.json"
    if not corrections.exists():
        _save(corrections, {"schema_version": 1, "by_qid": {}})
    if not approvals.exists():
        _save(approvals, {"schema_version": 1, "by_qid": {}})

    unsure = []
    for item in bank_draft.get("unsure") or []:
        qid = str(item.get("question_id", ""))
        record = next((row for row in question_records
                       if row["id"] == qid), {})
        unsure.append({
            "kind": "question",
            "question_id": qid,
            "paper_id": item.get("paper_id", ""),
            "pages": record.get("pages", []),
            "code": item.get("code", ""),
            "detail": item.get("detail", ""),
            "path": f"bank/questions/{qid}.json" if qid else "",
            "blocking": True,
        })
    for item in manifest.get("unresolved") or []:
        unsure.append({
            "kind": "reference",
            "question_id": "",
            "paper_id": item.get("paper_id", ""),
            "pages": [item.get("page")],
            "code": "unresolved_reference",
            "detail": f"{item.get('label')}: {item.get('reason')}",
            "path": str(item.get("page_image", "")),
            "blocking": True,
        })
    unsure.append({
        "kind": "template",
        "question_id": "",
        "paper_id": "",
        "pages": [],
        "code": "template_identity",
        "detail": (
            "No file named scheme_updated.docx was found. Using the accepted "
            "experiment scheme_template.docx; confirm its cover and box "
            "offsets are the intended standard."),
        "path": "data/tracking/csc429/templates/scheme_template.docx",
        "blocking": True,
    })
    for question in question_records:
        for note in (question.get("notes") or "").split("; "):
            if not note:
                continue
            if note.startswith("dangling reference") or "belongs to" in note:
                unsure.append({
                    "kind": "question_integrity",
                    "question_id": question["id"],
                    "paper_id": question["source_paper"],
                    "pages": question.get("pages", []),
                    "code": "integrity",
                    "detail": note,
                    "path": f"bank/questions/{question['id']}.json",
                    "blocking": True,
                })
    _save(BANK / "unsure.json", {
        "schema_version": 1,
        "subject": SUBJECT,
        "count": len(unsure),
        "items": unsure,
    })
    lines = ["# CSC429 P1 unsure items", ""]
    for item in unsure:
        lines.append(
            f"- **{item['code']}** — {item['paper_id']} "
            f"p{item.get('pages')} — {item['detail']} — `{item['path']}`")
    (BANK / "unsure.md").write_text("\n".join(lines) + "\n",
                                    encoding="utf-8")

    topic_counts = Counter(row["topic_primary"] for row in question_records)
    status_counts = Counter(row["status"] for row in question_records)
    kind_counts = Counter(row["kind"] for row in asset_records.values())
    summary = {
        "schema_version": 1,
        "subject": SUBJECT,
        "papers": len({row["source_paper"] for row in question_records}),
        "questions": len(question_records),
        "subparts": sum(len(row["subpart_marks"]) for row in question_records),
        "questions_with_assets": sum(
            1 for row in question_records if row["assets"]),
        "assets": len(asset_records),
        "asset_kinds": dict(sorted(kind_counts.items())),
        "topics": dict(sorted(topic_counts.items())),
        "status": dict(sorted(status_counts.items())),
        "unsure": len(unsure),
        "rejected_registry": "data/tracking/csc429/rejected_registry.json",
        "config": _rel(pure_config.CONFIG_PATH),
        "cost_usd": 0.0,
    }
    _save(BANK / "index.json", summary)
    _save(BANK / "assets_index.json", {
        "schema_version": 1,
        "count": len(asset_records),
        "assets": [
            {key: asset[key] for key in (
                "id", "question_ids", "source_paper", "page", "label",
                "kind", "treatment", "sha256", "path", "verdict")}
            for asset in sorted(asset_records.values(), key=lambda row: row["id"])
        ],
    })
    _save(BANK / "questions_index.json", {
        "schema_version": 1,
        "count": len(question_records),
        "questions": [
            {key: row[key] for key in (
                "id", "source_paper", "pages", "marks", "part", "topic_tags",
                "topic_primary", "assets", "refs", "status", "content_hash")}
            for row in sorted(question_records, key=lambda row: row["id"])
        ],
    })
    return summary


def main() -> None:
    print(json.dumps(build(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
