"""Tiny LLM client wrapper (Qwen via its OpenAI-compatible endpoint)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field

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


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    calls: int = 0

    def add(self, prompt: int, completion: int, total: int) -> None:
        self.prompt_tokens += int(prompt or 0)
        self.completion_tokens += int(completion or 0)
        self.total_tokens += int(total or 0)
        self.calls += 1

    @property
    def cost_usd(self) -> float:
        return (
            self.prompt_tokens / 1_000_000 * config.QWEN_INPUT_PRICE_PER_1M
            + self.completion_tokens / 1_000_000 * config.QWEN_OUTPUT_PRICE_PER_1M
        )

    def as_dict(self) -> dict:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "calls": self.calls,
            "cost_usd": round(self.cost_usd, 6),
            "input_price_per_1m": config.QWEN_INPUT_PRICE_PER_1M,
            "output_price_per_1m": config.QWEN_OUTPUT_PRICE_PER_1M,
        }


@dataclass
class LLMResult:
    data: dict
    model: str
    usage: Usage
    attempts: int = 1
    raw: str = ""
    usage_log: list[dict] = field(default_factory=list)


def chat_json_result(system: str, user: str, model: str | None = None,
                     temperature: float = 0.2,
                     usage: Usage | None = None) -> LLMResult:
    """Chat completion forced into a JSON object, with retries.

    Token usage is accumulated in `usage` across every attempt that received
    a response, including attempts whose JSON failed to parse.
    """
    usage = usage or Usage()
    last_err: Exception | None = None
    use_json_mode = True
    chosen_model = model or config.QWEN_MODEL
    for attempt in range(1, config.LLM_MAX_RETRIES + 1):
        try:
            kwargs: dict = {
                "model": chosen_model,
                "messages": [{"role": "system", "content": system},
                             {"role": "user", "content": user}],
                "temperature": temperature,
                # Qwen thinking models are slow and charge reasoning tokens;
                # question drafting needs none of it.
                "extra_body": {"enable_thinking": False},
                "max_tokens": 8000,
            }
            if use_json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            resp = client().chat.completions.create(**kwargs)
            u = getattr(resp, "usage", None)
            if u is not None:
                usage.add(getattr(u, "prompt_tokens", 0),
                          getattr(u, "completion_tokens", 0),
                          getattr(u, "total_tokens", 0))
            content = resp.choices[0].message.content or ""
            data = json.loads(_extract_json(content))
            return LLMResult(data=data, model=chosen_model, usage=usage,
                             attempts=attempt, raw=content)
        except Exception as e:  # retry on any failure; json_mode may be unsupported
            last_err = e
            use_json_mode = False
    raise RuntimeError(
        f"LLM call failed after {config.LLM_MAX_RETRIES} tries: {last_err}")


def chat_json(system: str, user: str, model: str | None = None,
              temperature: float = 0.2) -> dict:
    """Backward-compatible wrapper returning only the parsed object."""
    return chat_json_result(system, user, model=model,
                            temperature=temperature).data
