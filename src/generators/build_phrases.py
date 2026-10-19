"""Build the offline phrase bank for computed question type #1 (one LLM call).

The LLM generates ~150 short security-themed phrases ONCE; code filters
(uppercase A-Z + spaces, 10-25 letters, meaningful words, deduped, not used in
any past paper) and saves data/phrases.json. Question generation then picks
from this bank with a seeded random pick - no per-question plaintext calls.

Run:  uv run python -m src.generators.build_phrases
"""
from __future__ import annotations

import json
import random
import re
from difflib import SequenceMatcher

from openpyxl import load_workbook

from src.config import DATA_DIR, TRACKING_XLSX
from src.llm import chat_json

PHRASE_MODEL = "qwen3.7-flash"  # cheap model for this one-off call

SYSTEM = ("Generate 150 short security-themed phrases. Output exactly one JSON "
          "object: {\"phrases\": [\"...\", ...]}. Each phrase: 10-25 letters, "
          "uppercase English letters and spaces only, meaningful security text "
          "(passwords, malware, firewalls, encryption, backups, phishing, access "
          "control, trusted computing...). Vary sentence structure and topic. "
          "No ciphertext, no numbers, no punctuation.")


def _clean(s: str) -> str:
    return re.sub(r"[^A-Z]", "", str(s).upper())


def _meaningful(s: str) -> bool:
    words = re.findall(r"[A-Z]+", s)
    if not words:
        return False
    for w in words:
        if len(w) > 1 and not re.search(r"[AEIOU]", w):
            return False
        if re.search(r"[^AEIOU]{5}", w):
            return False
    return True


def _past_pool() -> list[str]:
    ws = load_workbook(TRACKING_XLSX)["Questions"]
    headers = [c.value for c in ws[1]]
    return [str(r["Original question text"]) for r in
            (dict(zip(headers, row)) for row in ws.iter_rows(min_row=2, values_only=True))]


def build(past_pool: list[str] | None = None) -> list[str]:
    past_pool = past_pool if past_pool is not None else _past_pool()
    past_tokens: set[str] = set()
    for past in past_pool:
        past_tokens.update(t.upper() for t in re.findall(r"[A-Za-z]{4,}", past))
        cleaned = _clean(past)
        if cleaned and len(cleaned) <= 40:
            past_tokens.add(cleaned)

    data = chat_json(SYSTEM, "Generate the phrases now.", model=PHRASE_MODEL)
    raw = [str(p) for p in data.get("phrases", [])]

    bank: list[str] = []
    for p in raw:
        p = " ".join(p.split()).upper()
        if not (10 <= len(_clean(p)) <= 25):
            continue
        if not _meaningful(p):
            continue
        content = _clean(p)
        if content in past_tokens:
            continue
        if any(SequenceMatcher(None, content, _clean(prev)).ratio() >= 0.8
               for prev in bank):
            continue
        bank.append(p)
    return bank


def main() -> None:
    bank: list[str] = []
    for attempt in range(4):
        new = build()
        added = [p for p in new if p not in bank]
        bank.extend(added)
        print(f"call {attempt + 1}: +{len(added)} phrases (total {len(bank)})")
        if len(bank) >= 120:
            break
    path = DATA_DIR / "phrases.json"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"model": PHRASE_MODEL, "phrases": bank}, indent=2),
                    encoding="utf-8")
    print(f"saved {len(bank)} phrases -> {path} (model: {PHRASE_MODEL})")
    rng = random.Random(42)
    for p in rng.sample(bank, min(8, len(bank))):
        print(f"  - {p}")


if __name__ == "__main__":
    main()
