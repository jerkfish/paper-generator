"""Evidence-based Stage-1 corrections for CSC429.

The normal extractor is deliberately conservative.  This module applies the
owner-verified corrections in ``stage1_corrections.json`` after the normal
question/asset build:

* crop an uncaptioned diagram and remove its flattened labels from prose;
* attach an owner-supplied native table (with cell data) to a question;
* correct verified subpart labels/marks and clerical table references.

The correction file is data, not a hidden code path.  Every entry records the
source page, crop or reason so it can be audited.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

from src import config

SUBJECT = "CSC429"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def _rel(path: Path) -> str:
    try:
        return path.relative_to(config.PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _inside(bbox: list[float], box: list[float]) -> bool:
    cx = (float(bbox[0]) + float(bbox[2])) / 2
    cy = (float(bbox[1]) + float(bbox[3])) / 2
    return box[0] <= cx <= box[2] and box[1] <= cy <= box[3]


def _page_meta(tracking: Path, paper_id: str, page_no: int) -> dict:
    manifest = _load(tracking / "pages" / paper_id / "manifest.json")
    for page in manifest.get("pages", []):
        if int(page.get("page", 0)) == int(page_no):
            return page
    raise RuntimeError(f"missing page {page_no} for {paper_id}")


def _source_file(tracking: Path, paper_id: str) -> str:
    layout = _load(tracking / "layout" / f"{paper_id}.json")
    return str(layout.get("paper", ""))


def _crop(tracking: Path, correction: dict) -> tuple[Path, int, int, list[float]]:
    paper_id = str(correction["paper_id"])
    page_meta = _page_meta(tracking, paper_id, int(correction["page"]))
    page_image = config.PROJECT_ROOT / page_meta["image"]
    if not page_image.is_file():
        raise RuntimeError(f"missing page image: {page_image}")
    box = [float(value) for value in correction["bbox_pdf"]]
    page_width, page_height = [float(value) for value in page_meta["page_points"]]
    with Image.open(page_image) as source:
        image = source.convert("RGB")
        sx = image.width / page_width
        sy = image.height / page_height
        crop = image.crop((
            max(0, int(box[0] * sx)),
            max(0, int(box[1] * sy)),
            min(image.width, int(box[2] * sx)),
            min(image.height, int(box[3] * sy)),
        ))
    target = tracking / "assets" / paper_id / f"{correction['asset_id']}.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    crop.save(target, "PNG", dpi=(300, 300))
    return target, crop.width, crop.height, [page_width, page_height]


def _diagram_update(question: dict, correction: dict) -> dict:
    box = [float(value) for value in correction["bbox_pdf"]]
    spans = list(question.get("source_spans") or [])
    kept = [span for span in spans
            if not _inside(list(span.get("bbox") or [0, 0, 0, 0]), box)]
    if len(kept) == len(spans):
        if correction["asset_id"] in (question.get("asset_ids") or []):
            return question
        raise RuntimeError(
            f"correction did not match any spans for {question['question_id']}")
    question["source_spans"] = kept
    question["text"] = "\n".join(str(span.get("text", "")) for span in kept)
    for subpart in question.get("subparts") or []:
        if subpart.get("label") == "main":
            subpart["text"] = question["text"]
            if kept:
                subpart["bbox"] = list(kept[0]["bbox"])
    asset_ids = list(question.get("asset_ids") or [])
    if correction["asset_id"] not in asset_ids:
        asset_ids.append(correction["asset_id"])
    question["asset_ids"] = asset_ids
    question["asset_status"] = "linked"
    flags = list(question.get("review_flags") or [])
    if "uncaptioned_diagram_recovered" not in flags:
        flags.append("uncaptioned_diagram_recovered")
    question["review_flags"] = flags
    return question


def _append_asset(manifest: dict, record: dict) -> None:
    rows = [row for row in manifest.get("assets", [])
            if row.get("asset_id") != record["asset_id"]]
    rows.append(record)
    manifest["assets"] = rows
    for paper in manifest.get("papers", []):
        if paper.get("paper_id") == record["paper_id"]:
            ids = list(paper.get("assets") or [])
            if record["asset_id"] not in ids:
                ids.append(record["asset_id"])
            paper["assets"] = ids
            break
    counts = manifest.setdefault("counts", {})
    counts["assets"] = len(rows)
    counts["figures"] = sum(
        1 for row in rows if row.get("kind") == "figure")
    counts["tables"] = sum(
        1 for row in rows if row.get("kind") == "table")
    counts["high"] = sum(
        1 for row in rows if row.get("confidence") == "high")
    counts["medium"] = sum(
        1 for row in rows if row.get("confidence") == "medium")
    counts["low"] = sum(
        1 for row in rows if row.get("confidence") == "low")


def _diagram_record(tracking: Path, correction: dict,
                    manifest: dict) -> dict:
    target, width, height, page_points = _crop(tracking, correction)
    page_meta = _page_meta(tracking, correction["paper_id"],
                           int(correction["page"]))
    record = {
        "asset_id": correction["asset_id"],
        "paper_id": correction["paper_id"],
        "source_file": _source_file(tracking, correction["paper_id"]),
        "kind": "figure",
        "label": correction.get("label", "Diagram 1"),
        "caption": "",
        "page": int(correction["page"]),
        "page_image": page_meta["image"],
        "page_points": page_points,
        "bbox_pdf": [round(float(value), 2)
                     for value in correction["bbox_pdf"]],
        "content_bbox": [round(float(value), 2)
                         for value in correction["bbox_pdf"]],
        "caption_bbox": None,
        "prompt_trim": None,
        "path": _rel(target),
        "width_px": width,
        "height_px": height,
        "dpi": 300,
        "sha256": _sha256(target),
        "method": "stage1_correction_crop",
        "tightened": True,
        "display_width_cm": 12.0,
        "confidence": "high",
        "review_flags": ["uncaptioned_diagram_correction"],
        "correction_reason": correction.get("reason", ""),
    }
    _append_asset(manifest, record)
    return record


def _table_record(tracking: Path, correction: dict,
                  manifest: dict) -> dict:
    target, width, height, page_points = _crop(tracking, correction)
    page_meta = _page_meta(tracking, correction["paper_id"],
                           int(correction["page"]))
    record = {
        "asset_id": correction["asset_id"],
        "paper_id": correction["paper_id"],
        "source_file": _source_file(tracking, correction["paper_id"]),
        "kind": "table",
        "label": correction.get("label", "Table 1"),
        "caption": correction.get("caption", ""),
        "page": int(correction["page"]),
        "page_image": page_meta["image"],
        "page_points": page_points,
        "bbox_pdf": [round(float(value), 2)
                     for value in correction["bbox_pdf"]],
        "content_bbox": [round(float(value), 2)
                         for value in correction["bbox_pdf"]],
        "caption_bbox": correction.get("caption_bbox"),
        "prompt_trim": None,
        "path": _rel(target),
        "width_px": width,
        "height_px": height,
        "dpi": 300,
        "sha256": _sha256(target),
        "method": "owner_verified_table",
        "tightened": False,
        "display_width_cm": None,
        "confidence": "high",
        "review_flags": ["owner_verified"],
        "table_data": correction["table_data"],
        "correction_reason": correction.get("reason", ""),
    }
    _append_asset(manifest, record)
    return record


def _apply_fix(question: dict, fix: dict) -> dict:
    replacements = fix.get("replacements") or []
    for old, new in replacements:
        old, new = str(old), str(new)
        question["text"] = str(question.get("text", "")).replace(old, new)
        for subpart in question.get("subparts") or []:
            subpart["text"] = str(subpart.get("text", "")).replace(old, new)
        for span in question.get("source_spans") or []:
            span["text"] = str(span.get("text", "")).replace(old, new)
    if replacements and question.get("figure_refs") is not None:
        refs = []
        for ref in question.get("figure_refs") or []:
            value = str(ref)
            for old, new in replacements:
                value = value.replace(str(old), str(new))
            if value not in refs:
                refs.append(value)
        question["figure_refs"] = refs
    if fix.get("text") is not None:
        question["text"] = str(fix["text"])
    if fix.get("subparts") is not None:
        question["subparts"] = [dict(part) for part in fix["subparts"]]
    if fix.get("marks") is not None:
        question["marks"] = int(fix["marks"])
    prepend = fix.get("prepend_first_span") or {}
    if prepend:
        match = str(prepend.get("match", ""))
        label = str(prepend.get("label", "a"))
        for span in question.get("source_spans") or []:
            text = str(span.get("text", ""))
            if match and match in text and not text.startswith(f"{label})"):
                span["text"] = f"{label}) {text}"
                break
    flags = list(question.get("review_flags") or [])
    for flag in fix.get("remove_flags") or []:
        flags = [value for value in flags if value != flag]
    if fix.get("asset_status"):
        question["asset_status"] = str(fix["asset_status"])
    if fix.get("attach_asset"):
        asset_id = str(fix["attach_asset"])
        asset_ids = list(question.get("asset_ids") or [])
        if asset_id not in asset_ids:
            asset_ids.append(asset_id)
        question["asset_ids"] = asset_ids
    if fix.get("figure_refs") is not None:
        question["figure_refs"] = list(fix["figure_refs"])
    if "owner_verified" not in flags:
        flags.append("owner_verified")
    question["review_flags"] = flags
    return question


def apply_corrections(tracking: Path | None = None) -> dict:
    tracking = Path(tracking) if tracking is not None else (
        config.TRACKING_DIR / "csc429")
    path = tracking / "stage1_corrections.json"
    if not path.is_file():
        return {"applied": 0, "reason": "no corrections file"}
    payload = _load(path)
    assets_path = tracking / "assets" / "manifest.json"
    bank_path = tracking / "question_bank_draft.json"
    manifest = _load(assets_path)
    bank = _load(bank_path)
    questions = {row["question_id"]: row for row in bank.get("questions", [])}
    applied = []
    fixed_ids = set()
    resolved = []

    for correction in payload.get("diagram_assets") or []:
        question = questions.get(str(correction.get("question_id", "")))
        if question is None:
            raise RuntimeError(
                f"correction question missing: {correction.get('question_id')}")
        record = _diagram_record(tracking, correction, manifest)
        _diagram_update(question, correction)
        fixed_ids.add(question["question_id"])
        applied.append({
            "question_id": question["question_id"],
            "asset_id": record["asset_id"],
            "kind": "diagram",
        })

    for correction in payload.get("table_assets") or []:
        question = questions.get(str(correction.get("question_id", "")))
        if question is None:
            raise RuntimeError(
                f"correction question missing: {correction.get('question_id')}")
        record = _table_record(tracking, correction, manifest)
        question["asset_ids"] = list(dict.fromkeys(
            list(question.get("asset_ids") or []) + [record["asset_id"]]))
        question["asset_status"] = "linked"
        fixed_ids.add(question["question_id"])
        applied.append({
            "question_id": question["question_id"],
            "asset_id": record["asset_id"],
            "kind": "table",
        })

    for fix in payload.get("question_fixes") or []:
        question_id = str(fix.get("question_id", ""))
        question = questions.get(question_id)
        if question is None:
            raise RuntimeError(f"correction question missing: {question_id}")
        _apply_fix(question, fix)
        fixed_ids.add(question_id)
        resolved.append({
            "question_id": question_id,
            "reason": fix.get("reason", ""),
        })
        applied.append({
            "question_id": question_id,
            "kind": "question_fix",
        })

    resolved_refs = {
        ("CSC429-2014-12", "Table 1"),
        ("CSC429-2016-12", "Table 4"),
        ("CSC429-2017-07", "Table 1"),
        ("CSC429-2023-02", "Table 1"),
    }
    kept_unresolved = []
    resolved_unresolved = []
    for item in manifest.get("unresolved") or []:
        key = (item.get("paper_id"), item.get("label"))
        if key in resolved_refs:
            resolved_unresolved.append(item)
        else:
            kept_unresolved.append(item)
    if resolved_unresolved:
        manifest["unresolved"] = kept_unresolved
        manifest["resolved_unresolved"] = resolved_unresolved
        manifest.setdefault("counts", {})["unresolved"] = len(kept_unresolved)

    if fixed_ids:
        kept_unsure = []
        removed_unsure = []
        for item in bank.get("unsure") or []:
            if item.get("question_id") in fixed_ids:
                removed_unsure.append(item)
            else:
                kept_unsure.append(item)
        bank["unsure"] = kept_unsure
        if removed_unsure:
            bank["resolved_unsure"] = removed_unsure
    bank["questions"] = list(questions.values())
    summary = bank.setdefault("summary", {})
    summary["with_assets"] = sum(
        1 for row in bank["questions"] if row.get("asset_ids"))
    summary["unsure"] = len(bank.get("unsure") or [])
    summary["resolved_unsure"] = len(bank.get("resolved_unsure") or [])
    _save(assets_path, manifest)
    _save(bank_path, bank)
    return {
        "applied": len(applied),
        "items": applied,
        "resolved_unsure": resolved,
        "remaining_unsure": len(bank.get("unsure") or []),
    }


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--tracking", default="")
    args = parser.parse_args()
    tracking = Path(args.tracking) if args.tracking else None
    print(json.dumps(apply_corrections(tracking), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
