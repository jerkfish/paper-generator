"""Apply the owner's MAT133 review decisions and render owner recreations.

The owner exports ``review_decisions.json`` from the review sheet.  This
module:

* stores every owner HTML recreation and renders it to PNG (Playwright/Edge);
* applies question-text corrections supplied by the owner;
* applies question and asset verdicts/comments;
* refreshes the bank index, review sheet, marks table and Gate A report;
* never approves Gate A.  The owner re-reviews the applied fixes.

Run:
    uv run python -m src.subjects.mat133.review_apply
    uv run python -m src.subjects.mat133.review_apply --no-render
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageChops

from src import config
from src.bank.duplicates import (cluster_duplicates, duplicate_map,
                                 near_duplicate_pairs)
from src.bank.quality import quality_band, quality_score
from src.bank.review import build_review_sheet
from src.bank.schema import normalize_text, question_content_hash
from src.bank.store import BankStore, load_json, save_json
from src.subjects.mat133.bank_build import (
    _gate_report,
    _gate_report_md,
    _part_marks,
    _question_topics,
    _write_marks_csv,
    _write_paper_index,
)
from src.subjects.mat133.papers import SUBJECT

TRACKING = config.TRACKING_DIR / "mat133" / "v2"
BANK = TRACKING / "bank"
REVIEW = BANK / "review"
OWNER_DIR = REVIEW / "owner_recreations"
DECISIONS = REVIEW / "review_decisions.json"
APPLY_REPORT = REVIEW / "review_apply_report.json"
APPLY_REPORT_MD = REVIEW / "review_apply_report.md"
UNASSIGNED_DECISIONS = BANK / "unassigned_decisions.json"

HTML_RE = re.compile(r"<!DOCTYPE\s+html[\s\S]*?</html\s*>", re.I)
HTML_TAG_RE = re.compile(r"<html[\s\S]*?</html\s*>", re.I)
SVG_RE = re.compile(r"<svg[\s\S]*?</svg\s*>", re.I)
TAG_RE = re.compile(r"<[^>]+>")
FIG_RE = re.compile(r"\b(Figure|Table)\s+(\d+)\b", re.I)
PART_RE = re.compile(r"(?mi)^[\s*]*([a-h])\s*\)[\s*]*")

APPENDIX_MARKERS = (
    "APPENDIX 1", "**QUESTION ENDS HERE**", "QUESTION ENDS HERE",
    "*END OF PAGE*", "UNIVERSITI TEKNOLOGI MARA",
)
INSTRUCTION_LINES = {
    "use this", "fix the question", "fix the question and figure 1",
    "no figure 2 in question.", "that is not a figure it is a equation.",
}
DROP_LINE_PREFIXES = (
    "use the provided", "use provided", "question c) is cutted",
    "full question c)", "d) did not capture",
)


def _load(path: Path, default=None):
    return load_json(path, default if default is not None else {})


def _save(path: Path, payload) -> Path:
    return save_json(path, payload)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _owner_html(text: str) -> tuple[str, str]:
    """Return ``(html_document, plain_note)`` from an owner comment."""
    raw = str(text or "")
    match = (HTML_RE.search(raw) or HTML_TAG_RE.search(raw)
             or SVG_RE.search(raw))
    if not match:
        return "", raw.strip()
    document = match.group(0).strip()
    if document.lower().startswith("<svg"):
        document = (
            "<!doctype html><html><head><meta charset='utf-8'>"
            "<style>body{margin:0;background:#fff}svg{display:block}</style>"
            "</head><body>" + document + "</body></html>")
    note = (raw[:match.start()] + raw[match.end():]).strip()
    note = "\n".join(line for line in note.splitlines()
                     if line.strip().lower() not in INSTRUCTION_LINES)
    return document, note.strip()


def _plain_note(text: str) -> str:
    _, note = _owner_html(text)
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub(" ", note))).strip()


def _save_owner_html(aid: str, document: str) -> Path:
    OWNER_DIR.mkdir(parents=True, exist_ok=True)
    path = OWNER_DIR / f"{aid}.html"
    path.write_text(document + "\n", encoding="utf-8")
    return path


def _trim_png(path: Path) -> None:
    if not path.is_file():
        return
    with Image.open(path) as source:
        image = source.convert("RGB")
    background = Image.new("RGB", image.size, image.getpixel((0, 0)))
    diff = ImageChops.difference(image, background)
    box = diff.getbbox()
    if box and box != (0, 0, image.width, image.height):
        image.crop(box).save(path, "PNG")


def render_owner_pngs(asset_ids: list[str], *, force: bool = False) -> dict:
    """Render saved owner HTML files to PNG with Edge/Playwright."""
    written = []
    failed = []
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover
        return {"written": [], "failed": [{"error": str(exc)}]}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        try:
            page = browser.new_page(viewport={"width": 1200, "height": 1000},
                                    device_scale_factor=2)
            for aid in asset_ids:
                source = OWNER_DIR / f"{aid}.html"
                target = OWNER_DIR / f"{aid}.png"
                if not source.is_file():
                    failed.append({"asset_id": aid,
                                   "error": "owner HTML missing"})
                    continue
                if (not force and target.is_file()
                        and target.stat().st_mtime >= source.stat().st_mtime):
                    written.append(str(target))
                    continue
                try:
                    page.goto(source.resolve().as_uri())
                    page.wait_for_timeout(250)
                    page.screenshot(path=str(target), full_page=True)
                    _trim_png(target)
                    written.append(str(target))
                except Exception as error:  # keep going asset by asset
                    failed.append({"asset_id": aid,
                                   "error": f"{type(error).__name__}: {error}"})
            page.close()
        finally:
            browser.close()
    return {"written": written, "failed": failed}


def _clean_reviewer_text(text: str, qid: str) -> str:
    value = str(text or "")
    value = re.sub(r"\*\(\s*(\d{1,3})\s*(marks?)\s*\)\*",
                   r"(\1 \2)", value, flags=re.I)
    value = value.replace("\\hfill", "")
    for marker in APPENDIX_MARKERS:
        index = value.find(marker)
        if index != -1:
            value = value[:index]
    if qid == "MAT133-2014-MAR-Q5":
        value = re.split(r"(?m)^\s*1\.\s*\$?\\?sin", value)[0]
    if qid == "MAT133-2023-JUL-Q5":
        match = re.search(r"\*\*QUESTION\s+5\*\*", value, re.I)
        if match:
            value = value[match.end():]
    lines = []
    for line in value.splitlines():
        stripped = line.strip()
        low = stripped.lower()
        if not stripped:
            lines.append("")
            continue
        if low in INSTRUCTION_LINES:
            continue
        if low.startswith(DROP_LINE_PREFIXES):
            continue
        if re.match(r"^\*{0,2}QUESTION\s+\d+\*{0,2}$", stripped, re.I):
            continue
        if stripped.startswith(("* NEW PAGE *", "*END OF PAGE*")):
            continue
        lines.append(line.rstrip())
    return "\n".join(lines).strip()


def _parse_reviewer_parts(text: str) -> list[dict]:
    matches = list(PART_RE.finditer(text))
    segments = []
    if not matches:
        segments.append({"label": "", "text": text.strip()})
    else:
        preamble = text[:matches[0].start()].strip()
        if preamble:
            segments.append({"label": "", "text": preamble})
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            segments.append({
                "label": match.group(1).lower(),
                "text": text[match.end():end].strip(),
            })
    parts = []
    for segment in segments:
        body = segment["text"].strip().strip("*").strip()
        if not body:
            continue
        marks, note = _part_marks(body)
        parts.append({
            "label": segment["label"],
            "text": body,
            "marks": marks,
            "marks_mineru": None,
            "marks_source": "owner_review" if marks is not None else "",
            "marks_note": note,
            "nested_labels": [],
            "merged_warning": "",
        })
    return parts


def _full_text(parts: list[dict]) -> str:
    lines = []
    for part in parts:
        text = str(part.get("text") or "").strip()
        label = str(part.get("label") or "")
        lines.append(f"{label}) {text}" if label else text)
    return "\n".join(lines)


def _apply_text(question: dict, comment: str, qid: str) -> bool:
    """Apply owner-provided text.  Returns True when text changed."""
    cleaned = _clean_reviewer_text(comment, qid)
    if not cleaned:
        return False
    # Asset-only instructions ("figure 1 needs fix") are not questions.
    if (not re.search(PART_RE, cleaned)
            and not re.search(r"\(\s*\d{1,3}\s*marks?\s*\)", cleaned, re.I)
            and len(cleaned) < 300):
        return False
    provided = _parse_reviewer_parts(cleaned)
    if not provided:
        return False
    existing = {str(part.get("label") or ""): part
                for part in question.get("parts") or []}

    if qid == "MAT133-2011-SEP-Q4":
        # Owner supplied only the missing part c).
        provided = [part for part in provided if part["label"] == "c"]
        if not provided:
            return False
        merged = []
        for label in ("a", "b", "c"):
            part = provided[0] if label == "c" else existing.get(label)
            if part:
                merged.append(part)
        question["parts"] = merged
    elif qid == "MAT133-2014-MAR-Q5":
        # Owner supplied a/b/c; d) remains the unverified figure part.
        merged = []
        for label in ("a", "b", "c", "d"):
            part = next((row for row in provided if row["label"] == label),
                        None) or existing.get(label)
            if part:
                if label == "d" and part.get("text"):
                    part = dict(part)
                    part["text"] = (_clean_reviewer_text(
                        str(part["text"]), qid) or str(part["text"]))
                merged.append(part)
        question["parts"] = merged
    elif qid == "MAT133-2026-FEB-Q3":
        # The owner supplied the missing equation for part a); keep part b).
        equation = provided[0]
        equation["label"] = "a"
        equation["marks"] = equation.get("marks") or 5
        equation["marks_source"] = "owner_review"
        b_part = existing.get("b")
        question["parts"] = [equation] + ([b_part] if b_part else [])
    else:
        if not any(part.get("label") for part in provided):
            provided[0]["label"] = "a"
        for part in provided:
            if part.get("marks") is None:
                old = existing.get(part["label"]) or {}
                if old.get("marks") is not None:
                    part["marks"] = old["marks"]
                    part["marks_source"] = "retained"
                    part["marks_note"] = (
                        "mark retained from the pre-review bank; owner text "
                        "did not include it")
        question["parts"] = provided

    parts = question["parts"]
    question["native_text"] = _full_text(parts)
    question["native_text_blocks"] = [{
        "text": question["native_text"],
        "normalised": normalize_text(question["native_text"]),
        "page": (question.get("pages") or [1])[0],
        "bbox": [],
    }]
    question["subpart_marks"] = [
        {"label": part["label"], "marks": int(part["marks"]),
         "source": part.get("marks_source", "")}
        for part in parts if part.get("marks") is not None
    ]
    question["marks"] = sum(int(part["marks"]) for part in parts
                            if part.get("marks") is not None)
    question["marks_complete"] = all(part.get("marks") is not None
                                     and part.get("label") for part in parts)
    question["refs"] = sorted({
        f"{kind.title()} {int(number)}"
        for kind, number in FIG_RE.findall(question["native_text"])})
    question["topic_tags"] = _question_topics(question["native_text"], parts)
    question["content_hash"] = question_content_hash(question)
    question["owner_review_text"] = cleaned
    return True


def _asset_relative(asset: dict, store: BankStore) -> str:
    path = Path(str(asset.get("path") or ""))
    try:
        return "../" + path.relative_to(store.root).as_posix()
    except ValueError:
        return ""


def _apply_asset(asset: dict, decision: dict) -> tuple[dict, str, str]:
    """Apply one asset decision; return (asset, owner_html, plain_note)."""
    choice = str(decision.get("choice") or "")
    raw_comment = str(decision.get("comment") or decision.get("notes") or "")
    owner_html, note = _owner_html(raw_comment)
    plain = note or _plain_note(raw_comment)
    if owner_html and not plain:
        plain = ("owner HTML recreation applied"
                 if choice == "use_recreation"
                 else "owner HTML recreation stored; original selected")
    asset = dict(asset)
    asset["review_choice"] = choice
    if plain:
        asset["review_note_text"] = plain
    else:
        asset["review_note_text"] = asset.get("review_note_text") or ""
    asset["reviewed_on"] = _today()
    if not asset.get("review_original_path"):
        asset["review_original_path"] = _asset_relative(asset, BankStore(BANK))
    if owner_html:
        asset["owner_recreation_html"] = f"{asset['id']}.html"
        asset["owner_recreation_file"] = f"{asset['id']}.png"
        asset["owner_recreation_sha256"] = _sha256_bytes(
            owner_html.encode("utf-8"))
    if choice == "use_original":
        asset["selected_treatment"] = "original_crop"
        asset["verdict"] = "approved"
        relative = str(asset.get("review_original_path") or "")
        if relative.startswith("../"):
            original = BANK / relative.replace("../", "", 1)
            if original.is_file():
                asset["path"] = str(original)
                asset["sha256"] = _sha256_file(original)
                asset["treatment"] = "original_crop"
                asset["dpi"] = None
    elif choice == "use_recreation":
        if owner_html or (OWNER_DIR / f"{asset['id']}.html").is_file():
            asset["selected_treatment"] = "html_recreation"
            asset["treatment"] = "html_recreation"
            asset["verdict"] = "approved"
            png = OWNER_DIR / f"{asset['id']}.png"
            if png.is_file():
                asset["path"] = str(png)
                asset["sha256"] = _sha256_file(png)
                asset["dpi"] = 200
                asset["owner_recreation_file"] = png.name
        else:
            asset["selected_treatment"] = "needs_recreation"
            asset["verdict"] = "pending"
            asset["review_note_text"] = (
                plain + " [no owner HTML recreation supplied]").strip()
    elif choice in {"needs_more_work", ""}:
        asset["verdict"] = "pending"
    else:
        asset["verdict"] = "pending"
        asset["review_note_text"] = f"{plain} [unknown choice {choice}]"
    return asset, owner_html, plain


REJECT_ASSETS = {
    "A-MAT133-2021-JUL-Q4-F2":
        "owner: page 8 figure is unrelated to the page 3 Figure 1",
    "A-MAT133-2023-JUL-Q5-C2":
        "owner: no Figure 2 in this question",
    "A-MAT133-2026-FEB-Q3-F1":
        "owner: this is an equation, not a figure",
}
OVERRIDE_NEEDS_FIX = {
    "MAT133-2014-MAR-Q5":
        "owner supplied corrected a/b/c; part d still has no captured Figure 1",
}
TEXT_NOTES = {
    "MAT133-2011-SEP-Q4": "part c replaced from owner-supplied text.",
    "MAT133-2014-MAR-Q5":
        "a/b/c replaced from owner-supplied text; part d Figure 1 is still "
        "missing.",
    "MAT133-2021-JUL-Q4-2":
        "question replaced from owner-supplied text; Figure 1 uses the "
        "owner recreation.",
    "MAT133-2021-JUL-Q5-2":
        "question replaced from owner-supplied text.",
    "MAT133-2021-JUL-Q5":
        "question text replaced; part b mark retained from the bank.",
    "MAT133-2023-JUL-Q5":
        "question replaced from owner-supplied text; Figure 2 removed.",
    "MAT133-2026-FEB-Q3":
        "part a equation added from owner-supplied text; the equation image "
        "was unlinked.",
}


def apply_decisions(decisions_path: Path = DECISIONS,
                    *, render: bool = True) -> dict:
    payload = _load(Path(decisions_path))
    if str(payload.get("subject")) != SUBJECT:
        raise SystemExit("review decisions are not for MAT133")
    decisions = payload.get("questions") or {}
    store = BankStore(BANK)
    questions = {str(row["id"]): row for row in store.questions()}
    assets = {str(row["id"]): row for row in store.assets()}
    missing = sorted(set(decisions) - set(questions))
    if missing:
        raise SystemExit(f"decisions reference missing questions: {missing}")

    owner_html_by_asset: dict[str, str] = {}
    counts = {"approved": 0, "needs_fix": 0, "rejected": 0,
              "use_original": 0, "use_recreation": 0,
              "asset_rejected": 0, "text_corrected": 0}
    applied = []
    for qid, decision in decisions.items():
        question = dict(questions[qid])
        verdict = str(decision.get("verdict") or "").strip()
        if verdict not in {"approved", "needs_fix", "rejected"}:
            raise SystemExit(f"{qid}: invalid verdict {verdict!r}")
        comment = str(decision.get("comment")
                      or decision.get("notes") or "").strip()
        question["review_verdict"] = verdict
        question["review_notes"] = _plain_note(comment)
        question["review_note_text"] = question["review_notes"]
        question["reviewed_on"] = _today()
        text_changed = _apply_text(question, comment, qid)
        if text_changed:
            counts["text_corrected"] += 1
            note = TEXT_NOTES.get(
                qid, "owner-provided corrected text applied; re-review.")
            question["review_notes"] = note
            question["review_note_text"] = note
        if qid in OVERRIDE_NEEDS_FIX and not text_changed:
            question["review_notes"] = (
                question["review_notes"] + " " + OVERRIDE_NEEDS_FIX[qid]
            ).strip()
            question["review_note_text"] = question["review_notes"]

        keep_assets = []
        for aid in list(question.get("assets") or []):
            asset = assets.get(aid)
            if asset is None:
                continue
            asset_decision = (decision.get("assets") or {}).get(aid) or {}
            asset, owner_html, plain = _apply_asset(
                asset, asset_decision if isinstance(asset_decision, dict)
                else {"choice": str(asset_decision)})
            if owner_html:
                owner_html_by_asset[aid] = owner_html
            if aid in REJECT_ASSETS:
                asset["verdict"] = "rejected"
                asset["review_note_text"] = REJECT_ASSETS[aid]
                asset["rejected_reason"] = REJECT_ASSETS[aid]
                counts["asset_rejected"] += 1
            else:
                keep_assets.append(aid)
            if asset.get("review_choice") == "use_original":
                counts["use_original"] += 1
            elif asset.get("review_choice") == "use_recreation":
                counts["use_recreation"] += 1
            save_json(store.asset_path(aid), asset)
            assets[aid] = asset
        question["assets"] = keep_assets
        question["unresolved_refs"] = [
            ref for ref in question.get("refs") or [] if not any(
                str(assets.get(aid, {}).get("label", "")).lower()
                == ref.lower() for aid in keep_assets)]
        if verdict == "approved":
            question["status"] = "approved"
            counts["approved"] += 1
        elif verdict == "rejected":
            question["status"] = "rejected"
            counts["rejected"] += 1
        else:
            question["status"] = "needs_fix"
            counts["needs_fix"] += 1
        if verdict != "rejected":
            if text_changed or qid in OVERRIDE_NEEDS_FIX:
                question["status"] = "needs_fix"
            if any(assets.get(aid, {}).get("verdict") != "approved"
                   for aid in keep_assets):
                question["status"] = "needs_fix"
        question["quality_score"] = quality_score(question, {
            aid: assets[aid] for aid in keep_assets if aid in assets})
        question["quality_band"] = quality_band(question["quality_score"])
        save_json(store.question_path(qid), question)
        questions[qid] = question
        applied.append({
            "question_id": qid,
            "review_verdict": verdict,
            "status": question["status"],
            "text_corrected": text_changed,
            "note": question["review_notes"],
        })

    # Save every owner HTML document before rendering.
    for aid, document in owner_html_by_asset.items():
        _save_owner_html(aid, document)
    render_result = {"written": [], "failed": []}
    if render:
        render_result = render_owner_pngs(sorted(owner_html_by_asset))
        for written in render_result.get("written") or []:
            path = Path(written)
            asset = assets.get(path.stem)
            if asset is None:
                continue
            asset["path"] = str(path)
            asset["sha256"] = _sha256_file(path)
            asset["dpi"] = 200
            asset["owner_recreation_file"] = path.name
            asset["treatment"] = "html_recreation"
            save_json(store.asset_path(asset["id"]), asset)
        for failed in render_result.get("failed") or []:
            asset = assets.get(str(failed.get("asset_id") or ""))
            if asset is not None:
                asset["verdict"] = "pending"
                asset["selected_treatment"] = "html_recreation_failed"
                save_json(store.asset_path(asset["id"]), asset)

    # Unassigned assets: ignore/delete decisions.
    unassigned_payload = _load(UNASSIGNED_DECISIONS, {
        "subject": SUBJECT, "decisions": {}})
    unassigned_payload["subject"] = SUBJECT
    unassigned_payload["decisions"] = dict(
        unassigned_payload.get("decisions") or {})
    ignored = set()
    for aid, value in (payload.get("unassigned_assets") or {}).items():
        choice = str(value.get("choice") or "") if isinstance(value, dict) else str(value)
        note = (_plain_note(value.get("comment") or value.get("notes") or "")
                if isinstance(value, dict) else "")
        unassigned_payload["decisions"][aid] = {
            "choice": choice, "note": note, "reviewed_on": _today()}
        if "ignore" in note.lower() or "delete" in note.lower():
            ignored.add(aid)
            source = next((path for path in (BANK / "unassigned").glob(
                f"*-{aid}.png")), None)
            if source and source.is_file():
                target_dir = BANK / "unassigned_ignored"
                target_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(target_dir / source.name))
    save_json(UNASSIGNED_DECISIONS, unassigned_payload)

    counts["approved"] = sum(1 for q in questions.values()
                             if q["status"] == "approved")
    counts["needs_fix"] = sum(1 for q in questions.values()
                              if q["status"] == "needs_fix")
    counts["rejected"] = sum(1 for q in questions.values()
                             if q["status"] == "rejected")
    metadata = refresh_bank(store, ignored=ignored,
                            render_result=render_result)
    report = {
        "schema_version": 1,
        "subject": SUBJECT,
        "applied_on": _now(),
        "decisions_exported_on": payload.get("exported_on", ""),
        "counts": counts,
        "questions": applied,
        "render": render_result,
        "rejected_assets": [
            {"asset_id": aid, "reason": reason}
            for aid, reason in sorted(REJECT_ASSETS.items())],
        "ignored_unassigned_assets": sorted(ignored),
        "bank": metadata,
        "gate_a": "pending re-review",
    }
    save_json(APPLY_REPORT, report)
    APPLY_REPORT_MD.write_text(_report_md(report), encoding="utf-8")
    return report


def _extra_assets(ignored: set[str]) -> list[dict]:
    extra = []
    decisions = (load_json(UNASSIGNED_DECISIONS, {}).get("decisions") or {})
    for aid in sorted(decisions):
        if aid in ignored:
            continue
        matches = list((BANK / "unassigned").glob(f"*-{aid}.png"))
        if not matches:
            continue
        path = matches[0]
        paper = path.stem[:-len(f"-{aid}")] if path.stem.endswith(
            f"-{aid}") else path.stem
        extra.append({
            "id": aid,
            "label": paper,
            "kind": "picture",
            "page": "",
            "treatment": "unassigned",
            "review_path": f"../unassigned/{path.name}",
        })
    return extra


def refresh_bank(store: BankStore, *, ignored: set[str],
                 render_result: dict) -> dict:
    questions = list(store.questions())
    assets = {str(asset["id"]): asset for asset in store.assets()}
    clusters = cluster_duplicates(questions)
    lookup = duplicate_map(questions)
    for question in questions:
        question["duplicate_cluster"] = lookup.get(
            question["id"], question["id"])
        linked = {aid: assets[aid] for aid in question.get("assets") or []
                  if aid in assets}
        question["quality_score"] = quality_score(question, linked)
        question["quality_band"] = quality_band(question["quality_score"])
        save_json(store.question_path(question["id"]), question)
    near = near_duplicate_pairs(questions)
    counts = {
        "papers": len({q["source_paper"] for q in questions}),
        "papers_expected": 37,
        "papers_missing": 0,
        "questions": len(questions),
        "extracted": sum(1 for q in questions if q["status"] == "extracted"),
        "approved": sum(1 for q in questions if q["status"] == "approved"),
        "needs_fix": sum(1 for q in questions if q["status"] == "needs_fix"),
        "rejected": sum(1 for q in questions if q["status"] == "rejected"),
        "assets": len(assets),
        "assets_approved": sum(1 for a in assets.values()
                               if a.get("verdict") == "approved"),
        "assets_pending": sum(1 for a in assets.values()
                              if a.get("verdict") == "pending"),
        "assets_rejected": sum(1 for a in assets.values()
                               if a.get("verdict") == "rejected"),
        "fallback_assets": sum(1 for a in assets.values()
                               if a.get("treatment") == "page_crop_fallback"),
        "references": sum(len(q.get("refs") or []) for q in questions),
        "unresolved_references": sum(
            len(q.get("unresolved_refs") or []) for q in questions),
        "duplicate_clusters": sum(1 for c in clusters if c["count"] > 1),
        "near_duplicate_pairs": len(near),
        "unsure": 0,
        "marks_total": sum(int(q.get("marks") or 0) for q in questions),
    }
    topic_counts: dict[str, int] = {}
    for question in questions:
        for topic in question.get("topic_tags") or ["other"]:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
    index = {
        "schema_version": 2,
        "subject": SUBJECT,
        "generated_on": _now(),
        "model": "vlm",
        "counts": counts,
        "topics": dict(sorted(topic_counts.items())),
        "papers": sorted({q["source_paper"] for q in questions}),
        "missing_papers": [],
        "questions": [{
            "id": q["id"], "source_paper": q["source_paper"],
            "marks": q["marks"], "status": q["status"],
            "topic_tags": q["topic_tags"],
            "quality_score": q["quality_score"],
            "quality_band": q["quality_band"],
            "refs": q.get("refs") or [], "assets": q.get("assets") or [],
        } for q in questions],
    }
    unsure_items = []
    for question in questions:
        if question["status"] in {"needs_fix", "rejected"}:
            note = (question.get("review_notes")
                    or "; ".join(question.get("parse_notes") or [])
                    or "owner marked needs fix")
            unsure_items.append({
                "question_id": question["id"],
                "item": note,
                "blocking": question["status"] == "needs_fix",
                "opened": question.get("reviewed_on") or _today(),
            })
    counts["unsure"] = len(unsure_items)
    index["counts"] = counts
    save_json(BANK / "index.json", index)
    save_json(BANK / "unsure.json", {
        "subject": SUBJECT, "generated_on": _now(),
        "items": unsure_items})
    save_json(BANK / "duplicates.json", {"exact": clusters, "near": near})
    save_json(BANK / "approvals.json", {
        "subject": SUBJECT,
        "gate_a": {
            "status": "pending",
            "reviewed_on": _today(),
            "counts": counts,
            "note": "Fixes applied; owner re-review required.",
        },
    })
    review = build_review_sheet(
        store, store.review_dir, subject=SUBJECT,
        title="MAT133 v2 question bank",
        extra_assets=_extra_assets(ignored))
    needs_fix_review = build_review_sheet(
        store, store.review_dir, subject=SUBJECT,
        title="MAT133 v2 question bank — needs fix",
        only_status={"needs_fix"},
        filename="index_needs_fix.html",
        export_name="review_decisions_needs_fix.json")
    _write_paper_index(index, store.review_dir)
    _write_paper_index(
        index, store.review_dir,
        filename="index_by_paper_needs_fix.html",
        sheet="index_needs_fix.html",
        statuses={"needs_fix"},
        heading="MAT133 v2 — needs fix by paper")
    _write_marks_csv(questions, store.review_dir)
    report = _gate_report(index, questions, list(assets.values()),
                          unsure_items, review)
    save_json(BANK / "gate1_report.json", report)
    (BANK / "gate1_report.md").write_text(
        _gate_report_md(report, questions), encoding="utf-8")
    return {"counts": counts, "review": str(review),
            "needs_fix_review": str(needs_fix_review),
            "gate_a": "pending re-review",
            "render": render_result}


def _report_md(report: dict) -> str:
    counts = report["counts"]
    lines = [
        "# MAT133 review decisions — applied",
        "",
        f"Applied: {report['applied_on']}",
        f"Owner export: {report['decisions_exported_on']}",
        "",
        "Gate A remains **pending**; this is a fix pass for re-review.",
        "",
        "## Verdicts",
        "",
        f"- Questions approved: {counts['approved']}",
        f"- Questions needs fix: {counts['needs_fix']}",
        f"- Questions rejected: {counts['rejected']}",
        f"- Question texts corrected: {counts['text_corrected']}",
        f"- Assets use original: {counts['use_original']}",
        f"- Assets use recreation: {counts['use_recreation']}",
        f"- Assets rejected/unlinked: "
        f"{len(report.get('rejected_assets') or [])}",
        f"- Owner HTML recreations rendered: "
        f"{len(report['render'].get('written') or [])}",
        f"- Render failures: {len(report['render'].get('failed') or [])}",
        f"- Ignored unassigned assets: "
        f"{len(report.get('ignored_unassigned_assets') or [])}",
        "",
        "## Rejected / unlinked assets",
        "",
    ]
    for row in report.get("rejected_assets") or []:
        lines.append(f"- `{row['asset_id']}`: {row['reason']}")
    if not report.get("rejected_assets"):
        lines.append("None.")
    lines += [
        "",
        "## Questions",
        "",
    ]
    for row in report["questions"]:
        lines.append(
            f"- `{row['question_id']}`: {row['review_verdict']} → "
            f"{row['status']}"
            + (" [text corrected]" if row["text_corrected"] else ""))
    if report["render"].get("failed"):
        lines += ["", "## Render failures", ""]
        for row in report["render"]["failed"]:
            lines.append(f"- `{row.get('asset_id')}`: {row.get('error')}")
    lines += [
        "",
        "Re-open `review/index.html` to review the applied fixes; Gate A is "
        "not approved.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decisions", default=str(DECISIONS))
    parser.add_argument("--no-render", action="store_true")
    args = parser.parse_args()
    report = apply_decisions(Path(args.decisions),
                             render=not args.no_render)
    print(json.dumps({
        "counts": report["counts"],
        "render": {
            "written": len(report["render"].get("written") or []),
            "failed": report["render"].get("failed") or [],
        },
        "bank": report["bank"]["counts"],
    }, indent=2))


if __name__ == "__main__":
    main()
