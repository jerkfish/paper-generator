"""Tiny LLM client wrapper (Qwen via its OpenAI-compatible endpoint)."""
from __future__ import annotations

import json

from openai import OpenAI

from src import config

_client: OpenAI | None = None


def client() -> OpenAI:
    global _client
    if _client is None:
        if not config.QWEN_API_KEY:
            raise RuntimeError("QWEN_API_KEY is not set (see .env)")
        _client = OpenAI(api_key=config.QWEN_API_KEY, base_url=config.QWEN_BASE_URL,
                         timeout=180.0)
    return _client


def _extract_json(content: str) -> str:
    start, end = content.find("{"), content.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object in LLM reply")
    return content[start:end + 1]


def chat_json(system: str, user: str, model: str | None = None,
              temperature: float = 0.2) -> dict:
    """Chat completion forced into a JSON object, with retries."""
    last_err: Exception | None = None
    use_json_mode = True
    for _ in range(config.LLM_MAX_RETRIES):
        try:
            kwargs: dict = {
                "model": model or config.QWEN_MODEL,
                "messages": [{"role": "system", "content": system},
                             {"role": "user", "content": user}],
                "temperature": temperature,
                # Qwen thinking models are slow and charge reasoning tokens;
                # labelling needs none of it.
                "extra_body": {"enable_thinking": False},
                "max_tokens": 8000,
            }
            if use_json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            resp = client().chat.completions.create(**kwargs)
            content = resp.choices[0].message.content or ""
            return json.loads(_extract_json(content))
        except Exception as e:  # retry on any failure; json_mode may be unsupported
            last_err = e
            use_json_mode = False
    raise RuntimeError(f"LLM call failed after {config.LLM_MAX_RETRIES} tries: {last_err}")
