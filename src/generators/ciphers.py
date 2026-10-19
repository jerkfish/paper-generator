"""Pure-Python classical cipher solvers for the computed question module.

CONVENTIONS (documented so marking schemes can state them explicitly):
- Alphabet A-Z, A=0. Input case-insensitive; output uppercase, spaces and
  punctuation stripped (past papers print contiguous uppercase blocks).
- Caesar: shift k in 1..25; C = (P + k) mod 26.
- Vigenere: standard tableau (key letters repeated, A=0).
- Playfair: I and J share one cell (grid letter "I"); J in input is treated
  as I. Padding "X": inserted between doubled letters and at the end of an
  odd-length plaintext. Decryption CANNOT undo padding (ambiguous) - decrypt
  output may contain padding X; readability is checked instead.
- Affine: E(x) = (a*x + b) mod 26 with gcd(a, 26) == 1; D uses modular inverse.
- Columnar transposition:
  * numeric key n  -> n columns filled row-wise, read column by column
    left-to-right (padding fills the last row).
  * keyword key    -> columns read in alphabetical rank order of the key
    letters (ties: leftmost first). Pad character default "X"; past papers
    sometimes specify 'z' - the pad is a solver parameter.
- OTP/Vernam: key = list of numbers, applied mod 26 to successive letters
  (A=0). Letter keys are converted A..Z -> 0..25.
"""
from __future__ import annotations

import math
import re

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def clean(text: str) -> str:
    return re.sub(r"[^A-Z]", "", str(text).upper())


def _shift_char(ch: str, k: int) -> str:
    return ALPHABET[(ALPHABET.index(ch) + k) % 26]


def caesar_encrypt(plaintext: str, shift: int) -> str:
    if not 0 < shift < 26:
        raise ValueError("caesar shift must be in 1..25")
    return "".join(_shift_char(c, shift) for c in clean(plaintext))


def caesar_decrypt(ciphertext: str, shift: int) -> str:
    if not 0 < shift < 26:
        raise ValueError("caesar shift must be in 1..25")
    return "".join(_shift_char(c, -shift) for c in clean(ciphertext))


def caesar_bruteforce(ciphertext: str) -> list[tuple[int, str]]:
    c = clean(ciphertext)
    return [(k, "".join(_shift_char(x, -k) for x in c)) for k in range(1, 26)]


def vigenere_encrypt(plaintext: str, key: str) -> str:
    k = clean(key)
    if not k or len(k) < 3:
        raise ValueError("vigenere key must be >= 3 letters")
    out = []
    for i, ch in enumerate(clean(plaintext)):
        out.append(_shift_char(ch, ALPHABET.index(k[i % len(k)])))
    return "".join(out)


def vigenere_decrypt(ciphertext: str, key: str) -> str:
    k = clean(key)
    if not k or len(k) < 3:
        raise ValueError("vigenere key must be >= 3 letters")
    out = []
    for i, ch in enumerate(clean(ciphertext)):
        out.append(_shift_char(ch, -ALPHABET.index(k[i % len(k)])))
    return "".join(out)


def playfair_grid(key: str) -> list[list[str]]:
    k = clean(key).replace("J", "I")
    seen: list[str] = []
    for ch in k + ALPHABET.replace("J", ""):
        if ch not in seen:
            seen.append(ch)
    return [seen[i:i + 5] for i in range(0, 25, 5)]


def _grid_pos(grid: list[list[str]], ch: str) -> tuple[int, int]:
    ch = "I" if ch == "J" else ch
    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            if cell == ch:
                return r, c
    raise ValueError(f"character {ch!r} not in grid")


def playfair_encrypt(plaintext: str, key: str, pad: str = "X") -> str:
    if len(pad) != 1 or not pad.isalpha():
        raise ValueError("pad must be one letter")
    grid = playfair_grid(key)
    p = clean(plaintext).replace("J", "I")
    pairs = []
    i = 0
    while i < len(p):
        a = p[i]
        b = p[i + 1] if i + 1 < len(p) else pad
        if a == b:
            b = pad
            i += 1
        else:
            i += 2
        pairs.append((a, b))
    out = []
    for a, b in pairs:
        (r1, c1), (r2, c2) = _grid_pos(grid, a), _grid_pos(grid, b)
        if r1 == r2:
            out.append(grid[r1][(c1 + 1) % 5])
            out.append(grid[r2][(c2 + 1) % 5])
        elif c1 == c2:
            out.append(grid[(r1 + 1) % 5][c1])
            out.append(grid[(r2 + 1) % 5][c2])
        else:
            out.append(grid[r1][c2])
            out.append(grid[r2][c1])
    return "".join(out)


