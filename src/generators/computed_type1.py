"""Computed question type #1: classical ciphers, end to end.

Design rule (owner-approved): the LLM supplies ONLY cipher type, plaintext
(short, meaningful), key, task (encrypt/decrypt) and marks. The ciphertext,
the answer and all marking-scheme working are computed by code - the LLM
never produces ciphertext or answers.

Verifier: solver runs; plaintext is meaningful English/Malay; key is valid
for the cipher; marks fit the modern slots (2 or 6); not a near-copy of any
past question. Failures regenerate, max 3 retries.

Run:  uv run python -m src.generators.computed_type1
"""
from __future__ import annotations

import json
import math
import random
import re
from difflib import SequenceMatcher

from openpyxl import load_workbook
from pydantic import BaseModel, Field

from src.config import DATA_DIR, OUTPUTS_DIR, TRACKING_XLSX
from src.generators import ciphers as C
from src.llm import chat_json

CIPHERS = ("caesar", "vigenere", "playfair", "affine", "columnar", "vernam")
ALLOWED_MARKS = (2, 6)
DRAFT_MODEL = "qwen3.7-flash"  # cheap model for per-question draft calls


def _phrase_bank() -> list[str]:
    path = DATA_DIR / "phrases.json"
    if not path.exists():
        raise SystemExit("run 'uv run python -m src.generators.build_phrases' first")
    return list(json.loads(path.read_text(encoding="utf-8"))["phrases"])


class DraftQuestion(BaseModel):
    cipher: str
    plaintext: str = ""  # filled from the phrase bank by code
    key: str = Field(min_length=1)
    task: str
    marks: int


SYSTEM = """You draft exam questions for a computer-security course's cipher drills.
Output ONE JSON object exactly:
{"cipher": "caesar|vigenere|playfair|affine|columnar|vernam",
 "key": "see formats below",
 "task": "encrypt|decrypt",
 "marks": 2 or 6}
The plaintext is supplied by code from a phrase bank - do NOT include a
plaintext field. Key formats: caesar -> "shift=7"; vigenere/playfair -> a word
of >=3 letters; affine -> "(a,b)" with a coprime to 26, e.g. "(17,20)";
columnar -> a keyword of >=3 letters OR a column count 2-10; vernam ->
space-separated numbers, e.g. "3 6 12 9 4" (at least 6 numbers).
Rules: never include any ciphertext in your output. Vary ciphers across calls
and include decrypt tasks. Return only the JSON object."""


def _parse_key(cipher: str, key: str):
    k = key.strip()
    if cipher == "caesar":
        m = re.fullmatch(r"shift\s*=\s*(\d+)", k, re.I)
        if not m or not 1 <= int(m.group(1)) <= 25:
            raise ValueError("caesar key must be shift=1..25")
        return int(m.group(1))
    if cipher == "affine":
        m = re.fullmatch(r"\((\d+)\s*,\s*(\d+)\)", k)
        if not m:
            raise ValueError("affine key must be (a,b)")
        a, b = int(m.group(1)), int(m.group(2))
        if math.gcd(a, 26) != 1 or not 0 <= b <= 25:
            raise ValueError("affine key: a coprime with 26, b in 0..25")
        return (a, b)
    if cipher == "vernam":
        nums = [int(x) for x in k.replace(",", " ").split()]
        if len(nums) < 6:
            raise ValueError("vernam key needs >= 6 numbers")
        return nums
    if cipher == "columnar":
        if k.isdigit():
            n = int(k)
            if not 2 <= n <= 10:
                raise ValueError("columnar count must be 2..10")
            return n
        if not k.isalpha() or len(C.clean(k)) < 3:
            raise ValueError("columnar keyword must be >= 3 letters")
        return C.clean(k)
    word = C.clean(k)
    if len(word) < 3:
        raise ValueError(f"{cipher} key must be >= 3 letters")
    return word


