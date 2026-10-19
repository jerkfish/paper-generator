"""Era check: per-paper year / computed sum / era / structure, proposed era
boundaries from structural changes, and a labelled near-clean view (sum 94-106).

Also recomputes the "Paper marks check" sheet after question recovery so sums
stay in sync with the Questions sheet.

Run:  uv run python -m src.fingerprint.era_check
"""
from __future__ import annotations

import re
from collections import defaultdict

from openpyxl import load_workbook

from src.config import TRACKING_XLSX


def _sheet(name: str) -> list[dict]:
    ws = load_workbook(TRACKING_XLSX)[name]
    headers = [c.value for c in ws[1]]
    return [dict(zip(headers, row)) for row in ws.iter_rows(min_row=2, values_only=True)]


def _sums(rows: list[dict]) -> dict[str, float]:
    out: dict[str, float] = defaultdict(float)
    for r in rows:
        if r["Marks"] is not None:
            out[r["Paper ID"]] += float(r["Marks"])
    return out


def _structure(rows: list[dict]) -> dict[str, dict]:
    per: dict[str, dict] = defaultdict(lambda: {"parts": 1, "nq": set(), "so": 0, "n": 0})
    for r in rows:
        s = per[r["Paper ID"]]
        q = str(r["Q no."])
        if re.match(r"^[A-Z]", q):
            s["parts"] = 2
        m = re.match(r"^([A-Z])?(\d+)", q)
        s["nq"].add((m.group(1) or "", m.group(2) or q))
        if r["Task"] == "short objective":
            s["so"] += 1
        s["n"] += 1
    return per


def _recompute_checks(rows: list[dict], checks: list[dict], sums: dict[str, float]) -> None:
    wb = load_workbook(TRACKING_XLSX)
    ws = wb["Paper marks check"]
    for i, row in enumerate(checks, start=2):
        pid = row["Paper ID"]
        total = sums.get(pid, 0.0)
        official = row["Official total"]
        ws.cell(row=i, column=3).value = round(total, 1)
        if isinstance(official, int):
            status = "match" if abs(total - official) < 0.01 else "mismatch"
            note = f"official {official} vs logged {total}" if status == "mismatch" \
                else f"logged {total} == official {official}"
        else:
            status, note = "official total unsure", f"computed sum = {total}"
        ws.cell(row=i, column=4).value = status
        ws.cell(row=i, column=5).value = note
    wb.save(TRACKING_XLSX)
    print("Paper marks check sheet recomputed from Questions rows.")


def main() -> None:
    rows = _sheet("Questions")
    papers = {r["Paper ID"]: r for r in _sheet("Papers")}
    checks = _sheet("Paper marks check")

    sums = _sums(rows)
    _recompute_checks(rows, checks, sums)
    struct = _structure(rows)

    order = sorted(papers, key=lambda p: (papers[p]["Year"],
                                          int(p[6:8]), p))
    print(f"\n{'paper':22} {'year':>4} {'sum':>6} {'era':12} {'parts':>5} {'nQ':>4} "
          f"{'shortObj%':>9}")
    for pid in order:
        p = papers[pid]
        s = struct[pid]
        so_share = 100 * s["so"] / s["n"] if s["n"] else 0
        print(f"{pid:22} {p['Year']:>4} {sums.get(pid, 0):6.1f} "
              f"{p['Era'].split(' ')[0]:12} {s['parts']:>5} {len(s['nq']):>4} "
              f"{so_share:8.0f}%")

    print("\nNear-clean papers (sum 94-106, labelled separately):")
    for pid in order:
        if 94 <= sums.get(pid, 0) <= 106:
            print(f"  {pid}: sum = {sums[pid]:.0f}")

    print("\nStructural profile per era (provisional boundaries):")
    for era in ("classic", "transitional", "modern"):
        ids = [pid for pid in order if papers[pid]["Era"].split(" ")[0] == era]
        if not ids:
            continue
        parts = {struct[pid]["parts"] for pid in ids}
        nqs = [len(struct[pid]["nq"]) for pid in ids]
        sos = [100 * struct[pid]["so"] / struct[pid]["n"] for pid in ids]
        print(f"  {era:12} n={len(ids)}  parts={sorted(parts)}  "
              f"questions={min(nqs)}-{max(nqs)} (mean {sum(nqs)/len(nqs):.0f})  "
              f"shortObj% mean {sum(sos)/len(sos):.0f}")


if __name__ == "__main__":
    main()
