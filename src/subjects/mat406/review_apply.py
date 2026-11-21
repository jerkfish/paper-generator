"""Apply the first MAT406 bank review and prepare a needs-fix-only round 2.

The owner exported ``review_decisions.json`` from the review sheet.  This
module applies the 44 approvals, corrects the 14 flagged questions/assets and
regenerates `review/index.html` with only those 14 items.  It never approves
Gate A; the owner re-reviews the fixes.

Run:
    uv run python -m src.subjects.mat406.review_apply
    uv run python -m src.subjects.mat406.review_apply --no-render
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageChops

from src import config
from src.bank.duplicates import cluster_duplicates, duplicate_map
from src.bank.quality import quality_band, quality_score
from src.bank.review import build_review_sheet
from src.bank.schema import normalize_text, question_content_hash
from src.bank.store import BankStore, load_json, save_json
from src.subjects.mat406.bank_build import (
    _gate_report,
    _gate_report_md,
    _write_marks_csv,
    _write_paper_index,
)
from src.subjects.mat406.papers import SUBJECT

TRACKING = config.TRACKING_DIR / "mat406" / "v2"
BANK = TRACKING / "bank"
REVIEW = BANK / "review"
OWNER_DIR = REVIEW / "owner_recreations"
DECISIONS = REVIEW / "review_decisions.json"
APPLY_REPORT = REVIEW / "review_apply_report.json"
APPLY_REPORT_MD = REVIEW / "review_apply_report.md"
ROUND2_MD = REVIEW / "ROUND2.md"

HTML_RE = re.compile(r"<!DOCTYPE\s+html[\s\S]*?</html\s*>", re.I)
HTML_TAG_RE = re.compile(r"<html[\s\S]*?</html\s*>", re.I)
SVG_RE = re.compile(r"<svg[\s\S]*?</svg\s*>", re.I)
TAG_RE = re.compile(r"<[^>]+>")

# ``�`` is the replacement glyph left by MinerU/OCR.  These values are the
# printed characters confirmed by the owner's comments and the source pages.
TEXT_FIXES: dict[str, tuple[str, ...]] = {
    "MAT406-2021-JUL-Q1": ("m",),
    "MAT406-2021-JUL-Q2": (r"\theta",),
    "MAT406-2021-JUL-Q3": ("x", "A", "B", "A", "B"),
    "MAT406-2021-JUL-Q4": (r"\beta", "A"),
    "MAT406-2021-JUL-Q5": ("P",),
    "MAT406-2022-FEB-Q6": ("x",),
    "MAT406-2022-FEB-Q7": (r"\alpha",),
}

TEXT_NOTES = {
    "MAT406-2021-JUL-Q1": "replaced the unreadable glyph with m; owner recreation selected for Figure 1.",
    "MAT406-2021-JUL-Q2": "replaced the unreadable glyph with theta; owner recreation selected for Figure 2.",
    "MAT406-2021-JUL-Q3": "replaced the unreadable glyphs with x, A and B.",
    "MAT406-2021-JUL-Q4": "corrected two unreadable glyphs to beta and A and removed a stray page number in an already-approved question.",
    "MAT406-2021-JUL-Q5": "replaced the unreadable glyph with P.",
    "MAT406-2022-FEB-Q6": "replaced the unreadable glyph with x.",
    "MAT406-2022-FEB-Q7": "replaced the unreadable glyph with alpha.",
    "MAT406-2023-JUL-Q6": "removed the stray CONFIDENTIAL line.",
}

DELETE_ASSETS = {
    "A-MAT406-2026-FEB-Q2-2-F1": "owner: figure/picture not related; delete.",
    "A-MAT406-2026-FEB-Q3-F1": "owner: figure/picture not related; delete.",
    "A-MAT406-2026-FEB-Q3-F2": "owner: figure/picture not related; delete.",
    "A-MAT406-2026-FEB-Q3-F3": "owner: figure/picture not related; delete.",
    "A-MAT406-2026-FEB-Q3-F4": "owner: figure/picture not related; delete.",
    "A-MAT406-2026-FEB-Q3-F5": "owner: figure/picture not related; delete.",
    "A-MAT406-2026-FEB-Q4-F1": "owner: figure/picture not related; delete.",
}


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
                    page.wait_for_timeout(300)
                    page.screenshot(path=str(target), full_page=True)
                    _trim_png(target)
                    written.append(str(target))
                except Exception as error:
                    failed.append({"asset_id": aid,
                                   "error": f"{type(error).__name__}: {error}"})
            page.close()
        finally:
            browser.close()
    return {"written": written, "failed": failed}


UNKNOWN_GLYPH_RE = re.compile(r"[�-]")


def _replace_unknown(text: str, values: tuple[str, ...]) -> str:
    out = str(text or "")
    if len(values) == 1:
        return UNKNOWN_GLYPH_RE.sub(
            lambda _match, value=values[0]: value, out)
    for value in values:
        out = UNKNOWN_GLYPH_RE.sub(
            lambda _match, replacement=value: replacement, out, count=1)
    return out


def _apply_text_fixes(question: dict, qid: str) -> bool:
    if qid not in TEXT_FIXES and qid != "MAT406-2023-JUL-Q6":
        return False
    changed = False
    if qid in TEXT_FIXES:
        values = TEXT_FIXES[qid]
        for key in ("native_text", "stem"):
            old = str(question.get(key) or "")
            new = _replace_unknown(old, values)
            if new != old:
                question[key] = new
                changed = True
        for part in question.get("parts") or []:
            old = str(part.get("text") or "")
            if qid == "MAT406-2021-JUL-Q3":
                part_values = (("x",) if part.get("label") == "a"
                               else ("A", "B", "A", "B"))
            else:
                part_values = values
            new = _replace_unknown(old, part_values)
            if new != old:
                part["text"] = new
                changed = True
    if qid == "MAT406-2021-JUL-Q4":
        # Remove the stray page number printed between parts a) and b).
        for key in ("native_text", "stem"):
            old = str(question.get(key) or "")
            new = re.sub(r"(?m)^\s*4\s*\n?", "", old)
            if new != old:
                question[key] = new.strip()
                changed = True
        for part in question.get("parts") or []:
            old = str(part.get("text") or "")
            new = re.sub(r"(?m)^\s*4\s*\n?", "", old)
            if new != old:
                part["text"] = new.strip()
                changed = True
    if qid == "MAT406-2021-JUL-Q1":
        # The owner's glyph note fixes the first unknown as m; the second is
        # printed as p (page 2), so correct the repeated m after glyph repair.
        for key in ("native_text", "stem"):
            old = str(question.get(key) or "")
            new = old.replace("the value of m using the value of m",
                              "the value of p using the value of m")
            if new != old:
                question[key] = new
                changed = True
        for part in question.get("parts") or []:
            old = str(part.get("text") or "")
            new = old.replace("the value of m using the value of m",
                              "the value of p using the value of m")
            if new != old:
                part["text"] = new
                changed = True
    if qid == "MAT406-2023-JUL-Q6":
        for key in ("native_text", "stem"):
            old = str(question.get(key) or "")
            new = re.sub(r"\s*CONFIDENTIAL\s*", " ", old).strip()
            if new != old:
                question[key] = new
                changed = True
        for part in question.get("parts") or []:
            old = str(part.get("text") or "")
            new = re.sub(r"\s*CONFIDENTIAL\s*", " ", old).strip()
            if new != old:
                part["text"] = new
                changed = True
    if changed:
        text = str(question.get("native_text") or "")
        question["native_text_blocks"] = [{
            "text": text,
            "normalised": normalize_text(text),
            "page": (question.get("pages") or [1])[0],
            "bbox": [],
        }]
    return changed


def _asset_relative(asset: dict) -> str:
    try:
        return "../" + Path(str(asset.get("path") or "")).relative_to(
            BANK).as_posix()
    except ValueError:
        return ""


def _apply_asset(asset: dict, decision: dict) -> tuple[dict, str, str]:
    choice = str(decision.get("choice") or "")
    raw = str(decision.get("comment") or decision.get("notes") or "")
    owner_html, note = _owner_html(raw)
    plain = note or _plain_note(raw)
    asset = dict(asset)
    asset["review_choice"] = choice
    asset["review_note_text"] = plain
    asset["reviewed_on"] = _today()
    if not asset.get("review_original_path") and asset.get("path"):
        asset["review_original_path"] = _asset_relative(asset)
    aid = str(asset["id"])
    if aid in DELETE_ASSETS or re.search(r"\b(delete|not related)\b",
                                         plain, re.I):
        asset["verdict"] = "rejected"
        asset["selected_treatment"] = "deleted"
        asset["rejected_reason"] = DELETE_ASSETS.get(
            aid, plain or "owner: not related")
        return asset, "", plain
    if choice == "use_recreation":
        if owner_html:
            asset["owner_recreation_html"] = f"{aid}.html"
            asset["owner_recreation_file"] = f"{aid}.png"
            asset["owner_recreation_sha256"] = _sha256_bytes(
                owner_html.encode("utf-8"))
            asset["selected_treatment"] = "html_recreation"
            asset["verdict"] = "pending"
        else:
            asset["verdict"] = "pending"
            asset["selected_treatment"] = "needs_recreation"
        return asset, owner_html, plain
    if choice == "use_original":
        asset["selected_treatment"] = "original_crop"
        asset["verdict"] = "pending" if plain else "approved"
        return asset, "", plain
    asset["verdict"] = "pending"
    return asset, "", plain


def _refresh(store: BankStore) -> dict:
    questions = list(store.questions())
    assets = list(store.assets())
    duplicate_clusters = cluster_duplicates(questions)
    duplicate_lookup = duplicate_map(questions)
    asset_map = {str(row["id"]): row for row in assets}
    for question in questions:
        question["duplicate_cluster"] = duplicate_lookup.get(
            question["id"], question["id"])
        question["content_hash"] = question_content_hash(question)
        linked = [asset_map[aid] for aid in question.get("assets") or []
                  if aid in asset_map and asset_map[aid].get("verdict") != "rejected"]
        question["quality_score"] = quality_score(question, {
            row["id"]: row for row in linked})
        question["quality_band"] = quality_band(question["quality_score"])
        save_json(store.question_path(question["id"]), question)
    active_assets = [row for row in assets
                     if row.get("verdict") != "rejected"]
    rejected_assets = [row for row in assets
                       if row.get("verdict") == "rejected"]
    statuses = {
        "approved": sum(1 for q in questions if q["status"] == "approved"),
        "needs_fix": sum(1 for q in questions if q["status"] == "needs_fix"),
        "rejected": sum(1 for q in questions if q["status"] == "rejected"),
        "extracted": sum(1 for q in questions if q["status"] == "extracted"),
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
        "counts": {
            "papers": 9,
            "papers_expected": 9,
            "papers_missing": 0,
            "questions": len(questions),
            **statuses,
            "assets": len(active_assets),
            "rejected_assets": len(rejected_assets),
            "fallback_assets": 0,
            "references": sum(len(q.get("refs") or []) for q in questions),
            "unresolved_references": sum(
                len(q.get("unresolved_refs") or []) for q in questions),
            "duplicate_clusters": sum(1 for row in duplicate_clusters
                                      if row["count"] > 1),
            "near_duplicate_pairs": 6,
            "unsure": 0,
            "excluded_assets": 1,
            "marks_total": sum(int(q.get("marks") or 0) for q in questions),
        },
        "topics": dict(sorted(topic_counts.items())),
        "papers": sorted({q["source_paper"] for q in questions}),
        "missing_papers": [],
        "excluded_assets": load_json(
            TRACKING / "asset_exclusions.json", {}).get("assets", {}),
        "questions": [{
            "id": q["id"],
            "source_paper": q["source_paper"],
            "marks": q["marks"],
            "status": q["status"],
            "topic_tags": q["topic_tags"],
            "quality_score": q["quality_score"],
            "quality_band": q["quality_band"],
            "refs": q["refs"],
            "assets": q["assets"],
        } for q in questions],
    }
    save_json(BANK / "index.json", index)
    save_json(BANK / "unsure.json", {
        "subject": SUBJECT, "generated_on": _now(), "items": []})
    save_json(BANK / "approvals.json", {
        "subject": SUBJECT,
        "gate_a": {
            "status": "pending",
            "by": "",
            "on": "",
            "evidence": [],
            "note": "Round 1 applied: 44 approved, 14 fixes await round 2 review.",
        },
    })
    build_review_sheet(
        store, REVIEW, subject=SUBJECT,
        title="MAT406 v2 bank — round 1 full review",
        filename="all.html", export_name="review_decisions_all.json")
    build_review_sheet(
        store, REVIEW, subject=SUBJECT,
        title="MAT406 v2 bank — round 2: needs fix only",
        only_status={"needs_fix"}, filename="index.html",
        export_name="review_decisions_round2.json")
    _write_paper_index(
        index, REVIEW, filename="index_by_paper.html", sheet="index.html",
        statuses={"needs_fix"},
        heading="MAT406 v2 bank — round 2 (needs fix only)")
    _write_marks_csv(questions, REVIEW)
    report = _gate_report(
        index, questions, active_assets, [], REVIEW / "index.html")
    report["counts"]["rejected_assets"] = len(rejected_assets)
    report["review_round"] = 2
    report["round1_counts"] = statuses
    save_json(BANK / "gate1_report.json", report)
    (BANK / "gate1_report.md").write_text(
        _gate_report_md(report, questions), encoding="utf-8")
    return {
        "questions": len(questions),
        **statuses,
        "assets": len(active_assets),
        "rejected_assets": len(rejected_assets),
        "index": str(BANK / "index.json"),
    }


def apply_decisions(decisions_path: Path = DECISIONS,
                    *, render: bool = True) -> dict:
    payload = load_json(Path(decisions_path), {})
    if str(payload.get("subject")) != SUBJECT:
        raise SystemExit("review decisions are not for MAT406")
    decisions = payload.get("questions") or {}
    store = BankStore(BANK)
    questions = {str(row["id"]): row for row in store.questions()}
    assets = {str(row["id"]): row for row in store.assets()}
    missing = sorted(set(decisions) - set(questions))
    if missing:
        raise SystemExit(f"decisions reference missing questions: {missing}")

    owner_html_by_asset: dict[str, str] = {}
    applied = []
    counts = {"approved": 0, "needs_fix": 0, "rejected": 0,
              "text_corrected": 0, "asset_recreation": 0,
              "asset_deleted": 0}
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
        question["review_round"] = 1
        text_changed = _apply_text_fixes(question, qid)
        has_text_fix = qid in TEXT_FIXES or qid == "MAT406-2023-JUL-Q6"
        if has_text_fix:
            counts["text_corrected"] += 1
        asset_notes = []
        for aid, asset_decision in (decision.get("assets") or {}).items():
            ad = (asset_decision if isinstance(asset_decision, dict)
                  else {"choice": str(asset_decision)})
            plain_note = _plain_note(
                ad.get("comment") or ad.get("notes") or "")
            if aid in DELETE_ASSETS or re.search(
                    r"(delete|not related)", plain_note, re.I):
                asset_notes.append(f"{aid}: unrelated asset deleted")
            elif str(ad.get("choice") or "") == "use_recreation":
                asset_notes.append(f"{aid}: owner recreation selected")
        notes = []
        if has_text_fix:
            notes.append(TEXT_NOTES.get(
                qid, "owner-requested text correction applied."))
        notes.extend(asset_notes)
        if notes:
            cleaned = [note.rstrip(".") for note in notes]
            question["fix_note"] = "; ".join(cleaned) + "."
        keep_assets = []
        for aid in list(question.get("assets") or []):
            asset = assets.get(aid)
            if asset is None:
                continue
            asset_decision = (decision.get("assets") or {}).get(aid) or {}
            asset, owner_html, _plain = _apply_asset(
                asset, asset_decision if isinstance(asset_decision, dict)
                else {"choice": str(asset_decision)})
            if owner_html:
                owner_html_by_asset[aid] = owner_html
                counts["asset_recreation"] += 1
            if asset.get("verdict") == "rejected":
                counts["asset_deleted"] += 1
            else:
                keep_assets.append(aid)
            save_json(store.asset_path(aid), asset)
            assets[aid] = asset
        question["assets"] = keep_assets
        question["unresolved_refs"] = [
            ref for ref in question.get("refs") or []
            if not any(str(assets.get(aid, {}).get("label", "")).lower()
                       == str(ref).lower() for aid in keep_assets)]
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
            # A text-only correction to an already-approved question keeps the
            # owner's approved verdict.  A pending asset still needs round 2.
            if any(assets.get(aid, {}).get("verdict") == "pending"
                   for aid in keep_assets):
                question["status"] = "needs_fix"
        if question["status"] == "needs_fix" and question.get("fix_note"):
            question["parse_notes"] = [question["fix_note"]]
        save_json(store.question_path(qid), question)
        questions[qid] = question
        applied.append({
            "question_id": qid,
            "review_verdict": verdict,
            "status": question["status"],
            "text_corrected": text_changed,
            "note": question.get("fix_note") or question["review_notes"],
        })

    # Report the final bank statuses, not just the raw verdict counts.
    counts["approved"] = sum(1 for q in questions.values()
                             if q["status"] == "approved")
    counts["needs_fix"] = sum(1 for q in questions.values()
                              if q["status"] == "needs_fix")
    counts["rejected"] = sum(1 for q in questions.values()
                             if q["status"] == "rejected")
    counts["asset_recreation"] = sum(
        1 for a in assets.values() if a.get("owner_recreation_file"))
    counts["asset_deleted"] = sum(
        1 for a in assets.values() if a.get("verdict") == "rejected")

    for aid, document in owner_html_by_asset.items():
        _save_owner_html(aid, document)
    render_result = {"written": [], "failed": []}
    if render and owner_html_by_asset:
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

    metadata = _refresh(store)
    report = {
        "schema_version": 1,
        "subject": SUBJECT,
        "applied_on": _now(),
        "decisions_exported_on": payload.get("exported_on", ""),
        "counts": counts,
        "questions": applied,
        "render": render_result,
        "bank": metadata,
        "gate_a": "pending round 2 re-review",
    }
    save_json(APPLY_REPORT, report)
    APPLY_REPORT_MD.write_text(_report_md(report), encoding="utf-8")
    _write_round2_md(applied, counts)
    return report


def _report_md(report: dict) -> str:
    counts = report["counts"]
    lines = [
        "# MAT406 round 1 review — applied",
        "",
        f"Applied: {report['applied_on']}",
        f"Decisions exported: {report['decisions_exported_on']}",
        "",
        f"- Questions approved: {counts['approved']}",
        f"- Questions needing round 2: {counts['needs_fix']}",
        f"- Questions rejected: {counts['rejected']}",
        f"- Text corrections: {counts['text_corrected']}",
        f"- Asset recreations: {counts['asset_recreation']}",
        f"- Assets deleted: {counts['asset_deleted']}",
        f"- Rendered recreations: {len(report['render'].get('written') or [])}",
        f"- Render failures: {len(report['render'].get('failed') or [])}",
        "",
        "Gate A remains pending.  Only the needs-fix questions are shown in "
        "`review/index.html` for round 2.",
        "",
    ]
    return "\n".join(lines)


def _write_round2_md(applied: list[dict], counts: dict) -> None:
    rows = [row for row in applied if row["status"] == "needs_fix"]
    lines = [
        "# MAT406 — round 2 review (needs fix only)",
        "",
        f"Round 1 approved {counts['approved']} questions.  "
        f"{len(rows)} questions were flagged and fixed; only these are in "
        "the round 2 sheet.",
        "",
        "| Question | What changed |",
        "|---|---|",
    ]
    for row in rows:
        note = str(row.get("note") or "").replace("|", "/")
        lines.append(f"| `{row['question_id']}` | {note} |")
    lines += [
        "",
        "Open `data/tracking/mat406/v2/bank/review/index.html` and export "
        "`review_decisions_round2.json` after reviewing.",
        "",
    ]
    ROUND2_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decisions", type=Path, default=DECISIONS)
    parser.add_argument("--no-render", action="store_true")
    args = parser.parse_args()
    result = apply_decisions(args.decisions, render=not args.no_render)
    print(json.dumps({
        "counts": result["counts"],
        "bank": result["bank"],
        "render": result["render"],
        "gate_a": result["gate_a"],
    }, indent=2))


if __name__ == "__main__":
    main()
