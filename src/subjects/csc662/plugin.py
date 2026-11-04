"""CSC662 plugin adapter.

CSC662 is the reference type-A subject: lecture-deck retrieval plus the LLM
theory pipeline.  The shared application never imports this module directly;
it is resolved through the ``plugins`` block in
``subjects/CSC662/subject.json``.
"""
from __future__ import annotations

import json
from pathlib import Path

from src import config


def plan(mode: str, style: str, computed_marks: int | None, seed: int):
    from src.planner.planner import build_plan
    return build_plan(mode, style, computed_marks, seed)


def plan_markdown(summary: dict) -> str:
    from src.planner.planner import to_markdown
    return to_markdown(summary)


def library_seeds() -> list[int]:
    seeds: set[int] = set()
    for path in config.OUTPUTS_DIR.glob(
            "eval_final_deepseek/seed_*_theory.json"):
        try:
            seeds.add(int(path.stem.split("_")[1]))
        except Exception:
            continue
    return sorted(seed for seed in seeds if seed > 0)


def library_metadata(seed: int) -> dict:
    path = (config.OUTPUTS_DIR / "eval_final_deepseek" /
            f"seed_{seed:02d}_planner.json")
    if not path.exists():
        return {}
    try:
        return dict(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return {}


def plan_inputs(seed: int) -> dict[str, Path]:
    base = config.OUTPUTS_DIR / "eval_final_deepseek"
    return {
        "plan": base / f"seed_{seed:02d}_planner.json",
        "theory": base / f"seed_{seed:02d}_theory.json",
    }


def generator_labels() -> dict:
    from src.planner.planner import TYPE_LABEL
    return dict(TYPE_LABEL)


def topic_labels() -> dict:
    return {
        "attacks/malware": "ATK",
        "authentication/biometrics": "AUT",
        "access control models": "ACC",
        "trusted computing/blockchain": "TRU",
        "software/OS security": "SWS",
        "network security": "NET",
        "risk/management (ethics)": "ETH",
        "classical ciphers": "CIP",
        "general cryptography": "CRY",
        "block ciphers": "BLK",
        "hashing/signatures": "HSH",
        "public-key": "PKI",
    }
