"""Reusable recycle assembler helpers: feasibility, seed plans and rendering.

The subject keeps its own DOCX template and question-numbering rules.  This
module owns the subject-agnostic parts extracted from the CSC429 pipeline:
mark/topic feasibility, approved-only deterministic selection, reference
renumbering and asset-label mapping.
"""
from __future__ import annotations

import random
import re
from collections import Counter
from dataclasses import dataclass

REF_RE = re.compile(r"\b(Figure|Table)\s+(\d+)\b", re.I)
ROMAN_LABELS = {"i", "ii", "iii", "iv", "v", "vi", "vii"}


@dataclass(frozen=True)
class SlotRequirement:
    label: str
    part: str
    marks: int


def requirements_from_sections(sections: list[dict]) -> list[SlotRequirement]:
    rows: list[SlotRequirement] = []
    for section in sections:
        part = str(section.get("key") or "")
        count = int(section.get("questions") or 0)
        marks = section.get("marks_per_slot")
        if isinstance(marks, int):
            marks = [marks]
        marks = [int(value) for value in (marks or [])]
        if not marks or count <= 0:
            continue
        for index in range(count):
            slot_marks = marks[index] if index < len(marks) else marks[-1]
            rows.append(SlotRequirement(
                label=f"{part}{index + 1}", part=part, marks=slot_marks))
    return rows


def _class_key(part: str, marks: int) -> str:
    return f"{part}:{marks}"


def pool_summary(questions: list[dict],
                 requirements: list[SlotRequirement]) -> dict:
    by_class = Counter()
    by_topic = Counter()
    for question in questions:
        if question.get("status") != "approved":
            continue
        by_class[_class_key(str(question.get("part") or ""),
                            int(question.get("marks") or 0))] += 1
        by_topic[str(question.get("topic_primary")
                     or question.get("topic") or "other")] += 1
    counts = Counter(_class_key(row.part, row.marks) for row in requirements)
    return {
        "approved_questions": sum(1 for row in questions
                                  if row.get("status") == "approved"),
        "by_class": dict(sorted(by_class.items())),
        "by_topic": dict(sorted(by_topic.items())),
        "slots_per_seed": dict(sorted(counts.items())),
    }


