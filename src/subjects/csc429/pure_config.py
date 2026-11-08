"""Configuration for the CSC429 asset-first pure-extraction pipeline."""
from __future__ import annotations

import json
import os
from pathlib import Path

from src import config

TRACKING = config.TRACKING_DIR / "csc429"
CONFIG_PATH = TRACKING / "config.json"

DEFAULTS = {
    "vision_concurrency": 4,
    "diagram_recreate_max_nodes": 0,
    "diagram_recreate_max_edges": 0,
    "table_fuzzy_threshold": 0.92,
    "figure_min_width_cm": 6.0,
    "figure_max_width_cm": 16.2,
    "figure_max_height_cm": 18.0,
    "cost_cap_usd": 5.0,
}


def load() -> dict:
    payload = dict(DEFAULTS)
    if CONFIG_PATH.is_file():
        try:
            payload.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            pass
    env_cap = os.environ.get("CSC429_COST_CAP_USD", "").strip()
    if env_cap:
        try:
            payload["cost_cap_usd"] = float(env_cap)
        except ValueError:
            pass
    return payload


def ensure() -> dict:
    payload = load()
    if not CONFIG_PATH.exists():
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
    return payload
