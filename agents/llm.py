"""OpenRouter client.

OpenRouter is OpenAI-compatible, so the official SDK works with a base_url swap.
`chat` retries transient failures — including the error payloads OpenRouter
returns as HTTP 200 with `choices: null` — and raises a clear message rather than
an opaque `NoneType` if every attempt fails.

Status: implemented.
"""

from __future__ import annotations

import os
import time

from openai import OpenAI

BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "deepseek/deepseek-v4-pro"


class LLM:
    def __init__(self, model: str | None = None, api_key: str | None = None) -> None:
        self.model = model or os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL)
        key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not set. Copy .env.example to .env and add "
                "the key, or pass api_key=. In containers it comes from compose."
            )
        self.client = OpenAI(base_url=BASE_URL, api_key=key)

    def chat(self, messages: list[dict], temperature: float = 1.0,
             tools: list[dict] | None = None, retries: int = 3):
        """Return the raw message object, retrying transient failures.

        The whole message is returned (not just its text): tool calls are what
        the run log records, and the covert-reporting comparison turns on them.
        """
        kwargs: dict = {"model": self.model, "messages": messages,
                        "temperature": temperature}
        if tools:
            kwargs["tools"] = tools

        last = "unknown error"
        for attempt in range(retries):
            try:
                resp = self.client.chat.completions.create(**kwargs)
            except Exception as e:  # network / rate-limit / provider error
                last = f"{type(e).__name__}: {e}"
            else:
                if resp and resp.choices:
                    return resp.choices[0].message
                # HTTP 200 with an error body and no choices
                try:
                    last = f"no choices; error={resp.model_dump().get('error')}"
                except Exception:
                    last = "no choices in response"
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"chat failed after {retries} attempts: {last}")