def feasibility(questions: list[dict], requirements: list[SlotRequirement],
                *, reuse_cap: int = 4, max_seeds: int = 20) -> dict:
    """Report distinct seeds, reuse-cap capacity and feasible Library size."""
    approved = [row for row in questions if row.get("status") == "approved"]
    demand = Counter(_class_key(row.part, row.marks) for row in requirements)
    pool = Counter(_class_key(str(row.get("part") or ""),
                              int(row.get("marks") or 0)) for row in approved)
    distinct = []
    capped = []
    missing = []
    for key, needed in demand.items():
        if pool[key] < needed:
            missing.append(key)
            continue
        distinct.append(pool[key] // needed)
        capped.append(pool[key] * max(1, int(reuse_cap)) // needed)
    feasible_cap = min(capped) if capped and not missing else 0
    feasible = min(int(max_seeds), feasible_cap)
    return {
        "approved_questions": len(approved),
        "reuse_cap": int(reuse_cap),
        "max_seeds_requested": int(max_seeds),
        "slots_per_seed": sum(demand.values()),
        "pools": dict(sorted(pool.items())),
        "required_per_seed": dict(sorted(demand.items())),
        "missing_classes": missing,
        "distinct_seeds_without_reuse": min(distinct) if distinct and not missing else 0,
        "max_seeds_with_cap": feasible_cap,
        "feasible_seeds": feasible,
        "requested_seeds_feasible": bool(missing == [] and feasible >= max_seeds),
        "library_size": min(int(max_seeds), feasible),
    }


def build_plans(questions: list[dict], requirements: list[SlotRequirement],
                *, seed_count: int, reuse_cap: int = 4,
                rng_seed: str = "recycle") -> list[dict]:
    """Build deterministic approved-only plans with no in-paper repeats.

    The cap is enforced across plans; adjacent seeds avoid reusing a question
    when an alternative exists.
    """
    approved = [row for row in questions if row.get("status") == "approved"]
    by_class: dict[str, list[dict]] = {}
    for question in approved:
        key = _class_key(str(question.get("part") or ""),
                         int(question.get("marks") or 0))
        by_class.setdefault(key, []).append(question)
    for row in requirements:
        key = _class_key(row.part, row.marks)
        if not by_class.get(key):
            raise ValueError(f"no approved questions for slot class {key}")

    uses: Counter[str] = Counter()
    last_used: dict[str, int] = {}
    plans: list[dict] = []
    for serial in range(1, int(seed_count) + 1):
        rng = random.Random(f"{rng_seed}:{serial}")
        chosen: list[dict] = []
        chosen_ids: set[str] = set()
        for requirement in requirements:
            key = _class_key(requirement.part, requirement.marks)
            candidates = [
                row for row in by_class[key]
                if str(row.get("id")) not in chosen_ids
                and uses[str(row.get("id"))] < int(reuse_cap)
                and last_used.get(str(row.get("id"))) != serial - 1
            ]
            if not candidates:
                candidates = [
                    row for row in by_class[key]
                    if str(row.get("id")) not in chosen_ids
                    and uses[str(row.get("id"))] < int(reuse_cap)
                ]
            if not candidates:
                raise ValueError(
                    f"seed {serial} {requirement.label}: no approved "
                    "candidate within the reuse cap")
            topic_counts = Counter(
                str(row.get("topic_primary") or row.get("topic") or "")
                for row in chosen)
            paper_counts = Counter(
                str(row.get("source_paper") or "") for row in chosen)

            def score(row: dict):
                qid = str(row.get("id"))
                return (
                    paper_counts[str(row.get("source_paper") or "")],
                    topic_counts[str(row.get("topic_primary")
                                     or row.get("topic") or "")],
                    uses[qid],
                    str(row.get("topic_primary") or row.get("topic") or ""),
                    rng.random(),
                )

            picked = min(candidates, key=score)
            chosen.append({
                "slot": requirement.label,
                "part": requirement.part,
                "marks": requirement.marks,
                "question_id": picked.get("id"),
                "source_paper": picked.get("source_paper"),
                "pages": picked.get("pages"),
                "topic": picked.get("topic_primary") or picked.get("topic"),
                "topic_tags": picked.get("topic_tags") or [],
                "assets": picked.get("assets") or [],
                "refs": picked.get("refs") or [],
                "content_hash": picked.get("content_hash"),
            })
            chosen_ids.add(str(picked.get("id")))
        for slot in chosen:
            qid = str(slot["question_id"])
            uses[qid] += 1
            last_used[qid] = serial
        plans.append({
            "schema_version": 1,
            "seed": serial,
            "reuse_cap": int(reuse_cap),
            "total_marks": sum(slot["marks"] for slot in chosen),
            "slots": chosen,
        })
    return plans


def _inside(bbox: list, box: list) -> bool:
    cx = (float(bbox[0]) + float(bbox[2])) / 2
    cy = (float(bbox[1]) + float(bbox[3])) / 2
    return box[0] <= cx <= box[2] and box[1] <= cy <= box[3]


def clean_question_text(question: dict, assets: dict[str, dict]) -> str:
    spans = (question.get("native_text_blocks") or [{}])[0].get("spans") or []
    if not spans:
        return str((question.get("native_text_blocks") or [{}])[0].get(
            "text", ""))
    boxes = []
    for aid in question.get("assets") or []:
        asset = assets.get(aid)
        if not asset:
            continue
        page = int(asset.get("page", 0))
        for key in ("content_bbox", "caption_bbox"):
            box = asset.get(key)
            if box and len(box) == 4:
                boxes.append((page, [float(value) for value in box]))
    kept = []
    for span in spans:
        bbox = span.get("bbox")
        page = int(span.get("page", 0))
        if bbox and any(page == box_page and _inside(bbox, box)
                        for box_page, box in boxes):
            continue
        text = str(span.get("text", "")).strip()
        if text:
            kept.append(text)
    return "\n".join(kept)


def rewrite_references(text: str, mapping: dict[str, str]) -> str:
    def replace(match):
        old = f"{match.group(1).title()} {int(match.group(2))}"
        return mapping.get(old, match.group(0))
    return REF_RE.sub(replace, str(text or ""))


def caption_text(asset: dict, new_label: str) -> str:
    caption = " ".join(str(asset.get("caption") or "").split())
    old = str(asset.get("label") or "")
    if old and caption.lower().startswith(old.lower()):
        caption = new_label + caption[len(old):]
    elif caption:
        caption = f"{new_label}: {caption}"
    else:
        caption = new_label
    return caption


def asset_mapping(question: dict, assets: dict[str, dict],
                  fig_counter: list[int], table_counter: list[int]):
    mapping = {}
    ordered = []
    for aid in question.get("assets") or []:
        asset = assets.get(aid)
        if not asset:
            raise RuntimeError(f"missing asset {aid}")
        if asset.get("kind") == "table":
            table_counter[0] += 1
            new = f"Table {table_counter[0]}"
        else:
            fig_counter[0] += 1
            new = f"Figure {fig_counter[0]}"
        old = str(asset.get("label") or "")
        if old in mapping:
            raise RuntimeError(f"duplicate asset label {old} in {question['id']}")
        mapping[old] = new
        ordered.append((asset, new))
    return mapping, ordered


def display_width(asset: dict, config_data: dict) -> float:
    width = float(asset.get("width_px") or 0)
    height = float(asset.get("height_px") or 0)
    minimum = float(config_data.get("figure_min_width_cm", 6.0))
    maximum = float(config_data.get("figure_max_width_cm", 16.2))
    max_height = 18.0 if asset.get("kind") == "picture" else float(
        config_data.get("figure_max_height_cm", 18.0))
    if width <= 0 or height <= 0:
        return minimum
    aspect = width / height
    area = width * height
    chosen = 8.0 if area < 300_000 else 12.0
    if aspect >= 4.5:
        chosen = maximum
    if asset.get("kind") == "table":
        chosen = 12.0
    chosen = max(minimum, min(maximum, chosen))
    if chosen * height / width > max_height:
        chosen = max_height * width / height
    return round(max(minimum, chosen), 2)


def split_subparts(text: str, subparts: list[dict]) -> list[tuple[str, str]]:
    labels = [str(part.get("label", "")).lower()
              for part in subparts or []
              if str(part.get("label", "")).lower() not in ("", "main")]
    if not labels:
        return [("", str(text or "").strip())]
    ordered = sorted(set(labels), key=len, reverse=True)
    alternatives = "|".join(re.escape(label) for label in ordered)
    pattern = re.compile(
        r"(?:(?<=\n)|^|(?<=[.!?]))\s*(?:\((?P<paren>"
        + alternatives
        + r")\)|(?P<close>" + alternatives + r")\))\s*",
        re.I | re.M)
    matches = list(pattern.finditer(text or ""))
    if not matches:
        return [("", str(text or "").strip())]
    segments: list[tuple[str, str]] = []
    preamble = (text or "")[:matches[0].start()].strip()
    if preamble:
        segments.append(("", preamble))
    for index, match in enumerate(matches):
        label = (match.group("paren") or match.group("close")).lower()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = (text or "")[start:end].strip()
        segments.append((label, body))
    return segments