def ciphertext(q: DraftQuestion) -> str:
    """The ciphertext shown in the paper. For decrypt questions the LLM's
    plaintext is the intended readable ANSWER, so we encrypt it to display."""
    key = _parse_key(q.cipher, q.key)
    p = C.clean(q.plaintext)
    if q.cipher == "caesar":
        return C.caesar_encrypt(p, key)
    if q.cipher == "vigenere":
        return C.vigenere_encrypt(p, key)
    if q.cipher == "playfair":
        return C.playfair_encrypt(p, key)
    if q.cipher == "affine":
        return C.affine_encrypt(p, key[0], key[1])
    if q.cipher == "columnar":
        return C.columnar_encrypt(p, key)
    if q.cipher == "vernam":
        return C.vernam_encrypt(p, key)
    raise ValueError(f"unknown cipher {q.cipher}")


def answer(q: DraftQuestion) -> str:
    """The single correct answer: readable plaintext for decrypt questions,
    the ciphertext otherwise."""
    return C.clean(q.plaintext) if q.task == "decrypt" else ciphertext(q)


def _meaningful(plaintext: str) -> tuple[bool, str]:
    words = re.findall(r"[A-Za-z]+", plaintext)
    if not words:
        return False, "no words"
    for w in words:
        if len(w) > 1 and not re.search(r"[AEIOUaeiou]", w):
            return False, f"word without vowel: {w}"
        if re.search(r"[^AEIOUaeiou]{5}", w):
            return False, f"suspicious consonant run: {w}"
    if len(plaintext) < 5 or len(plaintext) > 40:
        return False, "length out of range"
    return True, ""


def render_question(q: DraftQuestion) -> str:
    p = q.plaintext.strip()
    k = q.key.strip()
    if q.task == "decrypt":
        value = ciphertext(q)
        if q.cipher == "caesar":
            return (f"Using Caesar Cipher technique, decrypt the following "
                    f"ciphertext.\n{value}\n({q.marks} marks)")
        if q.cipher == "vigenere":
            return (f"Decrypt the following ciphertext using the Vigenere cipher "
                    f"with the key {k}.\n{value}\n({q.marks} marks)")
        if q.cipher == "affine":
            return (f"Decrypt the following ciphertext using the affine cipher "
                    f"with key {k}.\n{value}\n({q.marks} marks)")
        if q.cipher == "vernam":
            return (f"Decrypt the following ciphertext using one-time pad with "
                    f"the key numbers {k}.\n{value}\n({q.marks} marks)")
        if q.cipher == "columnar":
            return (f"Decrypt the following ciphertext using columnar "
                    f"transposition with the key {k}.\n{value}\n({q.marks} marks)")
        return (f"Decrypt the following ciphertext using Playfair encryption "
                f"with the key {k}.\n{value}\n({q.marks} marks)")
    if q.cipher == "caesar":
        shift = _parse_key(q.cipher, q.key)
        return (f"Using Caesar Cipher technique, encrypt the following plaintext "
                f"with shift {shift}.\n{p}\n({q.marks} marks)")
    if q.cipher == "vigenere":
        return (f"Encrypt the plaintext below using Vigenere cipher with the key "
                f"{k}.\n{p}\n({q.marks} marks)")
    if q.cipher == "playfair":
        return (f"Encrypt the message below using Playfair encryption with the "
                f"key {k}.\n{p}\n({q.marks} marks)")
    if q.cipher == "affine":
        return (f"Encrypt the plaintext below using affine cipher with key {k}. "
                f"\n{p}\n({q.marks} marks)")
    if q.cipher == "columnar":
        return (f"Using columnar transposition with the key {k}, encrypt the "
                f"following plaintext.\n{p}\n({q.marks} marks)")
    return (f"Based on Vernam cipher, using the given random numbers {k}, "
            f"encrypt the following plaintext.\n{p}\n({q.marks} marks)")


