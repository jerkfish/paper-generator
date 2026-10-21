"""Copy the pre-Phase-1 flat Library cache into per-subject folders.

The old cache key had no subject in its hash.  This script copies each flat
``outputs/web_cache/<hash>`` folder to
``outputs/web_cache/CSC662/<new-hash>``, rewrites absolute file paths in
``meta.json``, and adds the subject, UTC year and topic-mark fields.  The old
folder is left in place as a fallback/backup unless ``--move`` is passed.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from src import config
from src.app.filenames import utc_year
from src.app.jobs import DEFAULT_SUBJECT, _config_hash


def _planner_topic_marks(seed: int) -> dict:
    path = (config.OUTPUTS_DIR / "eval_final_deepseek" /
            f"seed_{seed:02d}_planner.json")
    if not path.exists():
        return {}
    try:
        return dict(json.loads(path.read_text(encoding="utf-8"))
                    .get("assigned_topic_marks") or {})
    except Exception:
        return {}


def migrate(seed_root: Path | None = None, move: bool = False) -> list[dict]:
    root = Path(seed_root or config.WEB_CACHE_DIR)
    subject = DEFAULT_SUBJECT
    done = []
    for meta_path in sorted(root.glob("*/meta.json")):
        if meta_path.parent.parent.name == subject:
            continue  # already migrated
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            seed = int(meta["seed"])
        except Exception:
            continue
        mode = str(meta.get("mode") or "realistic")
        computed = meta.get("computed_marks")
        key = _config_hash(mode, seed, computed, False, subject)
        target = root / subject / key
        target.mkdir(parents=True, exist_ok=True)
        for child in meta_path.parent.iterdir():
            if child.is_file():
                shutil.copy2(child, target / child.name)
        new_meta_path = target / "meta.json"
        meta["subject"] = subject
        meta["year"] = int(meta.get("year") or utc_year(
            meta.get("created") or 0))
        meta["topic_marks"] = dict(
            meta.get("topic_marks") or _planner_topic_marks(seed))
        files = {}
        for kind, value in (meta.get("files") or {}).items():
            if not value:
                files[kind] = ""
                continue
            name = Path(value).name
            files[kind] = str(target / name) if (target / name).exists() else value
        meta["files"] = files
        new_meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        if move:
            shutil.rmtree(meta_path.parent)
        done.append({"seed": seed, "from": str(meta_path.parent),
                     "to": str(target), "moved": move})
    return done


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--move", action="store_true",
                    help="remove the old flat cache after copying")
    args = ap.parse_args()
    for row in migrate(move=args.move):
        print(row, flush=True)


if __name__ == "__main__":
    main()
