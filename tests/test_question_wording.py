"""Paper stems must state the key/grid/filler and the slide's method wording."""
from __future__ import annotations

from src.assemble.build_docx_paper import build_slots, paper_question


def test_caesar_stem_states_shift_and_direction():
    q = build_slots()["Q2a"]
    stem = paper_question(q, include_marks=False)
    assert "shift of 7" in stem
    assert "positions to the left" in stem
    assert q["ciphertext"] in stem
    assert "(2 marks)" not in stem
    assert "(2 marks)" in paper_question(q)


def test_playfair_stem_states_grid_ij_and_filler():
    q = build_slots()["Q2b"]
    stem = paper_question(q, include_marks=False)
    assert "key REDFOX" in stem
    assert "5 x 5" in stem
    assert "merge I and J" in stem
    assert "filler" in stem
    assert q["plaintext"] in stem


def test_columnar_stem_states_grid_fill_read_and_filler():
    q = build_slots()["Q5b"]
    stem = paper_question(q, include_marks=False)
    assert "3 x 4 matrix" in stem
    assert "3 rows, 4 columns" in stem
    assert "into the columns" in stem
    assert "out of the rows" in stem
    assert "filler X" in stem
    assert "column size, 4" in stem
    assert q["ciphertext"] in stem


def test_unused_ciphers_also_state_their_convention():
    v = paper_question({"cipher": "vigenere", "key": "LEMON", "marks": 6,
                        "ciphertext": "LXFOPV", "task": "decrypt"})
    assert "standard 26 x 26 Vigenere tableau" in v
    a = paper_question({"cipher": "affine", "key": "(5,8)", "marks": 6,
                        "ciphertext": "IZZISG", "task": "decrypt"})
    assert "modular inverse" in a


def test_part_headings_include_mark_totals():
    from src.assemble.build_docx_paper import PART_A_HEADING, PART_B_HEADING
    assert PART_A_HEADING == "PART A (80 MARKS)"
    assert PART_B_HEADING == "PART B (20 MARKS)"