def verify(q: DraftQuestion, pool: list[str]) -> list[str]:
    problems = []
    try:
        key = _parse_key(q.cipher, q.key)
    except ValueError as e:
        return [str(e)]
    if q.marks not in ALLOWED_MARKS:
        problems.append(f"marks {q.marks} not in {ALLOWED_MARKS}")
    plain = C.clean(q.plaintext)
    ok, why = _meaningful(str(q.plaintext))
    if not ok:
        problems.append(f"plaintext not meaningful: {why}")
    if q.task == "decrypt" and len(plain) < 5:
        problems.append("decrypt plaintext too short")
    if q.cipher == "vernam" and key and len(key) < 8:
        problems.append("vernam key needs at least 8 numbers (it repeats)")
    try:
        ciphertext(q)
        answer(q)
    except Exception as e:
        problems.append(f"solver error: {e}")
    # near-copy check: compare the CONTENT (plaintext/key) against the words
    # used in past questions - token granularity, not template stems
    content_plain = _norm(q.plaintext)
    past_tokens: set[str] = set()
    for past in pool:
        past_tokens.update(t.upper() for t in re.findall(r"[A-Za-z]{4,}", past))
        cleaned = _norm(past)
        if cleaned and len(cleaned) <= 40:  # short entries = whole phrases
            past_tokens.add(cleaned)
    for tok in past_tokens:
        if (len(tok) >= 4 and content_plain
                and (content_plain == tok
                     or SequenceMatcher(None, content_plain, tok).ratio() >= 0.85)):
            problems.append("plaintext already used in a past question")
            break
    return problems


def _norm(s: str) -> str:
    return re.sub(r"[^A-Z]", "", str(s).upper())


def _past_pool() -> list[str]:
    ws = load_workbook(TRACKING_XLSX)["Questions"]
    headers = [c.value for c in ws[1]]
    return [str(r["Original question text"]) for r in
            (dict(zip(headers, row)) for row in ws.iter_rows(min_row=2, values_only=True))]


def working_text(q: DraftQuestion) -> str:
    """Marking-scheme working: the arithmetic, not just the answer."""
    key = _parse_key(q.cipher, q.key)
    plain = C.clean(q.plaintext)
    ct = ciphertext(q)
    decrypt = q.task == "decrypt"
    # for decrypt questions walk the ciphertext backwards to the plaintext
    src, sign = (ct, -1) if decrypt else (plain, 1)
    lines = [f"Answer: {answer(q)}", "", "Working:"]
    if q.cipher == "caesar":
        shift = sign * key
        for ch in src:
            lines.append(f"  {ch} ({C.ALPHABET.index(ch):2}) "
                         f"{'+' if shift >= 0 else ''}{shift} mod 26 "
                         f"-> {C.ALPHABET[(C.ALPHABET.index(ch) + shift) % 26]}")
    elif q.cipher in ("vigenere", "vernam"):
        nums = ([C.ALPHABET.index(x) for x in key] if isinstance(key, str)
                else [n % 26 for n in key])
        for i, ch in enumerate(src):
            k = nums[i % len(nums)]
            out = C.ALPHABET[(C.ALPHABET.index(ch) + sign * k) % 26]
            lines.append(f"  {ch}({C.ALPHABET.index(ch):2}) "
                         f"{'+' if sign > 0 else '-'}{k:2} mod 26 -> {out}")
    elif q.cipher == "affine":
        a, b = key
        inv = pow(a, -1, 26)
        for ch in src:
            x = C.ALPHABET.index(ch)
            if not decrypt:
                lines.append(f"  {a}*{x} + {b} = {a * x + b} -> "
                             f"{(a * x + b) % 26} -> {C.ALPHABET[(a * x + b) % 26]}")
            else:
                lines.append(f"  {inv}*({x} - {b}) mod 26 = "
                             f"{(inv * (x - b)) % 26} -> {C.ALPHABET[(inv * (x - b)) % 26]}")
    elif q.cipher == "playfair":
        grid = C.playfair_grid(str(key))
        lines.append("  Grid (I/J merged):")
        lines.append("  " + " ".join(" ".join(row) for row in grid))
        lines.append(f"  {q.task} result: {answer(q)}")
    elif q.cipher == "columnar":
        lines.append(f"  Key: {key}; convention: fill rows, read columns "
                     f"(keyword: alphabetical rank order; pad X)")
        lines.append(f"  {q.task} result: {answer(q)}")
    return "\n".join(lines)


def _style_examples() -> str:
    return "\n".join([
        "Using Caesar Cipher technique, decrypt the following ciphertext.",
        "Based on Vernam Cipher, by using the random number 77, 49, 17 ... "
        "encrypt the following plaintext.",
        "Encrypt the message below using Playfair encryption with the key "
        "REDFOX.",
        "Decrypt the following ciphertext using columnar transposition with "
        "character 'z' as a padding character.",
        "Decrypt the ciphertext using affine cipher with key = (17,20). "
        "Show your work.",
    ])


