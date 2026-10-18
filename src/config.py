"""Central configuration: paths, model settings and thresholds.

API keys are NEVER stored here - they are read from environment variables
at runtime (see ANTHROPIC_API_KEY below).
"""
from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# --- paths ---------------------------------------------------------------
ORIGINAL_PAPERS_DIR = PROJECT_ROOT / "CSC662"  # user's originals - never modified
DATA_DIR = PROJECT_ROOT / "data"
PAPERS_DIR = DATA_DIR / "papers"               # read-only working copies
NOTES_DIR = DATA_DIR / "notes"                 # lecture material
TRACKING_DIR = DATA_DIR / "tracking"
TRACKING_XLSX = TRACKING_DIR / "mock_paper_planner.xlsx"
OCR_CACHE_DIR = TRACKING_DIR / "ocr_cache"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# --- LLM -----------------------------------------------------------------
# Provider: Qwen via its OpenAI-compatible endpoint (per project owner).
# Keys are NEVER hardcoded - they live in .env (gitignored) or the environment.
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except Exception:  # dotenv optional at runtime
    pass

QWEN_API_KEY = os.environ.get("QWEN_API_KEY", "")
# key verified against the international compatible-mode endpoint 2026-10-18
QWEN_BASE_URL = os.environ.get(
    "QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
QWEN_MODEL = os.environ.get("MOCKGEN_QWEN_MODEL", "qwen3.7-plus")
LLM_MAX_RETRIES = 3

# --- thresholds ----------------------------------------------------------
OCR_MIN_TEXT_CHARS = 50  # below this, a cover is treated as scanned (no text layer)