def playfair_decrypt(ciphertext: str, key: str) -> str:
    grid = playfair_grid(key)
    c = clean(ciphertext)
    if len(c) % 2 != 0:
        raise ValueError("playfair ciphertext must have even length")
    out = []
    for i in range(0, len(c), 2):
        a, b = c[i], c[i + 1]
        (r1, c1), (r2, c2) = _grid_pos(grid, a), _grid_pos(grid, b)
        if r1 == r2:
            out.append(grid[r1][(c1 - 1) % 5])
            out.append(grid[r2][(c2 - 1) % 5])
        elif c1 == c2:
            out.append(grid[(r1 - 1) % 5][c1])
            out.append(grid[(r2 - 1) % 5][c2])
        else:
            out.append(grid[r1][c2])
            out.append(grid[r2][c1])
    return "".join(out)


def affine_encrypt(plaintext: str, a: int, b: int) -> str:
    if math.gcd(a, 26) != 1:
        raise ValueError(f"affine key a={a} must be coprime with 26")
    out = []
    for ch in clean(plaintext):
        out.append(ALPHABET[(a * ALPHABET.index(ch) + b) % 26])
    return "".join(out)


def affine_decrypt(ciphertext: str, a: int, b: int) -> str:
    if math.gcd(a, 26) != 1:
        raise ValueError(f"affine key a={a} must be coprime with 26")
    inv = pow(a, -1, 26)
    out = []
    for ch in clean(ciphertext):
        out.append(ALPHABET[(inv * (ALPHABET.index(ch) - b)) % 26])
    return "".join(out)


def _column_order(key: str | int) -> list[int]:
    """Reading order of columns. int n -> 0..n-1; keyword -> alphabetical rank."""
    if isinstance(key, int):
        if key < 2:
            raise ValueError("column count must be >= 2")
        return list(range(key))
    k = clean(key)
    if len(k) < 3:
        raise ValueError("keyword key must be >= 3 letters")
    return [i for i, _ in sorted(enumerate(k), key=lambda t: (k[t[0]], t[0]))]


def columnar_encrypt(plaintext: str, key: str | int, pad: str = "X",
                     rows: int | None = None) -> str:
    """Fill rows left-to-right, read columns in `order`. Numeric key = column
    count; keyword key = rank-ordered columns. `rows` may state the grid size
    explicitly (papers do, e.g. 'five (5) rows')."""
    if len(pad) != 1 or not pad.isalpha():
        raise ValueError("pad must be one letter")
    p = clean(plaintext)
    if key is None and rows is not None:
        n = math.ceil(len(p) / rows)
        order = list(range(n))
        nrows = rows
    elif isinstance(key, str):
        order = _column_order(key)
        n, nrows = len(order), math.ceil(len(p) / len(order))
    else:
        order = _column_order(int(key))
        n = len(order)
        nrows = rows if rows is not None else math.ceil(len(p) / n)
    if n * nrows < len(p):
        raise ValueError(f"grid {nrows}x{n} too small for {len(p)} chars")
    row_chunks = [p[i:i + n] for i in range(0, len(p), n)]
    if row_chunks and len(row_chunks[-1]) < n:
        row_chunks[-1] += pad * (n - len(row_chunks[-1]))
    if len(row_chunks) < nrows:
        row_chunks.extend([pad * n] * (nrows - len(row_chunks)))
    cols = ["".join(row[ci] for row in row_chunks if ci < len(row)) for ci in range(n)]
    return "".join(cols[ci] for ci in order)


