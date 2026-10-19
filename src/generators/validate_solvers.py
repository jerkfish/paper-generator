"""Validate the classical-cipher solvers against REAL past-paper questions.

Decrypt cases are judged on readability (human checks the printed output);
encrypt-only cases are flagged 'convention unverified' - no official answer
key exists for these papers.

Run:  uv run python -m src.generators.validate_solvers
"""
from __future__ import annotations

from src.generators import ciphers as C

# (label, kind, fn) - fn prints/returns solver output for a real paper question
CASES: list[tuple[str, str, object]] = []


def _caesar_brute(label, ciphertext):
    print(f"[{label}] Caesar brute-force decrypt of {ciphertext}:")
    for k, t in C.caesar_bruteforce(ciphertext):
        print(f"    shift {k:2}: {t}")


def _decrypt(label, fn, *args, **kwargs):
    try:
        print(f"[{label}] -> {fn(*args, **kwargs)}")
    except Exception as e:
        print(f"[{label}] !! solver error: {e}")


def _encrypt(label, fn, *args, **kwargs):
    try:
        print(f"[{label}] (encrypt-only, convention unverified) -> {fn(*args, **kwargs)}")
    except Exception as e:
        print(f"[{label}] !! solver error: {e}")


def main() -> None:
    print("=== DECRYPT cases (readability judged below) ===")
    _caesar_brute("2006-10 Q2a Caesar decrypt (shift not stated)", "wuhdwblpsrvvleoh")
    _decrypt("2006-10 Q2d iii Vigenere decrypt key=kuntum",
             C.vigenere_decrypt, "cyytgmrueblmlu", "kuntum")
    _decrypt("2010-04 Q13 single-transposition decrypt keyword=NED pad=Z",
             C.single_transposition_decrypt, "IVOLEUOYZ", "NED", pad="Z")
    _decrypt("2011-04 Q7 single-transposition decrypt cols=5 (key unclear)",
             C.single_transposition_decrypt, "ACRYSRASEYPTCPHEUTIMROCZEGSZ",
             "ABCDE", pad="Z")
    _decrypt("2014-12 Q4b affine decrypt key=(17,20)",
             C.affine_decrypt, "FEKHFMBABFKKH", 17, 20)
    _decrypt("2016-12 Q7 Caesar decrypt shift=7",
             C.caesar_decrypt, "SHCPLLUYVZL", 7)
    _decrypt("2017-07 Q6d Caesar decrypt shift=4",
             C.caesar_decrypt, "XVYWXIHGSQTYXMRKXIGLRSPSKC", 4)
    _decrypt("2019-12 A4b OTP decrypt key=CRYPTOGRAPHY",
             C.vernam_decrypt, "EIWEMOTRLNZGU", "CRYPTOGRAPHY")
    _decrypt("2018-01 Q10 columnar decrypt pad=D (cols=4 guessed, key unclear)",
             C.columnar_decrypt, "AEICCRTTOSYSMESDPCUDUUBDTRJD", 4, pad="D")

    print("\n=== ENCRYPT-only cases (convention unverified) ===")
    _encrypt("2006-10 Q2b columnar rows=5 (cols derived)", C.columnar_encrypt,
             "HARI INI HARI SELASA YANG AMAT INDAH", None, rows=5)
    _encrypt("2006-10 Q2c Vernam numbers", C.vernam_encrypt, "GOODLUCKBABY",
             [77, 49, 17, 83, 44, 3, 58, 11, 60, 7, 49, 89])
    _encrypt("2006-10 Q2d i Vigenere key=pusing", C.vigenere_encrypt,
             "TEPUK AMAI AMAI BELALANG KUPU", "pusing")
    _encrypt("2006-10 Q2d ii Vigenere key=gasing", C.vigenere_encrypt,
             "TIMANG TINGGI SAMPAI PUCUK ATAP TAU", "gasing")
    _encrypt("2010-10 Q13 Vigenere key=COMPUTER", C.vigenere_encrypt,
             "TO BE OR NOT TO BE", "COMPUTER")
    _encrypt("2013-12 Q13 Vigenere key=COMPUTER", C.vigenere_encrypt,
             "AN ATTACK FROM NORTH", "COMPUTER")
    _encrypt("2015-06 Q10 Caesar shift=19", C.caesar_encrypt,
             "THE FAULT, DEAR BRUTUS, LIES NOT IN OUR STARS BUT IN OURSELVES", 19)
    _encrypt("2015-12 Q10 Caesar shift=18", C.caesar_encrypt,
             "MY DEAR FRIEND, DO NOT FIND FAULT, FIND A REMEDY", 18)
    _encrypt("2016-12 Q8 Playfair key=REDFOX", C.playfair_encrypt,
             "LESS IS MORE", "REDFOX")
    _encrypt("2017-07 Q6b columnar keyword=MALAYSIA", C.columnar_encrypt,
             "I LOVE NETWORK SECURITY", "MALAYSIA")
    _encrypt("2019-06 A4b columnar key=4", C.columnar_encrypt, "CRYPTOGRAPHY", 4)

    print("\n=== NOT SUPPORTED by current solvers (listed honestly) ===")
    for note in [
        "rail-fence (5 questions: 2012-06 Q7b, 2013-12 Q4b, 2017-07 Q6c, "
        "2018-01 Q13a, 2018-06 Q10) - not in approved scope",
        "autokey cipher (2014-06 Q8 decrypt, 2014-12 Q4a encrypt)",
        "custom poly-alphabetic odd+3/even-3 (2012-01 Q4c, 2016-06 Q9, 2011-04 Q17)",
        "custom substitution table (2019-06 A4b part 1)",
        "custom letter-number key mapping A-07..X-02 (2012-01 Q14a)",
        "pseudo-code writing (2012-06 Q7a, 2013-12 Q4a, 2015-06 Q9a) - no inputs",
        "2026-02 A3a Caesar shift 4 - plaintext word not visible in extracted text",
        "2018-01 Q10 columnar - key/columns not stated in extracted text",
        "2017-07 Q10 Vigenere - key garbled by OCR (table image)",
    ]:
        print(f"  - {note}")


if __name__ == "__main__":
    main()
