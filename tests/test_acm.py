"""ACM/ACL/capability construction tests: consistency, derivation, rendering."""
from __future__ import annotations

from src.generators.acm import (AccessScenario, build_matrix, check_consistency,
                                derive_acls, derive_capabilities, empty_rows_cols,
                                matrix_from_acls, matrix_from_capabilities,
                                scenario_signature, to_dot)


def _scenario() -> AccessScenario:
    return AccessScenario(
        users=["ali", "yati", "root"],
        objects=["X1", "X2"],
        grants=[
            {"user": "ali", "object": "X1", "rights": ["read", "write"]},
            {"user": "yati", "object": "X1", "rights": ["read"]},
            {"user": "root", "object": "X1", "rights": ["read", "write", "execute"]},
            {"user": "root", "object": "X2", "rights": ["execute"]},
        ],
        marks=6,
    )


def test_consistency_holds():
    assert check_consistency(_scenario()) == (True, "")


def test_matrix_acl_capability_roundtrip():
    s = _scenario()
    m = build_matrix(s)
    assert matrix_from_acls(derive_acls(m, s.objects)) == m
    assert matrix_from_capabilities(derive_capabilities(m, s.users)) == m


def test_acl_view():
    s = _scenario()
    acls = derive_acls(build_matrix(s), s.objects)
    assert acls["X1"]["root"] == ["execute", "read", "write"]
    assert acls["X1"]["yati"] == ["read"]


def test_capability_view():
    s = _scenario()
    caps = derive_capabilities(build_matrix(s), s.users)
    assert caps["root"]["X2"] == ["execute"]


def test_empty_rows_cols_detected():
    bad = AccessScenario(
        users=["ali", "idle"], objects=["X1", "orphan"],
        grants=[{"user": "ali", "object": "X1", "rights": ["read"]}], marks=2)
    problems = empty_rows_cols(bad)
    assert any("idle" in p for p in problems)
    assert any("orphan" in p for p in problems)


def test_unknown_right_rejected():
    bad = _scenario().model_copy(deep=True)
    bad.grants[0]["rights"] = ["fly"]
    ok, msg = check_consistency(bad)
    assert not ok and "fly" in msg


def test_signature_unique_per_scenario():
    a = _scenario()
    b = a.model_copy(deep=True)
    assert scenario_signature(a) == scenario_signature(b)
    b.grants[0]["rights"] = ["read"]
    assert scenario_signature(a) != scenario_signature(b)


def test_dot_output_shape():
    s = _scenario()
    dot = to_dot(s, build_matrix(s))
    assert dot.startswith("digraph ACM")
    assert '"ali" -> "X1"' in dot
