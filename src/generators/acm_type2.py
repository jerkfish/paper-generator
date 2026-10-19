"""Computed question type #2: ACM/ACL/capability-list construction.

Design rule: the LLM supplies ONLY a scenario (user names, object names,
rights). Code builds the matrix, derives ACLs and capability lists and emits
the Graphviz diagram - the LLM never produces the answers.

Verifier: views rebuild each other without loss; no empty rows/columns; marks
fit the modern slot (2 or 6); the scenario is not a repeat. Max 3 retries.

Run:  uv run python -m src.generators.acm_type2
"""
from __future__ import annotations

import re

from pydantic import ValidationError

from src.config import OUTPUTS_DIR
from src.generators.acm import (AccessScenario, acl_table, build_matrix,
                                capability_table, check_consistency,
                                derive_acls, derive_capabilities, empty_rows_cols,
                                matrix_table, scenario_signature, to_dot)
from src.llm import chat_json

DRAFT_MODEL = "qwen3.7-flash"
ALLOWED_MARKS = (2, 6)
MAX_RETRIES = 3

SYSTEM = """You draft scenarios for access-control-matrix exercises in a
computer-security course. Output ONE JSON object:
{"users": ["name", ...], "objects": ["file", ...],
 "grants": [{"user": "name", "object": "file", "rights": ["read", "write"]}, ...],
 "marks": 6}
Rules: 3-4 users (Malay-style names like Ali, Yati, Umi, Farhan plus one
'Root' account); 3 objects named like X-1, REPORT, DATA; rights only from
read/write/execute. Every user must hold at least one grant and every object
must be granted to someone (Root typically holds all three rights on
everything). Vary the permission pattern. Marks: 6 (multi-part) or 2.
Return only the JSON object."""

STYLE = ("Real scenario style (tone only): 'Assume that there are only four "
         "accounts (ali, yati, umi root), four rights or permissions "
         "(read, write, execute).' 'A computer system with three (3) users: "
         "Farhan, Faizah, and Fazlan. Farhan owns the file X-1; Faizah and "
         "Fazlan can read it.'")


def render_scenario(s: AccessScenario) -> str:
    lines = [f"Assume a computer system with the accounts: "
             f"{', '.join(s.users)}.", ""]
    for g in s.grants:
        rights = ", ".join(sorted(r.lower() for r in g["rights"]))
        lines.append(f"{g['user']} can {rights} {g['object']}.")
    lines.append("")
    if s.marks == 6:
        lines.append("a) Write the access control matrix (ACM).")
        lines.append("b) Write a set of access control lists (ACL).")
        lines.append("c) Write a set of capability lists (CL).")
    else:
        lines.append("Write the access control matrix (ACM).")
    lines.append(f"({s.marks} marks)")
    return "\n".join(lines)


def verify(s: AccessScenario, past: set[str]) -> list[str]:
    problems = []
    if s.marks not in ALLOWED_MARKS:
        problems.append(f"marks {s.marks} not in {ALLOWED_MARKS}")
    if len(s.users) < 3 or len(s.objects) < 3:
        problems.append("need at least 3 users and 3 objects")
    ok, msg = check_consistency(s)
    if not ok:
        problems.append(f"inconsistent views: {msg}")
    problems.extend(empty_rows_cols(s))
    if scenario_signature(s) in past:
        problems.append("scenario already used")
    return problems


def render_answer(s: AccessScenario) -> str:
    matrix = build_matrix(s)
    return "\n\n".join([
        matrix_table(matrix, s.users, s.objects),
        acl_table(derive_acls(matrix, s.objects)),
        capability_table(derive_capabilities(matrix, s.users)),
        "**Diagram (Graphviz dot):**",
        "```dot\n" + to_dot(s, matrix) + "\n```",
    ])


def main() -> None:
    past: set[str] = set()
    accepted: list[AccessScenario] = []
    attempts = 0
    last_problems: list[str] = []
    while len(accepted) < 5 and attempts < 40:
        attempts += 1
        user = STYLE
        if last_problems:
            user += ("\nYour previous draft was rejected because: "
                     + "; ".join(last_problems)
                     + ". Use DIFFERENT account names, file names and a "
                       "different permission pattern.")
        try:
            data = chat_json(SYSTEM, user, model=DRAFT_MODEL)
            s = AccessScenario(**data)
        except (ValidationError, RuntimeError, KeyError) as e:
            print(f"draft rejected: {e}", flush=True)
            last_problems = [str(e)]
            continue
        problems = verify(s, past)
        if problems:
            last_problems = problems
            print(f"draft failed: {problems}", flush=True)
            continue
        last_problems = []
        accepted.append(s)
        past.add(scenario_signature(s))
        print(f"accepted {len(accepted)}: users={s.users} marks={s.marks} "
              f"[model {DRAFT_MODEL}]", flush=True)

    OUTPUTS_DIR.mkdir(exist_ok=True)
    md = ["# Computed sample questions - ACM / ACL / capability lists\n",
          f"Scenarios drafted by the LLM ({DRAFT_MODEL}) - names and rights only. "
          "Matrix, ACLs, capability lists and the diagram are built by code; "
          "consistency is machine-verified (each view rebuilds the others).\n",
          "Note: the Graphviz `dot` binary is not installed on this machine, so "
          "diagrams are emitted as `.dot` sources (rendered by any Graphviz "
          "installer).\n"]
    for i, s in enumerate(accepted, 1):
        md.append(f"## Question {i} ({s.marks} marks)\n")
        md.append("```\n" + render_scenario(s) + "\n```")
        md.append(render_answer(s))
        md.append("")
    out = OUTPUTS_DIR / "acm_samples.md"
    out.write_text("\n".join(md), encoding="utf-8")
    print(f"wrote {len(accepted)} questions -> {out}")


if __name__ == "__main__":
    main()
