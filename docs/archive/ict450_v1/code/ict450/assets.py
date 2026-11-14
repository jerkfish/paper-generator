"""Reusable past-paper assets for ICT450 generated questions.

The Stage-1a MinerU caches keep the cropped figures and tables that belonged to
real ICT450 questions.  Stage 6 repurposes those assets instead of redrawing
diagrams: each topic maps to a curated pool of ``(paper_id, asset_id)`` pairs,
and the selected image plus its provenance is attached to the generated
question.  Selection is deterministic for a seed.

    uv run python -m src.subjects.ict450.assets --seed 1
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
from pathlib import Path

from src import config

SUBJECT = "ICT450"
TRACKING = config.TRACKING_DIR / "ict450"
MINERU_DIR = TRACKING / "mineru"

# Curated pools.  Each entry is (paper_id, asset_id, display caption).
# Captions are rewritten to the numbering used by the generated paper.
ASSET_POOLS: dict[str, list[tuple[str, str, str]]] = {
    "database_concept": [
        ("ICT450-2023-FEB", "MU-B0030",
         "Table 1 : Sample data for a spreadsheet program"),
    ],
    "data_model": [
        ("ICT450-2024-JAN", "MU-B0034", "Table 1: BOOKS table"),
        ("ICT450-2024-JAN", "MU-B0040", "Table 2: PUBLISHERS table"),
    ],
    "relational": [
        ("ICT450-2022-FEB", "MU-B0029", "Table 1: STUDENT table"),
        ("ICT450-2022-FEB", "MU-B0030", "Table 2: COURSE table"),
    ],
    "erd": [
        ("ICT450-2019-DEC", "MU-B0029",
         "Figure 1 : Referential integrity in an Entity Relationship Diagram"),
    ],
    "normalization": [
        ("ICT450-2018-JUN", "MU-B0051",
         "Table 1 : Sample of college course information"),
    ],
    "database_design": [
        ("ICT450-2024-JAN", "MU-B0042",
         "Figure 1 : Database Design Process"),
    ],
    "sql": [
        ("ICT450-2023-JUL", "MU-B0058",
         "Table 1 : Relational schema for a loan management system"),
    ],
}


def _normalized_path(paper_id: str) -> Path | None:
    matches = sorted(MINERU_DIR.glob(f"{paper_id}/vlm_*/review/normalized.json"))
    return matches[0] if matches else None


def asset_index() -> dict[tuple[str, str], dict]:
    """Return ``{(paper_id, asset_id): asset}`` from the VLM caches."""
    index: dict[tuple[str, str], dict] = {}
    for path in MINERU_DIR.glob("*/vlm_*/review/normalized.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        paper_id = data.get("paper_id") or path.parents[2].name
        for asset in data.get("assets", []):
            index[(paper_id, asset["asset_id"])] = {**asset, "paper_id": paper_id}
    return index


def question_assets(topic: str, seed: int) -> list[dict]:
    """Pick the repurposed asset(s) for a generated question.

    Pools with more than one entry are selected by seed; a pool entry missing
    from disk is skipped.  Returns records with absolute ``img_path``.
    """
    pool = ASSET_POOLS.get(topic)
    if not pool:
        return []
    rng = random.Random(int(seed) * 7919 + sorted(ASSET_POOLS).index(topic))
    indexes = list(range(len(pool)))
    multi = topic in {"data_model", "relational"}
    if not multi:
        rng.shuffle(indexes)
    index = asset_index()
    selected: list[dict] = []
    for position in indexes:
        paper_id, asset_id, caption = pool[position]
        asset = index.get((paper_id, asset_id))
        if asset is None:
            continue
        path = Path(asset.get("img_path") or "")
        if not path.is_file():
            continue
        selected.append({
            "asset_id": asset_id,
            "kind": asset.get("kind", "image"),
            "label": asset.get("label", ""),
            "caption": caption,
            "img_path": str(path.resolve()),
            "table_html": asset.get("table_html", ""),
            "source_paper": paper_id,
            "source_question": asset.get("question_index"),
            "source_page": asset.get("page_idx"),
            "provenance": asset.get("provenance", {}),
        })
        if not multi:
            break
    return selected


def copy_assets(assets: list[dict], out_dir: Path, seed: int,
                question_index: int) -> list[dict]:
    """Copy selected assets next to the build and return updated records."""
    if not assets:
        return []
    target_dir = Path(out_dir) / "assets"
    target_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for index, asset in enumerate(assets, start=1):
        source = Path(asset["img_path"])
        suffix = source.suffix.lower() or ".jpg"
        target = (target_dir /
                  f"seed_{int(seed):02d}_q{int(question_index)}_asset_{index}"
                  f"{suffix}")
        shutil.copyfile(source, target)
        copied.append({**asset, "img_path": str(target.resolve())})
    return copied


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    topics = sorted(ASSET_POOLS)
    report = {
        topic: question_assets(topic, args.seed) for topic in topics
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
