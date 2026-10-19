"""Step-by-step working for the marking scheme.

Caesar / Vigenere / affine / Vernam already have detailed working in
outputs/computed_questions.json. Playfair and columnar only stored the grid
and result, so this module derives the pair/column steps from the same
solvers used to generate the questions.
"""
from __future__ import annotations

import math

from src.generators import ciphers as C
from src.generators.computed_type1 import ciphertext


def playfair_working(plaintext: str, key: str, pad: str = "X") -> str:
    """Encrypt working: 5x5 grid, padded pairs, rule used for each pair."""
    grid = C.playfair_grid(key)
    p = C.clean(plaintext).replace("J", "I")
    pairs: list[tuple[str, str]] = []
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

    lines = [f"Answer: {C.playfair_encrypt(plaintext, key, pad)}", "", "Working:"]
    lines.append("  Grid (I/J merged):")
    for row in grid:
        lines.append("    " + " ".join(row))
    lines.append("  Padded pairs: " + "  ".join(a + b for a, b in pairs))
    for a, b in pairs:
        (r1, c1), (r2, c2) = C._grid_pos(grid, a), C._grid_pos(grid, b)
        if r1 == r2:
            out = grid[r1][(c1 + 1) % 5] + grid[r2][(c2 + 1) % 5]
            rule = f"same row {r1 + 1}: shift right"
        elif c1 == c2:
            out = grid[(r1 + 1) % 5][c1] + grid[(r2 + 1) % 5][c2]
            rule = f"same column {c1 + 1}: shift down"
        else:
            out = grid[r1][c2] + grid[r2][c1]
            rule = f"rectangle ({r1 + 1},{c1 + 1})-({r2 + 1},{c2 + 1}): swap columns"
        lines.append(f"  {a}{b} -> {out}   ({rule})")
    lines.append(f"  Ciphertext: {C.playfair_encrypt(plaintext, key, pad)}")
    return "\n".join(lines)


def columnar_decrypt_working(ciphertext: str, key: str | int,
                             pad: str = "X",
                             rows: int | None = None) -> str:
    """Decrypt working: key ranking, column lengths, reconstructed rows.
    Numeric keys mean the column count; `rows` states an explicit grid
    (the course's 3 x 4 convention)."""
    c = C.clean(ciphertext)
    if key is None:
        raise ValueError("scheme working expects a keyword/numeric key")
    if isinstance(key, str) and key.strip().isdigit():
        key = int(key.strip())
    numeric = isinstance(key, int)
    order = C._column_order(key)
    n = len(order)
    nrows = rows if rows is not None else math.ceil(len(c) / n)
    total = nrows * n
    short = total - len(c)          # number of transport pad characters
    c_pad = c + pad.upper() * short
    cols: dict[int, str] = {}
    pos = 0
    for rank, ci in enumerate(order):
        length = nrows - (1 if rank >= n - short else 0)
        cols[ci] = c_pad[pos:pos + length]
        pos += length

    rows_out = []
    for r in range(nrows):
        rows_out.append("".join(cols[ci][r] if r < len(cols[ci]) else ""
                                for ci in range(n)))
    row_text = "".join(rows_out)
    plain = row_text.rstrip(pad.upper())
    trailing = len(row_text) - len(plain)

    lines = [f"Answer: {plain}", "", "Working:"]
    if numeric:
        ranked = ", ".join(f"col {ci + 1}" for ci in order)
        lines.append(f"  Numeric key: {n} columns; grid {nrows} rows x {n} "
                     f"columns; read order: {ranked}")
        col_labels = [f"col {ci + 1}" for ci in order]
    else:
        key_label = str(key)
        ranked = ", ".join(f"col {ci + 1} ({key_label[ci].upper()})"
                           for ci in order)
        lines.append(f"  Keyword: {key_label.upper()}; read order: {ranked}")
        col_labels = [f"col {ci + 1} ({key_label[ci].upper()})"
                      for ci in order]
    lines.append(f"  Grid: {n} columns x {nrows} rows ({total} cells; "
                 f"ciphertext {len(c)} chars; transport pad {short})")
    lines.append("  Ciphertext split in read order:")
    for label, ci in zip(col_labels, order):
        lines.append(f"    {label}: {cols[ci]}")
    lines.append("  Reconstructed rows:")
    for r, row in enumerate(rows_out):
        lines.append(f"    row {r + 1}: {row}")
    lines.append(f"  Row-wise: {row_text}")
    lines.append(f"  Remove {trailing} trailing pad '{pad.upper()}': {plain}")
    return "\n".join(lines)


def working_for(q: dict) -> str:
    """Pick the right working formatter for a computed question dict."""
    if q["cipher"] == "playfair":
        return playfair_working(q["plaintext"], q["key"])
    if q["cipher"] == "columnar" and q["task"] == "decrypt":
        return columnar_decrypt_working(q["ciphertext"], q["key"],
                                        rows=q.get("rows"))
    return q.get("working") or ""


def confidence_for(q: dict) -> str:
    if q["cipher"] == "playfair":
        return ("convention unverified - no lecture slide covers Playfair; "
                "I/J merge + X padding still to be confirmed")
    if q["cipher"] == "affine":
        return ("convention unverified - no lecture slide covers the affine "
                "cipher")
    if q["cipher"] == "columnar":
        return ("computed - 3 x 4 fill-rows/read-columns convention verified "
                "against lecture slides 20-21 and 24")
    if q["cipher"] == "caesar":
        return ("computed - matches lecture slides 5-9 (Caesar shift 3 "
                "examples)")
    if q["cipher"] == "vigenere":
        return "computed - matches lecture slide 15 (standard tableau)"
    if q["cipher"] == "vernam":
        return ("convention unverified - lecture slide 17 table mixes the "
                "I/J-merged and 26-letter alphabets")
    if q["cipher"] == "rail fence":
        return "computed - matches lecture slides 25-26"
    return "computed - solver validated on real past papers"


def mark_guidance_for(q: dict) -> str:
    if q["cipher"] == "playfair":
        return ("1 mark for the correct 5x5 grid; 1 mark for correct pairing/"
                "padding; 4 marks for the ciphertext pairs.")
    if q["cipher"] == "columnar":
        return ("1 mark for the key column order; 2 marks for reconstructing "
                "the columns; 2 marks for the row-wise plaintext; 1 mark for "
                "stripping the padding.")
    if q["marks"] == 2:
        return ("1 mark for identifying the cipher/shift direction; 1 mark for "
                "the complete plaintext.")
    return ("1 mark for the key/table setup; 4 marks for the letter-by-letter "
            "working; 1 mark for the complete answer.")


def _selftest() -> None:
    import json
    qs = json.loads(open("outputs/computed_questions.json", encoding="utf-8").read())
    for q in qs:
        w = working_for(q)
        assert w, q["cipher"]
        first = w.splitlines()[0]
        expected = q["answer"]
        assert first == f"Answer: {expected}", (q["cipher"], first, expected)
    print("scheme_working selftest: all computed answers match")


if __name__ == "__main__":
    _selftest()
