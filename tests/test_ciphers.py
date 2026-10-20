"""Solver tests: hand-computed vectors + round-trips + key validation."""
from __future__ import annotations

import pytest

from src.generators.ciphers import (affine_decrypt, affine_encrypt, caesar_bruteforce,
                                    caesar_decrypt, caesar_encrypt, columnar_decrypt,
                                    columnar_encrypt, playfair_decrypt, playfair_encrypt,
                                    playfair_grid, railfence_decrypt, railfence_encrypt,
                                    single_transposition_decrypt,
                                    single_transposition_encrypt, vigenere_decrypt,
                                    vigenere_encrypt, vernam_decrypt, vernam_encrypt)


def test_caesar_vector_and_roundtrip():
    assert caesar_encrypt("ATTACK", 3) == "DWWDFN"
    assert caesar_decrypt("DWWDFN", 3) == "ATTACK"
    assert caesar_decrypt(caesar_encrypt("HELLO WORLD", 19), 19) == "HELLOWORLD"


def test_caesar_bruteforce_finds_shift():
    c = caesar_encrypt("THREAT", 3)
    assert (3, "THREAT") in caesar_bruteforce(c)


def test_caesar_shift_bounds():
    with pytest.raises(ValueError):
        caesar_encrypt("A", 0)
    with pytest.raises(ValueError):
        caesar_encrypt("A", 26)


def test_vigenere_vector():
    # hand-computed: ATTACK with key KEY -> K X R K G I
    assert vigenere_encrypt("ATTACK", "KEY") == "KXRKGI"
    assert vigenere_decrypt("KXRKGI", "KEY") == "ATTACK"


def test_vigenere_roundtrip_with_spaces():
    c = vigenere_encrypt("THIS IS SECRET", "LEMON")
    assert vigenere_decrypt(c, "LEMON") == "THISISSECRET"


def test_playfair_grid_merges_ij():
    grid = playfair_grid("MONARCHY")
    flat = "".join("".join(row) for row in grid)
    assert "J" not in flat and "I" in flat and len(flat) == 25


def test_playfair_vector():
    # hand-computed: key MONARCHY, plaintext ARMY -> RMNC
    # A(0,3) R(0,4) same row -> RM ; M(0,0) Y(1,2) rectangle -> NC
    assert playfair_encrypt("ARMY", "MONARCHY") == "RMNC"
    assert playfair_decrypt("RMNC", "MONARCHY") == "ARMY"


def test_playfair_doubled_letter_padding():
    c = playfair_encrypt("BALLOON", "MONARCHY")
    assert len(c) % 2 == 0
    assert playfair_decrypt(c, "MONARCHY").startswith("BAL")  # X may remain


def test_affine_vector():
    # hand-computed: (a=5, b=8) ATTACK -> IZZISG
    assert affine_encrypt("ATTACK", 5, 8) == "IZZISG"
    assert affine_decrypt("IZZISG", 5, 8) == "ATTACK"


def test_affine_requires_coprime():
    with pytest.raises(ValueError):
        affine_encrypt("A", 2, 0)


def test_columnar_numeric_vector():
    # derived rows: ATTACK, 4 columns -> 2 rows -> ACTKTXAX
    assert columnar_encrypt("ATTACK", 4) == "ACTKTXAX"
    assert columnar_decrypt("ACTKTXAX", 4) == "ATTACK"


def test_columnar_explicit_rows_vector():
    # lecture slides 20-21: 3 x 4 grid, ATTACK, pad X -> ACXTKXTXXAXX
    assert columnar_encrypt("ATTACK", 4, rows=3) == "ACXTKXTXXAXX"
    assert columnar_decrypt("ACXTKXTXXAXX", 4, rows=3) == "ATTACK"


def test_columnar_keyword_explicit_rows_slide_24():
    # lecture slide 24: key MATH, 3 x 4 grid, ATTACK -> TKXAXXACXTXX
    assert columnar_encrypt("ATTACK", "MATH", rows=3) == "TKXAXXACXTXX"
    assert columnar_decrypt("TKXAXXACXTXX", "MATH", rows=3) == "ATTACK"


