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

import math
import re
from difflib import SequenceMatcher

from openpyxl import load_workbook
from pydantic import BaseModel, Field

from src.config import OUTPUTS_DIR, TRACKING_XLSX
from src.generators import ciphers as C
from src.llm import chat_json

CIPHERS = ("caesar", "vigenere", "playfair", "affine", "columnar", "vernam")
ALLOWED_MARKS = (2, 6)


class DraftQuestion(BaseModel):
    cipher: str
    plaintext: str = Field(min_length=4)
    key: str = Field(min_length=1)
    task: str
    marks: int


SYSTEM = """You draft exam questions for a computer-security course's cipher drills.
Output ONE JSON object exactly:
{"cipher": "caesar|vigenere|playfair|affine|columnar|vernam",
 "plaintext": "short meaningful message, 5-25 letters, English or Malay, often
  security-themed (papers use things like 'THIS IS SECRET', 'I LOVE NETWORK
  SECURITY', 'SELAMAT HARI RAYA')",
 "key": "see formats below",
 "task": "encrypt|decrypt",
 "marks": 2 or 6}
Key formats: caesar -> "shift=7"; vigenere/playfair -> a word of >=3 letters;
affine -> "(a,b)" with a coprime to 26, e.g. "(17,20)"; columnar -> a keyword
of >=3 letters OR a column count 2-10; vernam -> space-separated numbers,
e.g. "3 6 12 9 4" (at least 6 numbers).
Rules: never include any ciphertext in your output. Vary ciphers across calls
(also produce decrypt tasks - the plaintext you give is the readable answer).
Style reference (tone only, do not copy):
- "Using Caesar Cipher technique, decrypt the following ciphertext."
- "Encrypt the plaintext below using Vigenere cipher with the given key."
- "Encrypt the message using Playfair encryption. Show your work."
- "Decrypt the ciphertext using affine cipher with key (a, b). Show your work."
- "Using columnar transposition, encrypt the plaintext below."
- "Based on Vernam cipher, using the given random numbers encrypt the plaintext."
Return only the JSON object."""


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
        return (f"Using Caesar Cipher technique, encrypt the following plaintext "
                f"with shift {q.key}.\n{p}\n({q.marks} marks)")
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
    ok, why = _meaningful(plain)
    if not ok:
        problems.append(f"plaintext not meaningful: {why}")
    if q.cipher == "vernam" and key and len(key) < len(plain):
        problems.append("vernam key shorter than plaintext")
    try:
        ciphertext(q)
        answer(q)
    except Exception as e:
        problems.append(f"solver error: {e}")
    # near-copy check: compare the CONTENT (plaintext/key), not the template
    content = _norm(q.plaintext) + _norm(q.key)
    for past in pool:
        if not content or len(content) < 6:
            break
        if content in past:
            problems.append("plaintext/key already used in a past question")
            break
        match = SequenceMatcher(None, content, past).find_longest_match(
            0, len(content), 0, len(past)).size
        if match >= 0.9 * len(content):
            problems.append("near-copy of a past question")
            break
    if q.task == "decrypt" and len(plain) < 5:
        problems.append("decrypt plaintext too short")
    return problems


def _norm(s: str) -> str:
    return re.sub(r"[^A-Z]", "", str(s).upper())


def _past_pool() -> list[str]:
    ws = load_workbook(TRACKING_XLSX)["Questions"]
    headers = [c.value for c in ws[1]]
    return [_norm(r["Original question text"]) for r in
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
    accepted: list[DraftQuestion] = []
    attempts = 0
    last_problems: list[str] = []
    while len(accepted) < 10 and attempts < 40:
        attempts += 1
        user = _style_examples()
        if last_problems:
            user += ("\nYour previous draft was rejected because: "
                     + "; ".join(last_problems)
                     + ". Produce a DIFFERENT plaintext and key.")
        try:
            data = chat_json(SYSTEM, user)
            q = DraftQuestion(**data)
        except Exception as e:
            print(f"draft rejected (validation): {e}", flush=True)
            last_problems = [str(e)]
            continue
        if q.cipher not in target or target[q.cipher] <= 0:
            continue
        problems = verify(q, pool)
        if problems:
            last_problems = problems
            print(f"{q.cipher} draft failed: {problems}", flush=True)
            continue
        accepted.append(q)
        target[q.cipher] -= 1
        last_problems = []
        pool.append(_norm(q.plaintext) + _norm(q.key))  # avoid self-duplicates
        print(f"accepted {len(accepted)}: {q.cipher} {q.task} "
              f"'{q.plaintext}' ({q.marks}m)", flush=True)

    OUTPUTS_DIR.mkdir(exist_ok=True)
    md = ["# Computed sample questions - classical ciphers\n",
          "Drafted by the LLM (fields only); ciphertext, answers and working "
          "computed by code. Decrypt answers are readable plaintext; encrypt-only "
          "results are marked 'convention unverified' (no official keys exist).\n"]
    for i, q in enumerate(accepted, 1):
        note = "" if q.task == "decrypt" else \
            "\n> Convention note: encrypt-only - convention unverified."
        md.append(f"## Question {i} ({q.marks} marks)\n")
        md.append("```\n" + render_question(q) + "\n```")
        md.append("```\n" + working_text(q) + "\n```" + note)
        md.append("")
    out = OUTPUTS_DIR / "computed_samples.md"
    out.write_text("\n".join(md), encoding="utf-8")
    print(f"wrote {len(accepted)} questions -> {out}")


if __name__ == "__main__":
    main()
