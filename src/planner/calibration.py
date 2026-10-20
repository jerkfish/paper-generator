"""Calibration of computed-question sizes from real CSC662 questions.

The real-question sample is thin at several mark values, so each row reports
the number of real examples n and, where n < 3, the widened mark range used.
Lengths are letters after removing spaces/punctuation; keys are the printed
key/column/rail values. "Steps" is the explicit working the solver prints
(per-letter mappings, Playfair pairs, columnar columns/rows, ACM views).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Calibration:
    kind: str
    marks: str
    n: int
    length_range: str
    key: str
    steps: str
    note: str = ""


CALIBRATIONS: list[Calibration] = [
    Calibration("caesar", "2", 1, "not printed (word)", "shift 4", "word length",
                "n=1 at 2m; widened 2-6m gives n=4, lengths 11-24"),
    Calibration("caesar", "6", 2, "11-38", "shift 7/18", "11-38 mappings",
                "n=2 at 6m; widened 4-6m gives n=3, lengths 11-38"),
    Calibration("vigenere", "6", 1, "13", "table/keyword", "13 table lookups",
                "n=1 at 6m; widened 3-10m gives n=3, lengths 13-18"),
    Calibration("columnar_3x4", "2-6", 3, "21-30", "4-5 columns / keyword",
                "columns + rows", "slide 3x4 demo is 12 cells; real examples "
                "are 21-30 letters"),
    Calibration("columnar_keyword", "6", 1, "21-30", "keyword (4-6 letters)",
                "columns + rows", "n=1 at 6m; widened 2-6m gives n=3"),
    Calibration("rail_fence", "6", 3, "21-34", "3-4 rails", "zigzag rows + read",
                "n=3 at 6m (2012, 2013, 2018)"),
    Calibration("otp", "6", 1, "12-13", "12 key numbers/letters",
                "12 modular additions", "n=1 at 6m; widened 5-6m gives n=2; "
                "still thin, keep lengths 12-13. 26-letter alphabet is "
                "verified against DEC 2019; slide 17 is inconsistent"),
    Calibration("acm", "6", 1, "4 users x 3 objects", "matrix only",
                "12 matrix cells", "6m = matrix only; 9m = matrix + ACL + CL "
                "(2015-06, 2016-12)"),
    Calibration("playfair", "6", 1, "10", "key REDFOX (6)", "5 pairs",
                "older style only; no current lecture slide"),
    Calibration("affine", "6", 1, "13", "key (17,20)", "13 inverse operations",
                "older style only; no current lecture slide"),
]


def calibration_for(kind: str, marks: int) -> Calibration | None:
    for row in CALIBRATIONS:
        if row.kind == kind and str(marks) in row.marks.split("-"):
            return row
    return None


def target_size(kind: str, marks: int) -> str:
    """Planner-facing target band (letters / key / grid)."""
    if kind == "caesar":
        return "11-15 letters; shift 7" if marks == 2 else "11-24 letters; shift"
    if kind == "vigenere":
        return ("13-18 letters; keyword 6-8 letters"
                if marks >= 6 else "10-13 letters; keyword 4-6 letters")
    if kind == "columnar_3x4":
        return "12 cells (3 rows x 4 columns); pad X"
    if kind == "columnar_keyword":
        return "21-30 letters; keyword 4-6 letters"
    if kind == "rail_fence":
        return ("19-34 letters; 3-4 rails" if marks >= 6
                else "10-15 letters; 3 rails")
    if kind == "otp":
        return "12-13 letters; 12 key numbers"
    if kind == "acm":
        return ("4 users x 3 objects; matrix only" if marks == 6
                else "matrix + ACL + CL")
    if kind == "playfair":
        return "10-12 letters; key 5-6; 5 x 5 grid, I/J merge, X filler"
    if kind == "affine":
        return "13-15 letters; key (a,b)"
    return ""
