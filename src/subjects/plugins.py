"""Load subject plugins and presentation metadata from the registry.

A plugin entry is a dotted ``module:attribute`` path stored in the subject's
``plugins`` block.  This keeps subject-specific code outside the shared app:
for example ``src.subjects.mat133.plugin:build_seed``.
"""
from __future__ import annotations

import importlib
from typing import Any, Callable

from src.subjects.registry import Subject, SubjectError


def resolve(path: str) -> Callable[..., Any]:
    if not path or ":" not in path:
        raise SubjectError(f"invalid plugin path: {path!r}")
    module_name, _, attr = path.partition(":")
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        raise SubjectError(
            f"cannot import plugin module {module_name}: {exc}") from exc
    try:
        value = getattr(module, attr)
    except AttributeError:
        raise SubjectError(
            f"plugin module {module_name} has no attribute {attr}") from None
    if not callable(value):
        raise SubjectError(f"plugin is not callable: {path}")
    return value


def plugin_for(subject: Subject, name: str) -> Callable[..., Any] | None:
    path = subject.plugin_path(name)
    return resolve(path) if path else None


def require_plugin(subject: Subject, name: str) -> Callable[..., Any]:
    plugin = plugin_for(subject, name)
    if plugin is None:
        raise SubjectError(
            f"subject {subject.code} has no {name!r} plugin in subject.json")
    return plugin


def humanise(identifier: str) -> str:
    text = (str(identifier).replace(".", " ").replace("_", " ")
            .replace("-", " "))
    return text[:1].upper() + text[1:] if text else identifier


def generator_labels(subject: Subject) -> list[str]:
    inline = dict(subject.capabilities.get("generator_labels") or {})
    plugin = plugin_for(subject, "generator_labels")
    if plugin is not None:
        inline.update(dict(plugin() or {}))
    return [str(inline.get(g) or humanise(g))
            for g in subject.enabled_computed_generators]


def topic_labels(subject: Subject) -> dict[str, str]:
    labels = dict(subject.topic_labels or {})
    plugin = plugin_for(subject, "topic_labels")
    if plugin is not None:
        labels.update(dict(plugin() or {}))
    return labels
