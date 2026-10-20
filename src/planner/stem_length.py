"""Measure stem length from the 10 clean modern papers.

The verifier keeps generated stems within the 90th percentile for their mark
value.  Marks are read from the Questions sheet; question labels and trailing
``(N marks)`` text are stripped before counting words.
"""
from __future__ import annotations

import math
import re
from functools import lru_cache

from src.planner.fingerprint_data import load_modern_stats


def clean_stem(text: str) -> str:
    text = re.sub(r"\(\s*\d+\s*marks?\s*\)", "", str(text), flags=re.I)
    text = re.sub(r"^\s*QUESTION\s+\d+\s*", "", text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip()


def stem_word_count(text: str) -> int:
    return len(clean_stem(text).split())


def _percentile(values: list[int], pct: float) -> float:
    """Linear-interpolated percentile (same convention as numpy)."""
    if not values:
        return 0.0
    xs = sorted(values)
    pos = (len(xs) - 1) * pct / 100.0
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return float(xs[lo])
    frac = pos - lo
    return xs[lo] * (1 - frac) + xs[hi] * frac


@lru_cache(maxsize=1)
def stem_length_stats() -> dict[int, dict]:
    rows = [r for r in load_modern_stats().rows
            if str(r.get("Original question text", "")).strip()]
    out: dict[int, dict] = {}
    for marks in (2, 5, 6):
        vals = [stem_word_count(r["Original question text"]) for r in rows
                if int(r.get("Marks") or 0) == marks]
        if not vals:
            continue
        out[marks] = {
            "n": len(vals),
            "median": _percentile(vals, 50),
            "p90": _percentile(vals, 90),
            "max": max(vals),
        }
    return out


@lru_cache(maxsize=1)
def stem_p90_limits() -> dict[int, int]:
    """Word limits used by prompt and verifier, rounded up to whole words."""
    return {m: int(math.ceil(s["p90"]))
            for m, s in stem_length_stats().items()}


if __name__ == "__main__":
    for m, s in stem_length_stats().items():
        print(f"{m} marks: n={s['n']} median={s['median']:.1f} "
              f"p90={s['p90']:.1f} max={s['max']}")
    print("limits:", stem_p90_limits())
