"""Subject registry discovered from ``subjects/<CODE>/subject.json``.

The registry is the only place the app learns which subjects exist.  A subject
with status ``available`` may generate and browse papers; ``coming_soon``
subjects are shown on the home page but have no data or generators.

No subject code is special-cased in application code.  Behaviour comes from
the subject's ``type`` (A/B/C), ``capabilities`` block and the optional
``plugins`` entry points.  Subject-specific code lives in
``src/subjects/<code>/`` and is loaded by dotted path from the registry.

Type summary (see ``docs/SUBJECT_PLAYBOOK.md``):
  A - lecture slides + LLM theory pipeline
  B - deterministic computed papers (no LLM)
  C - hybrid: deterministic generators plus LLM theory where appropriate
  D - asset-first assembly from approved real questions and source assets
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from src import config

VALID_STATUSES = {"available", "coming_soon"}
VALID_TYPES = {"A", "B", "C", "D"}

PUBLIC_CAPABILITY_KEYS = (
    "subject_type", "generation", "prebuild", "public_documents",
    "needs_llm", "uses_slides", "uses_past_papers", "deterministic",
    "practice_mode", "placeholders", "public_scheme_requires_quote_marker",
)


class SubjectError(ValueError):
    pass


class SubjectNotFound(SubjectError):
    pass


@dataclass(frozen=True)
class Subject:
    code: str
    title: str
    status: str
    header_text: str = ""
    template_path: str = ""
    fingerprint: dict = field(default_factory=dict)
    deck_map: dict = field(default_factory=dict)
    topic_deck_allowlist: dict = field(default_factory=dict)
    enabled_computed_generators: list[str] = field(default_factory=list)
    has_practice_mode: bool = True
    has_placeholders: bool = True
    order: int = 9999
    registry_path: Path | None = None
    subject_type: str = "C"
    capabilities: dict = field(default_factory=dict)
    permissions: dict = field(default_factory=dict)
    plugins: dict = field(default_factory=dict)
    topic_labels: dict = field(default_factory=dict)

    @property
    def available(self) -> bool:
        return self.status == "available"

    @property
    def route(self) -> str:
        return self.code.lower()

    @property
    def deterministic(self) -> bool:
        return self.capabilities.get("generation") == "deterministic"

    @property
    def needs_llm(self) -> bool:
        return bool(self.capabilities.get("needs_llm", not self.deterministic))

    @property
    def public_scheme_requires_quote_marker(self) -> bool:
        return bool(self.capabilities.get(
            "public_scheme_requires_quote_marker", not self.deterministic))

    def plugin_path(self, name: str) -> str:
        return str(self.plugins.get(name, "") or "")

    def public_dict(self) -> dict:
        """Fields safe to publish. Internal paths and deck maps stay private."""
        capabilities = {
            key: self.capabilities[key]
            for key in PUBLIC_CAPABILITY_KEYS
            if key in self.capabilities
        }
        return {
            "code": self.code,
            "title": self.title,
            "status": self.status,
            "type": self.subject_type,
            "header_text": self.header_text,
            "enabled_computed_generators": list(self.enabled_computed_generators),
            "has_practice_mode": self.has_practice_mode,
            "has_placeholders": self.has_placeholders,
            "order": self.order,
            "capabilities": capabilities,
        }


def subjects_dir(root: Path | None = None) -> Path:
    return Path(root or config.PROJECT_ROOT) / "subjects"


def _infer_type(data: dict, deck_map: dict,
                enabled_generators: list[str]) -> str:
    caps = data.get("capabilities") or {}
    declared = str(data.get("type") or caps.get("subject_type") or "").upper()
    if declared in VALID_TYPES:
        return declared
    # Data-driven inference for the existing registry files, which predate the
    # explicit type field.  No subject code is referenced here.
    if deck_map:
        return "A"
    if enabled_generators:
        return "B"
    return "C"


def _default_capabilities(subject_type: str) -> dict:
    deterministic = subject_type in {"B", "D"}
    uses_slides = subject_type in {"A", "C"}
    asset_first = subject_type == "D"
    return {
        "subject_type": subject_type,
        "generation": ("deterministic" if deterministic else
                       "llm_theory" if subject_type == "A" else "hybrid"),
        "prebuild": ("plugin" if deterministic else
                     "llm_seed_set" if subject_type == "A" else "plugin"),
        "public_documents": ("copy_cached" if deterministic else
                             "rebuild_scheme"),
        "needs_llm": not deterministic,
        "uses_slides": uses_slides,
        "uses_past_papers": True,
        "deterministic": deterministic,
        "practice_mode": not deterministic,
        "placeholders": not deterministic,
        "public_scheme_requires_quote_marker": not deterministic,
        "asset_first": asset_first,
    }


def _default_permissions() -> dict:
    blank = {
        "allowed": False,
        "basis": "unsure",
        "confirmed_by": "",
        "confirmed_on": "",
        "notes": "Not recorded",
    }
    return {
        "papers": dict(blank),
        "scheme": dict(blank),
        "slides": dict(blank),
        "publication": dict(blank),
    }


def _load_one(path: Path) -> Subject:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise SubjectError(f"cannot read subject registry {path}: {e}") from e
    if not isinstance(data, dict):
        raise SubjectError(f"subject registry must be a JSON object: {path}")
    code = str(data.get("code", "")).strip().upper()
    title = str(data.get("title", "")).strip()
    status = str(data.get("status", "")).strip().lower()
    if not code or not title:
        raise SubjectError(f"subject registry needs code and title: {path}")
    if status not in VALID_STATUSES:
        raise SubjectError(
            f"subject {code}: status must be one of {sorted(VALID_STATUSES)}")

    deck_map = dict(data.get("deck_map") or {})
    enabled = list(data.get("enabled_computed_generators") or [])
    subject_type = _infer_type(data, deck_map, enabled)
    raw_caps = dict(data.get("capabilities") or {})
    default_caps = _default_capabilities(subject_type)
    capabilities = {**default_caps, **raw_caps}
    capabilities["subject_type"] = subject_type
    # A subject type is a promise about the pipeline.  Keep the derived flags
    # consistent even if an old registry file only has the legacy booleans.
    deterministic = capabilities.get("generation") == "deterministic"
    if "needs_llm" not in raw_caps:
        capabilities["needs_llm"] = not deterministic
    if "deterministic" not in raw_caps:
        capabilities["deterministic"] = deterministic
    capabilities.setdefault(
        "public_scheme_requires_quote_marker", not deterministic)

    practice = bool(data.get(
        "has_practice_mode",
        capabilities.get("practice_mode", not deterministic)))
    placeholders = bool(data.get(
        "has_placeholders",
        capabilities.get("placeholders", not deterministic)))
    capabilities["practice_mode"] = practice
    capabilities["placeholders"] = placeholders

    permissions = _default_permissions()
    permissions.update(dict(data.get("permissions") or {}))

    return Subject(
        code=code,
        title=title,
        status=status,
        header_text=str(data.get("header_text", "")),
        template_path=str(data.get("template_path", "")),
        fingerprint=dict(data.get("fingerprint") or {}),
        deck_map=deck_map,
        topic_deck_allowlist=dict(data.get("topic_deck_allowlist") or {}),
        enabled_computed_generators=enabled,
        has_practice_mode=practice,
        has_placeholders=placeholders,
        order=int(data.get("order", 9999)),
        registry_path=path,
        subject_type=subject_type,
        capabilities=capabilities,
        permissions=permissions,
        plugins=dict(data.get("plugins") or {}),
        topic_labels=dict(data.get("topic_labels") or {}),
    )


def load_subjects(root: Path | None = None) -> dict[str, Subject]:
    """Scan the registry folder. Available subjects sort before stubs."""
    base = subjects_dir(root)
    if not base.exists():
        raise SubjectError(f"subject registry folder not found: {base}")
    found: dict[str, Subject] = {}
    for path in sorted(base.glob("*/subject.json")):
        subject = _load_one(path)
        if subject.code in found:
            raise SubjectError(
                f"duplicate subject code {subject.code}: "
                f"{found[subject.code].registry_path} and {path}")
        found[subject.code] = subject
    if not found:
        raise SubjectError(f"no subjects found under {base}")
    return dict(sorted(
        found.items(),
        key=lambda item: (item[1].status != "available",
                          item[1].order, item[0])))


def get_subject(code: str, root: Path | None = None) -> Subject:
    key = str(code).strip().upper()
    subjects = load_subjects(root)
    try:
        return subjects[key]
    except KeyError:
        raise SubjectNotFound(f"unknown subject: {code}") from None


def available_subjects(root: Path | None = None) -> list[Subject]:
    return [s for s in load_subjects(root).values() if s.available]


def default_subject_code(root: Path | None = None) -> str:
    """First available subject, else the first registry entry.

    This is deliberately data-driven; no subject code is embedded in the app.
    """
    subjects = list(load_subjects(root).values())
    for subject in subjects:
        if subject.available:
            return subject.code
    return subjects[0].code


def default_generation_subject_code(root: Path | None = None) -> str:
    """First available subject that offers a generation pipeline."""
    subjects = list(load_subjects(root).values())
    for subject in subjects:
        if subject.available and subject.capabilities.get("generation"):
            return subject.code
    return default_subject_code(root)
