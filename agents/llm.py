"""OpenRouter client.

OpenRouter is OpenAI-compatible, so the official SDK works against it with
nothing more than a base_url swap.

Status: implemented.
"""

from __future__ import annotations

import os

from openai import OpenAI

BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-5.6-sol"


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

    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.5,
        tools: list[dict] | None = None,
    ):
        """Return the raw message object.

        The agent loop needs the whole message, not just its text — tool calls
        are what the run log records, and the covert reporting condition turns
        on exactly what was called versus what appears to have been called.
        """
        kwargs: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
        return self.client.chat.completions.create(**kwargs).choices[0].message
