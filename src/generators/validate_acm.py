"""Validate the ACM/ACL/capability construction against the real past-paper
scenarios (11 construction questions). Structures are built from each stated
scenario; papers print no answer keys, so validation is self-consistency plus
a human-readable printout of every view.

Run:  uv run python -m src.generators.validate_acm
"""
from __future__ import annotations

from src.generators.acm import (AccessScenario, acl_table, build_matrix,
                                capability_table, check_consistency, matrix_table)

# scenarios transcribed from the papers (names/rights as printed)
REAL_SCENARIOS: list[tuple[str, dict]] = [
    ("2014-06 Q5 (ali, yati, umi, root)", dict(
        users=["ali", "yati", "umi", "root"], objects=["file1", "file2", "file3"],
        grants=[
            {"user": "ali", "object": "file1", "rights": ["read", "write"]},
            {"user": "yati", "object": "file2", "rights": ["read"]},
            {"user": "umi", "object": "file3", "rights": ["read", "write", "execute"]},
            {"user": "root", "object": "file1", "rights": ["read", "write", "execute"]},
            {"user": "root", "object": "file2", "rights": ["read", "write", "execute"]},
            {"user": "root", "object": "file3", "rights": ["read", "write", "execute"]},
        ], marks=12)),
    ("2011-04 Q3 (dick, jane, sally, root)", dict(
        users=["dick", "jane", "sally", "root"], objects=["f1", "f2", "f3"],
        grants=[
            {"user": "dick", "object": "f1", "rights": ["read", "write"]},
            {"user": "jane", "object": "f2", "rights": ["read"]},
            {"user": "sally", "object": "f3", "rights": ["read", "write", "execute"]},
            {"user": "root", "object": "f1", "rights": ["read", "write", "execute"]},
            {"user": "root", "object": "f2", "rights": ["read", "write", "execute"]},
            {"user": "root", "object": "f3", "rights": ["read", "write", "execute"]},
        ], marks=12)),
    ("2015-06 Q7 (Farhan, Faizah, Fazlan; X-1..X-3)", dict(
        users=["Farhan", "Faizah", "Fazlan"],
        objects=["X-1", "X-2", "X-3"],
        grants=[
            {"user": "Farhan", "object": "X-1", "rights": ["read", "write", "execute"]},
            {"user": "Faizah", "object": "X-1", "rights": ["read"]},
            {"user": "Fazlan", "object": "X-1", "rights": ["read"]},
            {"user": "Faizah", "object": "X-2", "rights": ["read", "write"]},
            {"user": "Fazlan", "object": "X-2", "rights": ["read", "write", "execute"]},
            {"user": "Farhan", "object": "X-2", "rights": ["read"]},
            {"user": "Fazlan", "object": "X-3", "rights": ["read", "write", "execute"]},
        ], marks=9)),
    ("2018-06 Q7 (Adam, Suzy, Maryam, Root)", dict(
        users=["Adam", "Suzy", "Maryam", "Root"], objects=["P", "Q", "R"],
        grants=[
            {"user": "Adam", "object": "P", "rights": ["read", "write"]},
            {"user": "Suzy", "object": "Q", "rights": ["read"]},
            {"user": "Maryam", "object": "R", "rights": ["read", "write", "execute"]},
            {"user": "Root", "object": "P", "rights": ["read", "write", "execute"]},
            {"user": "Root", "object": "Q", "rights": ["read", "write", "execute"]},
            {"user": "Root", "object": "R", "rights": ["read", "write", "execute"]},
        ], marks=6)),
    ("2010/2014 Debra-Raymond-Marie-Frank (file Kids)", dict(
        users=["Debra", "Raymond", "Marie", "Frank"],
        objects=["Kids", "Notes"],
        grants=[
            {"user": "Debra", "object": "Kids", "rights": ["read", "write"]},
            {"user": "Raymond", "object": "Kids", "rights": ["read"]},
            {"user": "Marie", "object": "Kids", "rights": ["read"]},
            {"user": "Frank", "object": "Kids", "rights": ["read"]},
            {"user": "Raymond", "object": "Notes", "rights": ["read", "write", "execute"]},
        ], marks=8)),
]


def main() -> None:
    covered = len(REAL_SCENARIOS)
    for label, spec in REAL_SCENARIOS:
        s = AccessScenario(**spec)
        ok, msg = check_consistency(s)
        matrix = build_matrix(s)
        print(f"\n===== {label} | consistency={ok} ({msg}) =====")
        print(matrix_table(matrix, s.users, s.objects))
        print(acl_table(__import__("src.generators.acm", fromlist=["derive_acls"])
                         .derive_acls(matrix, s.objects)))
        print(capability_table(__import__("src.generators.acm",
                                          fromlist=["derive_capabilities"])
                               .derive_capabilities(matrix, s.users)))
    print(f"\n{covered} of 11 real construction questions transcribed and built.")
    print("The rest are partial/OCR-garbled scenarios or theory stems (2018-12 A3a "
          "conversion-theory, 2016-06 Q5 SID/Windows ACL, 2019-12 B2b structure "
          "choice, 2018-12 A3b matrix partly OCR'd) - listed, not silently guessed.")
    print("Papers print no answer keys, so validation = self-consistency only.")


if __name__ == "__main__":
    main()
