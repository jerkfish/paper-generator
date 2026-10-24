"""Central configuration: paths, model settings and thresholds.

API keys are NEVER stored here - they are read from environment variables
at runtime (see ANTHROPIC_API_KEY below).
"""
from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Load local environment before paths/keys are read.  .env is gitignored.
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except Exception:  # dotenv optional at runtime
    pass

# --- paths ---------------------------------------------------------------
ORIGINAL_PAPERS_DIR = PROJECT_ROOT / "CSC662"  # user's originals - never modified
DATA_DIR = PROJECT_ROOT / "data"
PAPERS_ROOT = DATA_DIR / "papers"              # read-only working copies
NOTES_DIR = DATA_DIR / "notes"                 # lecture material
TRACKING_DIR = DATA_DIR / "tracking"
TRACKING_XLSX = TRACKING_DIR / "mock_paper_planner.xlsx"
OCR_CACHE_DIR = TRACKING_DIR / "ocr_cache"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# Per-subject input folders.  Reference templates and lecture decks are
# read-only inputs; the generator never writes to them.
REFERENCE_DIR = DATA_DIR / "reference"
LECTURE_DECKS_ROOT = DATA_DIR / "lecturedecks"


def subject_papers_dir(subject: str) -> Path:
    return PAPERS_ROOT / str(subject).strip().upper()


def subject_reference_dir(subject: str) -> Path:
    return REFERENCE_DIR / str(subject).strip().upper()


def subject_lecture_decks_dir(subject: str) -> Path:
    """Prefer data/lecturedecks/<SUBJECT>, then the legacy external KB folder.

    Set <SUBJECT>_DECKS_DIR (for example CSC662_DECKS_DIR) to override either.
    """
    code = str(subject).strip().upper()
    override = os.environ.get(f"{code}_DECKS_DIR")
    if override:
        return Path(override)
    local = LECTURE_DECKS_ROOT / code
    if local.is_dir() and any(local.glob("*.pptx")):
        return local
    return Path.home() / "Desktop" / code


# Backwards-compatible CSC662 aliases.
PAPERS_DIR = subject_papers_dir("CSC662")
LECTURE_DECKS_DIR = subject_lecture_decks_dir("CSC662")
THEORY_CACHE_DIR = TRACKING_DIR / "theory"

# --- LLM -----------------------------------------------------------------
# Provider: Qwen via its OpenAI-compatible endpoint (per project owner).
# Keys are NEVER hardcoded - they live in .env (gitignored) or the environment.
QWEN_API_KEY = os.environ.get("QWEN_API_KEY", "")
# key verified against the international compatible-mode endpoint 2026-10-18
QWEN_BASE_URL = os.environ.get(
    "QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
QWEN_MODEL = os.environ.get("MOCKGEN_QWEN_MODEL", "qwen3.8-max")
# Theory drafting uses the cheap model the brief asks for.  Keep it
# configurable; the report records the model actually used.
QWEN_CHEAP_MODEL = os.environ.get(
    "MOCKGEN_QWEN_CHEAP_MODEL", "deepseek-v4.1-flash-1017")

# DeepSeek platform (official OpenAI-compatible endpoint).  The current
# model id for DeepSeek-V4.1-Flash-1017 is simply "deepseek-flash".
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.environ.get(
    "DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.environ.get(
    "MOCKGEN_DEEPSEEK_MODEL", "deepseek-flash")

# Google Gemini (OpenAI-compatible endpoint).  Used as the default model for
# public-build generation; local builds keep DeepSeek unless overridden.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_BASE_URL = os.environ.get(
    "GEMINI_BASE_URL",
    "https://generativelanguage.googleapis.com/v1beta/openai/")
GEMINI_MODEL = os.environ.get(
    "MOCKGEN_GEMINI_MODEL", "gemini-3.5-flash")
# Gemini 3.5 Flash accepts reasoning_effort="none" on the OpenAI-compatible
# endpoint; this keeps thinking tokens (and latency/cost) out of drafting.
# Set MOCKGEN_GEMINI_REASONING_EFFORT="" for models that reject the field.
GEMINI_REASONING_EFFORT = os.environ.get(
    "MOCKGEN_GEMINI_REASONING_EFFORT", "none").strip()


def _looks_like_placeholder(value: str) -> bool:
    """Reject template values such as REPLACE_WITH_GEMINI_API_KEY."""
    text = str(value or "").strip().upper()
    return (not text or text.startswith(("REPLACE", "YOUR_", "CHANGE_"))
            or "PLACEHOLDER" in text or text in {"XXX", "TODO", "SECRET"})


def _key_usable(value: str) -> bool:
    return bool(value) and not _looks_like_placeholder(value)
# Primary evaluation model for the final hardened run.
MOCKGEN_MODEL = os.environ.get("MOCKGEN_MODEL") or DEEPSEEK_MODEL
LLM_MAX_RETRIES = 3
# Cost estimation.  Defaults are the public qwen-flash list prices seen in
# the provider price listings on 2026-10-19 (USD per 1M tokens); override
# them in .env for the exact account/model.  Prices are estimates only.
QWEN_INPUT_PRICE_PER_1M = float(
    os.environ.get("MOCKGEN_QWEN_INPUT_PRICE_PER_1M", "0.022"))
