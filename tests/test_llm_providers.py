"""Provider routing and public-build model selection."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from src import config
from src.llm import _provider


def test_provider_routing():
    assert _provider("deepseek-flash") == "deepseek"
    assert _provider("gemini-3.5-flash") == "gemini"
    assert _provider("gemini-3.1-flash-lite") == "gemini"
    assert _provider("qwen3.8-max") == "qwen"


def test_llm_key_ready_follows_active_model(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "g")
    monkeypatch.setattr(config, "DEEPSEEK_API_KEY", "")
    monkeypatch.setattr(config, "QWEN_API_KEY", "")
    monkeypatch.setattr(config, "MOCKGEN_MODEL", "gemini-3.5-flash")
    assert config.llm_key_ready() is True
    monkeypatch.setattr(config, "MOCKGEN_MODEL", "deepseek-flash")
    assert config.llm_key_ready() is False
    monkeypatch.setattr(config, "DEEPSEEK_API_KEY", "d")
    assert config.llm_key_ready() is True


def test_placeholder_key_is_not_ready(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY",
                        "REPLACE_WITH_GEMINI_API_KEY")
    monkeypatch.setattr(config, "MOCKGEN_MODEL", "gemini-3.5-flash")
    assert config.llm_key_ready() is False
    assert config._looks_like_placeholder(
        "REPLACE_WITH_GEMINI_API_KEY") is True
    assert config._looks_like_placeholder("AQ.real-key") is False


def test_public_build_fails_closed_on_placeholder():
    env = dict(os.environ)
    env.update({
        "PUBLIC_BUILD": "1",
        "GEMINI_API_KEY": "REPLACE_WITH_GEMINI_API_KEY",
        "MOCKGEN_MODEL": "",
        "MOCKGEN_GEMINI_MODEL": "gemini-3.5-flash",
    })
    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, "-c",
         "from src import config; "
         "print(config.MOCKGEN_MODEL, config.llm_key_ready())"],
        cwd=root, env=env, capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "gemini-3.5-flash False"


def test_public_build_defaults_to_gemini():
    env = dict(os.environ)
    env.update({
        "PUBLIC_BUILD": "1",
        "GEMINI_API_KEY": "test-gemini",
        "MOCKGEN_MODEL": "",
        "MOCKGEN_GEMINI_MODEL": "gemini-3.5-flash",
    })
    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, "-c",
         "from src import config; print(config.MOCKGEN_MODEL)"],
        cwd=root, env=env, capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "gemini-3.5-flash"
