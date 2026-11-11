"""Subject lifecycle state: v1 stages 0-10 and v2 stages V0-V8.

The playbook is the authority for what each stage means.  This module is the
machine-readable companion used by ``scripts/new_subject.py`` and
``scripts/lifecycle_status.py``.  A stage is only "done" when its evidence
exists and its human checkpoint (where required) was recorded.

Schema v2 replaces the per-stage human checkpoints with the three playbook
gates: A (bank approved), B (first seeds approved) and C (publish).  A v1
state remains readable; nothing is migrated automatically.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
DONE_STATUSES = {"done", "skipped", "not_applicable"}
VALID_STATUSES = {"pending", "in_progress", "blocked", *DONE_STATUSES}

STAGES: tuple[dict[str, Any], ...] = (
    {
        "key": "0_intake",
        "title": "Intake and permissions",
        "human": True,
        "purpose": "Confirm subject identity, type, inputs and permission basis.",
    },
    {
        "key": "1_preprocess",
        "title": "Paper preprocessing",
        "human": True,
        "purpose": "Rename by cover, deduplicate, OCR and register papers.",
    },
    {
        "key": "2_scheme_slides",
        "title": "Scheme and slides",
        "human": True,
        "purpose": "Inventory the official scheme and lecture slides.",
    },
    {
        "key": "3_template",
        "title": "Template and cover",
        "human": True,
        "purpose": "Approve the paper/scheme template and cover layout.",
    },
    {
        "key": "4_taxonomy_question_log",
        "title": "Taxonomy and question log",
        "human": True,
        "purpose": "Derive topics, marks and question metadata from papers.",
    },
    {
        "key": "5_fingerprint_planner",
        "title": "Fingerprint and planner",
        "human": True,
        "purpose": "Approve the paper fingerprint and the slot planner.",
    },
    {
        "key": "6_generators",
        "title": "Generators",
        "human": True,
        "purpose": "Implement and validate computed/theory generators.",
    },
    {
        "key": "7_builders_qa",
        "title": "Builders and QA",
        "human": True,
        "purpose": "Build paper/scheme DOCX/PDF and pass structural QA.",
    },
    {
        "key": "8_library_prebuild",
        "title": "Library prebuild",
        "human": True,
        "purpose": "Build the accepted 20-seed Library without live LLM calls.",
    },
    {
        "key": "9_publish",
        "title": "Publish",
        "human": True,
        "purpose": "Build the public bundle, upload and deploy the Worker.",
    },
    {
        "key": "10_close_out",
        "title": "Close-out",
        "human": True,
        "purpose": "Record evidence, costs, unsure items and sign-off.",
    },
)

STAGE_KEYS = tuple(stage["key"] for stage in STAGES)
STAGE_BY_KEY = {stage["key"]: stage for stage in STAGES}

SCHEMA_VERSION_V2 = 2
PLAYBOOK_VERSION_V2 = "2.0"
GATE_KEYS = ("A", "B", "C")
GATE_TITLES = {
    "A": "Bank approved",
    "B": "First seeds approved",
    "C": "Publish approved",
}

STAGES_V2: tuple[dict[str, Any], ...] = (
    {
        "key": "V0_intake",
        "title": "Intake and permissions",
        "gate": None,
        "purpose": "Confirm identity, Type D recycle strategy and permissions.",
    },
    {
        "key": "V1_extract",
        "title": "Asset-first extraction",
        "gate": None,
        "purpose": "MinerU dossier per paper: full ZIP, layout, page crops.",
    },
    {
        "key": "V2_bank",
        "title": "Question bank",
        "gate": "A",
        "purpose": "Reviews, corrections, duplicate clusters and quality scores.",
    },
    {
        "key": "V3_format",
        "title": "Format profile",
        "gate": None,
        "purpose": "Current paper/scheme format, marks rules and numbering.",
    },
    {
        "key": "V4_answers",
        "title": "Answer sources",
        "gate": None,
        "purpose": "Official/solver/model/human answer provenance and schemes.",
    },
    {
        "key": "V5_seeds_1_3",
        "title": "Seed pilots 1-3",
        "gate": "B",
        "purpose": "Assemble and QA the first three recycled seeds.",
    },
    {
        "key": "V6_library",
        "title": "Library prebuild",
        "gate": None,
        "purpose": "Assemble min(20, feasible) seeds within the reuse cap.",
    },
    {
        "key": "V7_publish",
        "title": "Publish",
        "gate": "C",
        "purpose": "Build the public bundle, upload and deploy after Gate C.",
    },
    {
        "key": "V8_close_out",
        "title": "Close-out",
        "gate": None,
        "purpose": "Record evidence, bank counts, costs and unsure items.",
    },
)

STAGE_KEYS_V2 = tuple(stage["key"] for stage in STAGES_V2)
STAGE_BY_KEY_V2 = {stage["key"]: stage for stage in STAGES_V2}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today() -> str:
    return date.today().isoformat()


def blank_stage(spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "pending",
        "evidence": [],
        "llm_cost_usd": 0.0,
        "blockers": [],
        "human_approval": {
            "required": bool(spec.get("human")),
            "approved": False,
            "by": "",
            "on": "",
            "note": "",
        },
        "notes": "",
    }


def new_state(code: str, subject_type: str,
              template_path: str = "") -> dict[str, Any]:
    code = code.upper()
    stages = {key: blank_stage(STAGE_BY_KEY[key]) for key in STAGE_KEYS}
    # A new scaffold has not started stage 0; make the pending human decisions
    # explicit instead of pretending intake was completed.
    unsure = [
        {
            "stage": "0_intake",
            "item": f"Confirm {code} title, subject type ({subject_type}) and "
                    "curriculum order with the subject owner.",
            "blocking": True,
            "opened": _today(),
        },
        {
            "stage": "0_intake",
            "item": f"Record papers permission for {code}.",
            "blocking": True,
            "opened": _today(),
        },
        {
            "stage": "0_intake",
            "item": f"Record scheme permission for {code}.",
            "blocking": True,
            "opened": _today(),
        },
        {
            "stage": "0_intake",
            "item": f"Record lecture-slides permission for {code}.",
            "blocking": True,
            "opened": _today(),
        },
        {
            "stage": "9_publish",
            "item": f"Record publication permission for {code} before any "
                    "upload or deploy.",
            "blocking": True,
            "opened": _today(),
        },
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "subject": code,
        "type": subject_type,
        "template_path": template_path,
        "created": _now(),
        "updated": _now(),
        "stages": stages,
        "unsure": unsure,
        "llm_cost": {
            "currency": "USD",
            "total_usd": 0.0,
            "by_stage": {key: 0.0 for key in STAGE_KEYS},
        },
    }


def blank_stage_v2(spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "pending",
        "evidence": [],
        "llm_cost_usd": 0.0,
        "blockers": [],
        "human_approval": {
            "required": False,
            "approved": False,
            "by": "",
            "on": "",
            "note": "",
        },
        "notes": "",
    }


def new_state_v2(code: str, subject_type: str = "D",
                 title: str = "") -> dict[str, Any]:
    """Return a fresh schema-v2 lifecycle at V0 with all gates open."""
    code = code.upper()
    stages = {key: blank_stage_v2(STAGE_BY_KEY_V2[key])
              for key in STAGE_KEYS_V2}
    stages["V0_intake"]["status"] = "in_progress"
    return {
        "schema_version": SCHEMA_VERSION_V2,
        "playbook_version": PLAYBOOK_VERSION_V2,
        "subject": code,
        "title": title,
        "type": subject_type,
        "strategy": "recycle" if subject_type == "D" else "generate",
        "lifecycle_status": "in_progress",
        "created": _now(),
        "updated": _now(),
        "stages": stages,
        "gates": {
            key: {"status": "pending", "by": "", "on": "", "evidence": []}
            for key in GATE_KEYS
        },
        "bank": {
            "questions": 0,
            "approved": 0,
            "needs_fix": 0,
            "rejected": 0,
            "assets": 0,
            "duplicate_clusters": 0,
        },
        "answers": {
            "official": 0,
            "solver_verified": 0,
            "model_unofficial": 0,
            "human_checked": 0,
        },
        "unsure": [
            {
                "stage": "V0_intake",
                "item": f"Confirm {code} title, Type D recycle strategy and "
                        "curriculum order with the subject owner.",
                "blocking": True,
                "opened": _today(),
            },
            {
                "stage": "V0_intake",
                "item": f"Record papers, scheme and cloud-processing "
                        f"permissions for {code} before MinerU extraction.",
                "blocking": True,
                "opened": _today(),
            },
        ],
        "parser_provenance": [],
        "llm_cost": {
            "currency": "USD",
            "total_usd": 0.0,
            "by_stage": {key: 0.0 for key in STAGE_KEYS_V2},
        },
    }


def is_v2(state: dict[str, Any] | None) -> bool:
    """True for the V0-V8 schema.

    Some v1 subjects carry ``schema_version: 2`` for their own reasons (CSC429
    records a P0 reset that way), so the stage keys decide, not the number.
    """
    if not isinstance(state, dict):
        return False
    return "V0_intake" in (state.get("stages") or {})


def state_path(root: Path, code: str) -> Path:
    return Path(root) / "subjects" / code.upper() / "lifecycle_state.json"


def load_state(root: Path, code: str) -> dict[str, Any] | None:
    path = state_path(root, code)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def save_state(root: Path, code: str, state: dict[str, Any]) -> Path:
    path = state_path(root, code)
    path.parent.mkdir(parents=True, exist_ok=True)
    state["updated"] = _now()
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return path


def stage_keys(state: dict[str, Any]) -> tuple[str, ...]:
    return STAGE_KEYS_V2 if is_v2(state) else STAGE_KEYS


def stage_by_key(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return STAGE_BY_KEY_V2 if is_v2(state) else STAGE_BY_KEY


def gate_for_stage(state: dict[str, Any], stage: str) -> str | None:
    if not is_v2(state):
        return None
    return (STAGE_BY_KEY_V2.get(stage) or {}).get("gate")


def gate_status(state: dict[str, Any], gate: str) -> dict[str, Any]:
    return ((state.get("gates") or {}).get(gate) or
            {"status": "pending", "by": "", "on": "", "evidence": []})


def gate_approved(state: dict[str, Any], gate: str) -> bool:
    return str(gate_status(state, gate).get("status", "")).lower() == "approved"


def next_stage(state: dict[str, Any]) -> str | None:
    stages = state.get("stages") or {}
    for key in stage_keys(state):
        status = (stages.get(key) or {}).get("status", "pending")
        if status not in DONE_STATUSES:
            return key
    return None


def _evidence_missing(evidence: list[str]) -> list[str]:
    missing = []
    for value in evidence or []:
        text = str(value)
        if not text or text.startswith(("http://", "https://")):
            continue
        if not Path(text).exists():
            missing.append(text)
    return missing


def stage_blockers(state: dict[str, Any], stage: str,
                   root: Path | None = None) -> list[str]:
    spec = stage_by_key(state).get(stage)
    if spec is None:
        return [f"unknown stage {stage}"]
    entry = (state.get("stages") or {}).get(stage) or {}
    status = str(entry.get("status", "pending"))
    blockers = [f"stage is {status}"] if status == "blocked" else []
    blockers.extend(str(item) for item in entry.get("blockers") or []
                    if item)
    for item in state.get("unsure") or []:
        if item.get("stage") == stage and item.get("blocking"):
            blockers.append(f"unsure: {item.get('item')}")
    if status in DONE_STATUSES:
        missing = _evidence_missing(entry.get("evidence") or [])
        if missing:
            blockers.append("missing evidence: " + ", ".join(missing))
        if is_v2(state):
            gate = gate_for_stage(state, stage)
            if gate and not gate_approved(state, gate):
                blockers.append(
                    f"Gate {gate} ({GATE_TITLES[gate]}) is not approved")
        else:
            approval = entry.get("human_approval") or {}
            if spec.get("human") and not approval.get("approved"):
                blockers.append(
                    f"[HUMAN] approval not recorded for {spec['title']}")
    return blockers


def status_report(root: Path, code: str) -> dict[str, Any]:
    code = code.upper()
    state = load_state(root, code)
    if state is None:
        return {
            "subject": code,
            "initialized": False,
            "schema_version": 0,
            "next_stage": STAGE_KEYS[0],
            "stage_title": STAGE_BY_KEY[STAGE_KEYS[0]]["title"],
            "status": "missing",
            "blockers": [
                "lifecycle_state.json is missing; run the stage-0 intake "
                "scaffold or create it from the playbook template",
            ],
            "human_checkpoint": True,
        }
    v2 = is_v2(state)
    keys = stage_keys(state)
    specs = stage_by_key(state)
    stage = next_stage(state)
    if stage is None:
        return {
            "subject": code,
            "initialized": True,
            "schema_version": state.get("schema_version", 1),
            "lifecycle_schema": 2 if v2 else 1,
            "next_stage": None,
            "stage_title": "Complete",
            "status": "done",
            "blockers": [],
            "human_checkpoint": False,
            "gates": {key: gate_status(state, key) for key in GATE_KEYS}
            if v2 else {},
            "updated": state.get("updated", ""),
        }
    entry = (state.get("stages") or {}).get(stage) or {}
    blockers = stage_blockers(state, stage, root)
    # Previous incomplete stages are always the first blocker.
    for key in keys:
        if key == stage:
            break
        prior = (state.get("stages") or {}).get(key) or {}
        if prior.get("status") not in DONE_STATUSES:
            blockers.insert(0, f"previous stage incomplete: {key}")
            break
    gate = gate_for_stage(state, stage)
    if gate and not gate_approved(state, gate):
        blockers.append(f"Gate {gate} ({GATE_TITLES[gate]}) is not approved")
    return {
        "subject": code,
        "initialized": True,
        "schema_version": state.get("schema_version", 1),
        "lifecycle_schema": 2 if v2 else 1,
        "next_stage": stage,
        "stage_title": specs[stage]["title"],
        "status": entry.get("status", "pending"),
        "blockers": blockers,
        "human_checkpoint": (bool(specs[stage].get("human"))
                             if not v2 else False),
        "next_gate": gate,
        "gates": {key: gate_status(state, key) for key in GATE_KEYS}
        if v2 else {},
        "bank": dict(state.get("bank") or {}) if v2 else {},
        "updated": state.get("updated", ""),
        "unsure_count": sum(1 for item in state.get("unsure") or []
                            if item.get("blocking")),
        "llm_cost_usd": float((state.get("llm_cost") or {})
                              .get("total_usd", 0.0)),
    }