def main() -> None:
    pool = _past_pool()
    target = {"caesar": 2, "vigenere": 2, "playfair": 2, "affine": 1,
              "columnar": 2, "vernam": 1}
    bank = _phrase_bank()
    accepted: list[DraftQuestion] = []
    attempts = 0
    last_problems: list[str] = []
    while len(accepted) < 10 and attempts < 90:
        attempts += 1
        user = _style_examples()
        if last_problems:
            user += ("\nYour previous draft was rejected because: "
                     + "; ".join(last_problems)
                     + ". Produce a different key or cipher.")
        decrypt_count = sum(1 for a in accepted if a.task == "decrypt")
        if decrypt_count < 3 and (attempts > 20 or len(accepted) >= 8):
            user += ("\nIMPORTANT: make the next question a DECRYPT task "
                     "(task must be 'decrypt').")
        try:
            data = chat_json(SYSTEM, user, model=DRAFT_MODEL)
            q = DraftQuestion(**data)
        except Exception as e:
            print(f"draft rejected (validation): {e}", flush=True)
            last_problems = [str(e)]
            continue
        if q.cipher not in target or target[q.cipher] <= 0:
            remaining = [c for c, n in target.items() if n > 0]
            last_problems = [f"cipher '{q.cipher}' is already filled; choose one "
                             f"of {remaining}"]
            continue
        # plaintext comes from the offline bank (seeded pick)
        rng = random.Random(1000 + attempts)
        start = rng.randrange(len(bank))
        for offset in range(len(bank)):
            q.plaintext = bank[(start + offset) % len(bank)]
            if not any("already used" in p for p in verify(q, pool)):
                break
        problems = verify(q, pool)
        if problems:
            last_problems = problems
            print(f"{q.cipher} draft failed: {problems}", flush=True)
            continue
        accepted.append(q)
        target[q.cipher] -= 1
        last_problems = []
        pool.append(q.plaintext)  # keys are freely reusable; phrases are not
        print(f"accepted {len(accepted)}: {q.cipher} {q.task} "
              f"'{q.plaintext}' ({q.marks}m) [model {DRAFT_MODEL}]", flush=True)

    OUTPUTS_DIR.mkdir(exist_ok=True)
    md = ["# Computed sample questions - classical ciphers\n",
          f"Drafted by the LLM (cipher/key/task/marks only, model {DRAFT_MODEL}); "
          "plaintexts picked from the offline phrase bank (data/phrases.json, "
          "seeded). Ciphertext, answers and working are all computed by code.\n",
          "Conventions:\n",
          "- Playfair I/J merge + X padding: **convention unverified** "
          "(pending lecture-slide confirmation).\n",
          "- Columnar explicit-rows grid (3 x 4 style): **convention unverified**.\n",
          "- Encrypt-only answers: **convention unverified** (no official keys "
          "exist).\n",
          "- Decrypt answers: readable plaintext; solvers validated on real "
          "past papers (7 cases, see src/generators/validate_solvers.py).\n"]
    for i, q in enumerate(accepted, 1):
        notes = []
        if q.task == "encrypt":
            notes.append("encrypt-only - convention unverified")
        if q.cipher == "playfair":
            notes.append("Playfair I/J merge + X padding: convention unverified")
        note = ("\n> Convention note: " + "; ".join(notes) + ".") if notes else ""
        md.append(f"## Question {i} ({q.marks} marks)\n")
        md.append("```\n" + render_question(q) + "\n```")
        md.append("```\n" + working_text(q) + "\n```" + note)
        md.append("")
    out = OUTPUTS_DIR / "computed_samples.md"
    out.write_text("\n".join(md), encoding="utf-8")
    structured = [{
        "cipher": q.cipher, "plaintext": q.plaintext, "key": q.key,
        "task": q.task, "marks": q.marks,
        "question": render_question(q), "answer": answer(q),
        "ciphertext": ciphertext(q),
        "working": working_text(q),
    } for q in accepted]
    (OUTPUTS_DIR / "computed_questions.json").write_text(
        json.dumps(structured, indent=2), encoding="utf-8")
    print(f"wrote {len(accepted)} questions -> {out} (+ computed_questions.json)")


if __name__ == "__main__":
    main()
