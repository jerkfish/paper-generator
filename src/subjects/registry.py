"""Subject registry discovered from ``subjects/<CODE>/subject.json``.

The registry is the only place the app learns which subjects exist.  A subject
with status ``available`` may generate and browse papers; ``coming_soon``
subjects are shown on the home page but have no data or generators.

Computed generators are subject plugins: the CSC662 generator types listed here
are implemented in ``src.generators``.  Another subject needs its own plugin.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from src import config

VALID_STATUSES = {"available", "coming_soon"}


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
    registry_path: Path | None = None

    @property
    def available(self) -> bool:
        return self.status == "available"

    @property
    def route(self) -> str:
        return self.code.lower()

    def public_dict(self) -> dict:
        """Fields safe to publish. Internal paths and deck maps stay private."""
        return {
            "code": self.code,
            "title": self.title,
            "status": self.status,
            "header_text": self.header_text,
            "enabled_computed_generators": list(self.enabled_computed_generators),
        }


def subjects_dir(root: Path | None = None) -> Path:
    return Path(root or config.PROJECT_ROOT) / "subjects"


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
    return Subject(
        code=code,
        title=title,
        status=status,
        header_text=str(data.get("header_text", "")),
        template_path=str(data.get("template_path", "")),
        fingerprint=dict(data.get("fingerprint") or {}),
        deck_map=dict(data.get("deck_map") or {}),
        topic_deck_allowlist=dict(data.get("topic_deck_allowlist") or {}),
        enabled_computed_generators=list(
            data.get("enabled_computed_generators") or []),
        registry_path=path,
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
        key=lambda item: (item[1].status != "available", item[0])))


def get_subject(code: str, root: Path | None = None) -> Subject:
    key = str(code).strip().upper()
    subjects = load_subjects(root)
    try:
        return subjects[key]
    except KeyError:
        raise SubjectNotFound(f"unknown subject: {code}") from None


def available_subjects(root: Path | None = None) -> list[Subject]:
    return [s for s in load_subjects(root).values() if s.available]