def test_columnar_keyword_vector():
    # hand-computed: key CBA ranks C,B,A -> read col3,col2,col1 -> CFBEAD
    assert columnar_encrypt("ABCDEF", "CBA") == "CFBEAD"
    assert columnar_decrypt("CFBEAD", "CBA") == "ABCDEF"


def test_single_transposition_vector():
    # paper-validated: APR 2010 Q13 - key NED, pad Z, ILOVEYOUZ -> IVOLEUOYZ
    assert single_transposition_encrypt("ILOVEYOU", "NED", pad="Z") == "IVOLEUOYZ"
    assert single_transposition_decrypt("IVOLEUOYZ", "NED", pad="Z") == "ILOVEYOU"


def test_columnar_rows_derived():
    # 'five (5) rows' convention: rows given, columns derived (OCT 2006 Q2b)
    c = columnar_encrypt("HARI INI HARI SELASA YANG AMAT INDAH", None, rows=5)
    assert len(c) == 30
    assert columnar_decrypt(c, None, rows=5) == "HARIINIHARISELASAYANGAMATINDAH"


def test_columnar_pad_variant():
    c = columnar_encrypt("ATTACK", 4, pad="z")
    assert c.endswith("z")
    assert columnar_decrypt(c, 4, pad="z") == "ATTACK"


def test_vernam_vector():
    assert vernam_encrypt("ATTACK", [3, 3, 3, 3, 3, 3]) == "DWWDFN"
    assert vernam_decrypt("DWWDFN", [3, 3, 3, 3, 3, 3]) == "ATTACK"
    assert vernam_encrypt("ATTACK", "DDDDDD") == "DWWDFN"


def test_lecture_slide_caesar_examples():
    # slides 5-6 and 9: ATTACK <-> DWWDFN with shift 3
    assert caesar_encrypt("ATTACK", 3) == "DWWDFN"
    assert caesar_decrypt("DWWDFN", 3) == "ATTACK"
    assert caesar_decrypt("DWWDFN", 1) == "CVVCEM"
    assert caesar_decrypt("DWWDFN", 2) == "BUUBDL"


def test_lecture_slide_vigenere_example():
    # slide 15: ATTACK with key UNITUEUN -> UGBTWO
    assert vigenere_encrypt("ATTACK", "UNITUEUN") == "UGBTWO"
    assert vigenere_decrypt("UGBTWO", "UNITUEUN") == "ATTACK"


def test_lecture_slide_rail_fence_example():
    # slides 25-26: ATTACK with 3 rails -> ACTAKT
    assert railfence_encrypt("ATTACK", 3) == "ACTAKT"
    assert railfence_decrypt("ACTAKT", 3) == "ATTACK"


def test_lecture_slide_otp_example_is_inconsistent():
    # slide 17 prints ATTACK, key 18 6 3 9 18 6, ciphertext SYVJUQ.
    # The 26-letter reading gives SZWJUQ; the I/J-merged reading gives TZWKVQ.
    # Neither reproduces the printed row, so OTP stays unverified.
    assert vernam_encrypt("ATTACK", [18, 6, 3, 9, 18, 6]) == "SZWJUQ"
    assert vernam_encrypt("ATTACK", [18, 6, 3, 9, 18, 6],
                          ij_merge=True) == "TZWKVQ"


def test_railfence_vector():
    # slide vector: ATTACK with 3 rails -> ACTAKT
    assert railfence_encrypt("ATTACK", 3) == "ACTAKT"
    assert railfence_decrypt("ACTAKT", 3) == "ATTACK"


def test_railfence_roundtrip():
    c = railfence_encrypt("I AM STUDYING AT UITM", 3)
    assert railfence_decrypt(c, 3) == "IAMSTUDYINGATUITM"


def test_railfence_key_bounds():
    with pytest.raises(ValueError):
        railfence_encrypt("A", 1)


def test_vernam_bad_key():
    with pytest.raises(ValueError):
        vernam_encrypt("A", [])
    with pytest.raises(ValueError):
        vernam_encrypt("A", "K3Y")