def columnar_decrypt(ciphertext: str, key: str | int, pad: str = "X",
                     rows: int | None = None) -> str:
    c = clean(ciphertext)
    if key is None and rows is not None:
        n = math.ceil(len(c) / rows)
        order = list(range(n))
        nrows = rows
    elif isinstance(key, str):
        order = _column_order(key)
        n, nrows = len(order), math.ceil(len(c) / len(order))
    else:
        order = _column_order(int(key))
        n = len(order)
        nrows = rows if rows is not None else math.ceil(len(c) / n)
    total = nrows * n
    given = len(c)
    c += pad.upper() * (total - given)  # restore cells truncated by transport
    short_cols = total - given
    cols: dict[int, str] = {}
    pos = 0
    for rank, ci in enumerate(order):
        length = nrows - (1 if rank >= n - short_cols else 0)
        cols[ci] = c[pos:pos + length]
        pos += length
    out = []
    for r in range(nrows):
        for ci in range(n):
            if r < len(cols[ci]):
                out.append(cols[ci][r])
    return "".join(out).rstrip(pad.upper())


def single_transposition_encrypt(plaintext: str, key: str, pad: str = "X") -> str:
    """'Single transposition' as the papers use it: plaintext is written INTO
    columns in key-letter order, then read out row by row (columns displayed
    sorted by key). Validated against APR 2010 Q13 (key NED, pad Z)."""
    if len(pad) != 1 or not pad.isalpha():
        raise ValueError("pad must be one letter")
    order = _column_order(key)
    n = len(order)
    p = clean(plaintext)
    col_len = math.ceil(len(p) / n)
    cols = []
    for rank in range(n):
        chunk = p[rank * col_len:(rank + 1) * col_len]
        cols.append(chunk + pad.upper() * (col_len - len(chunk)))
    out = []
    for r in range(col_len):
        for rank in range(n):
            out.append(cols[rank][r])
    return "".join(out)


def single_transposition_decrypt(ciphertext: str, key: str, pad: str = "X") -> str:
    order = _column_order(key)
    n = len(order)
    c = clean(ciphertext)
    rows_n = math.ceil(len(c) / n)
    rows = [c[i * n:(i + 1) * n] for i in range(rows_n)]
    cols = ["".join(row[rank] for row in rows if rank < len(row))
            for rank in range(n)]
    return "".join(cols).rstrip(pad.upper())


def vernam_encrypt(plaintext: str, key: list[int] | str) -> str:
    nums = _vernam_numbers(key)
    out = []
    for i, ch in enumerate(clean(plaintext)):
        out.append(_shift_char(ch, nums[i % len(nums)] % 26))
    return "".join(out)


def vernam_decrypt(ciphertext: str, key: list[int] | str) -> str:
    nums = _vernam_numbers(key)
    out = []
    for i, ch in enumerate(clean(ciphertext)):
        out.append(_shift_char(ch, -(nums[i % len(nums)] % 26)))
    return "".join(out)


def _vernam_numbers(key: list[int] | str) -> list[int]:
    if isinstance(key, str):
        if not key.isalpha():
            raise ValueError("letter key must be A-Z")
        return [ALPHABET.index(ch) for ch in clean(key)]
    if not key or not all(isinstance(n, (int, float)) for n in key):
        raise ValueError("numeric key must be a non-empty list of numbers")
    return [int(n) for n in key]


SOLVER_CONVENTIONS = {
    "caesar": "A=0; shift k in 1..25; ciphertext letters are shifted k forward. "
              "Decrypt = shift back by k.",
    "vigenere": "Standard Vigenere tableau, A=0; key repeated over the message.",
    "playfair": "I and J share one cell (written I). Pad 'X' inserted between "
                "doubled letters and to complete a final odd pair. Decryption "
                "cannot remove padding reliably - readability is checked.",
    "affine": "E(x)=(a*x+b) mod 26 with gcd(a,26)=1; decrypt uses the modular "
              "inverse of a.",
    "columnar": "Numeric key = column count, read left-to-right. Keyword key = "
                "columns read in alphabetical rank (ties: leftmost first). "
                "Rows = ceil(len/columns) unless the paper states the matrix "
                "size - '3 x 4' -> columns=4, rows=3; 'five (5) rows' -> "
                "rows=5, columns derived (key=None). Pad character fills the "
                "final row (default 'X'; papers also use 'z').",
    "single transposition": "Plaintext is written INTO columns in key-letter "
                            "order and read out row by row (columns displayed "
                            "sorted by key). Validated against APR 2010 Q13.",
    "vernam": "Key numbers applied mod 26 to successive letters (A=0). Letter "
              "keys map A-Z to 0-25.",
}
