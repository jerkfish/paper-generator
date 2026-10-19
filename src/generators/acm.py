"""Access control matrix / ACL / capability-list construction (computed type #2).

Design rule (owner-approved): the LLM supplies ONLY a scenario (user names,
object names, rights). The matrix, ACLs, capability lists and the diagram
are all BUILT BY CODE - the LLM never produces the answers.

Consistency is verifiable: the matrix, the ACLs and the capability lists are
three views of the same relation, so each must rebuild the other two without
loss.
"""
from __future__ import annotations

from collections import defaultdict

from pydantic import BaseModel

RIGHTS = ("read", "write", "execute")


class AccessScenario(BaseModel):
    users: list[str]
    objects: list[str]
    grants: list[dict]  # {"user": ..., "object": ..., "rights": [...]}
    marks: int = 2


Matrix = dict[tuple[str, str], frozenset[str]]


def build_matrix(s: AccessScenario) -> Matrix:
    m: Matrix = {}
    for g in s.grants:
        key = (str(g["user"]), str(g["object"]))
        rights = frozenset(r.lower() for r in g.get("rights", []))
        m[key] = m.get(key, frozenset()) | rights
    return m


def derive_acls(matrix: Matrix, objects: list[str]) -> dict[str, dict[str, list[str]]]:
    """Per object: which users hold which rights."""
    acls: dict[str, dict[str, list[str]]] = defaultdict(dict)
    for (user, obj), rights in matrix.items():
        acls[obj][user] = sorted(rights)
    return dict(acls)


def derive_capabilities(matrix: Matrix, users: list[str]) -> dict[str, dict[str, list[str]]]:
    """Per user: which objects they may access with which rights."""
    caps: dict[str, dict[str, list[str]]] = defaultdict(dict)
    for (user, obj), rights in matrix.items():
        caps[user][obj] = sorted(rights)
    return dict(caps)


def matrix_from_acls(acls: dict[str, dict[str, list[str]]]) -> Matrix:
    m: Matrix = {}
    for obj, per_user in acls.items():
        for user, rights in per_user.items():
            m[(user, obj)] = frozenset(rights)
    return m


def matrix_from_capabilities(caps: dict[str, dict[str, list[str]]]) -> Matrix:
    m: Matrix = {}
    for user, per_obj in caps.items():
        for obj, rights in per_obj.items():
            m[(user, obj)] = frozenset(rights)
    return m


def check_consistency(s: AccessScenario) -> tuple[bool, str]:
    """ACLs and capability lists must rebuild the matrix without loss."""
    matrix = build_matrix(s)
    acls = derive_acls(matrix, s.objects)
    caps = derive_capabilities(matrix, s.users)
    if matrix_from_acls(acls) != matrix:
        return False, "ACL view lost or changed grants"
    if matrix_from_capabilities(caps) != matrix:
        return False, "capability view lost or changed grants"
    for (user, obj), rights in matrix.items():
        if user not in s.users or obj not in s.objects:
            return False, f"grant references unknown subject/object: {user}/{obj}"
        bad = set(rights) - set(RIGHTS)
        if bad:
            return False, f"unknown rights {sorted(bad)}"
    return True, ""


def empty_rows_cols(s: AccessScenario) -> list[str]:
    matrix = build_matrix(s)
    problems = []
    for user in s.users:
        if not any(o for (u, o) in matrix if u == user):
            problems.append(f"user {user} has no grants")
    for obj in s.objects:
        if not any(u for (u, o) in matrix if o == obj):
            problems.append(f"object {obj} is never accessed")
    return problems


def scenario_signature(s: AccessScenario) -> str:
    parts = [f"U{'|'.join(sorted(s.users))}", f"O{'|'.join(sorted(s.objects))}"]
    for g in sorted(s.grants, key=lambda g: (g["user"], g["object"])):
        parts.append(f"{g['user']}>{g['object']}:{','.join(sorted(g['rights']))}")
    return ";".join(parts)


def matrix_table(matrix: Matrix, users: list[str], objects: list[str]) -> str:
    head = "| Subject \\ Object | " + " | ".join(objects) + " |"
    sep = "|---|" + "---|" * len(objects)
    rows = [head, sep]
    for user in users:
        cells = []
        for obj in objects:
            r = matrix.get((user, obj), frozenset())
            cells.append("".join(sorted(r)) or "-")
        rows.append(f"| {user} | " + " | ".join(cells) + " |")
    return "\n".join(rows)


def acl_table(acls: dict[str, dict[str, list[str]]]) -> str:
    lines = ["**ACLs (per object):**"]
    for obj, per_user in acls.items():
        entry = "; ".join(f"{u}: {''.join(r)}" for u, r in sorted(per_user.items()))
        lines.append(f"- {obj} -> {entry}")
    return "\n".join(lines)


def capability_table(caps: dict[str, dict[str, list[str]]]) -> str:
    lines = ["**Capability lists (per subject):**"]
    for user, per_obj in caps.items():
        entry = "; ".join(f"{o}: {''.join(r)}" for o, r in sorted(per_obj.items()))
        lines.append(f"- {user} -> {entry}")
    return "\n".join(lines)


def to_dot(s: AccessScenario, matrix: Matrix) -> str:
    lines = ["digraph ACM {", "  rankdir=LR;", '  node [shape=box];']
    for user in s.users:
        lines.append(f'  "{user}";')
    for obj in s.objects:
        lines.append(f'  "{obj}" [shape=ellipse];')
    for (user, obj), rights in sorted(matrix.items()):
        label = ", ".join(sorted(rights))
        lines.append(f'  "{user}" -> "{obj}" [label="{label}"];')
    lines.append("}")
    return "\n".join(lines)