QWEN_OUTPUT_PRICE_PER_1M = float(
    os.environ.get("MOCKGEN_QWEN_OUTPUT_PRICE_PER_1M", "0.216"))

# Per-model estimate table (USD per 1M tokens).  These are estimates from
# public provider listings on 2026-10-20, not invoices; override in .env or
# update here for exact account pricing.
MODEL_PRICES: dict[str, tuple[float, float]] = {
    # Official DeepSeek platform peak cache-miss rates for
    # DeepSeek-V4.1-Flash-1017: $0.30 input / $1.20 output per 1M tokens.
    # Off-peak rates are half ($0.15 / $0.60); using peak rates here is a
    # conservative estimate for the evaluation.
    "deepseek-flash": (0.30, 1.20),
    "deepseek-v4.1-flash-1017": (0.30, 1.20),
    "deepseek-v4.1-flash": (0.30, 1.20),
    "deepseek-v4-flash-0731": (0.30, 1.20),
    "qwen3.8-flash": (0.02, 0.20),
    "qwen3.6-flash": (0.02, 0.20),
    "qwen3.5-flash": (0.02, 0.20),
    "qwen-flash": (0.022, 0.216),
    "qwen3.6-plus": (0.10, 0.30),
    "qwen3.8-max": (1.20, 6.00),
    # Gemini estimates; the cost cap uses these values.
    "gemini-3.5-flash": (0.30, 2.50),
    "gemini-3.5-flash-lite": (0.10, 0.40),
    "gemini-3.1-flash-lite": (0.10, 0.40),
}

# --- theory thresholds ---------------------------------------------------
# First gate: Snowball-stemmed content-token overlap.  Points below this
# threshold go to the LLM entailment checker; only "no" is regenerated.
THEORY_STEM_OVERLAP_THRESHOLD = float(
    os.environ.get("MOCKGEN_STEM_OVERLAP_THRESHOLD",
                   os.environ.get("MOCKGEN_TERM_OVERLAP_THRESHOLD", "0.50")))
# Legacy alias for older scripts; new code reads THEORY_STEM_OVERLAP_THRESHOLD.
THEORY_TERM_OVERLAP_THRESHOLD = THEORY_STEM_OVERLAP_THRESHOLD
THEORY_NEAR_COPY_THRESHOLD = float(
    os.environ.get("MOCKGEN_NEAR_COPY_THRESHOLD", "0.80"))
# Measured Part B scenario rate: 7/19 clean A/B questions (a lower bound).
THEORY_SCENARIO_RATE = float(
    os.environ.get("MOCKGEN_SCENARIO_RATE", "0.3684210526315789"))

# --- web app -------------------------------------------------------------
# Local-only study tool. PUBLIC_BUILD strips university branding and disables
# the Library (which is built from real course material).
PUBLIC_BUILD = os.environ.get("PUBLIC_BUILD", "0") == "1"
# Public-build generation defaults to Gemini when the key is configured.
# MOCKGEN_MODEL always wins if the operator set it explicitly.
if PUBLIC_BUILD and not os.environ.get("MOCKGEN_MODEL", "").strip():
    # Public builds use Gemini even when the key is missing/placeholder, so
    # they fail closed instead of silently falling back to another provider.
    MOCKGEN_MODEL = os.environ.get("MOCKGEN_PUBLIC_MODEL", GEMINI_MODEL)


def llm_key_ready(model: str | None = None) -> bool:
    """Whether a usable API key for the active model is configured."""
    name = str(model or MOCKGEN_MODEL)
    if name.startswith("gemini-"):
        return _key_usable(GEMINI_API_KEY)
    if name == DEEPSEEK_MODEL:
        return _key_usable(DEEPSEEK_API_KEY)
    return _key_usable(QWEN_API_KEY)


# Public builds keep the original local-build cover by default. Set
# MOCKGEN_PUBLIC_STRIP_BRANDING=1 to restore the old generic-cover behaviour.
PUBLIC_STRIP_BRANDING = os.environ.get(
    "MOCKGEN_PUBLIC_STRIP_BRANDING", "0") == "1"
SITE_NAME = os.environ.get("MOCKGEN_SITE_NAME", "Mock Paper Generator")
# Public deployment used by the local app's gallery-share proxy.
PUBLIC_SITE_URL = os.environ.get(
    "MOCKGEN_PUBLIC_SITE_URL", "https://uitmpapergen.download").rstrip("/")
CONTACT_EMAIL = os.environ.get("MOCKGEN_CONTACT_EMAIL",
                               "auzair1990@gmail.com")
REPO_URL = os.environ.get("MOCKGEN_REPO_URL",
                          "https://github.com/jerkfish/paper-generator")
WEB_COST_CAP_USD = float(
    os.environ.get("MOCKGEN_COST_CAP_USD", "0.05"))
WEB_RUNS_DIR = OUTPUTS_DIR / "web_runs"
WEB_CACHE_DIR = OUTPUTS_DIR / "web_cache"
WEB_LIBRARY_DIR = OUTPUTS_DIR / "web_library"

# --- thresholds ----------------------------------------------------------
OCR_MIN_TEXT_CHARS = 50  # below this, a cover is treated as scanned (no text layer)

# --- rendering -----------------------------------------------------------
USE_REAL_CREST = os.environ.get("MOCKGEN_USE_REAL_CREST", "1") == "1"
CREST_PATH = subject_reference_dir("CSC662") / "crest.png"
