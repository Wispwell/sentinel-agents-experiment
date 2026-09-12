"""Minimal OpenRouter client.

"""

from __future__ import annotations

import os

import httpx

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"


class LLM:
    def __init__(self, model: str | None = None, api_key: str | None = None) -> None:
        self.model = model or os.environ.get("OPENROUTER_MODEL", "openai/gpt-5.6-sol")
        self.api_key = api_key or os.environ["OPENROUTER_API_KEY"]
        self._client = httpx.Client(timeout=120.0)

    def chat(self, messages: list[dict], temperature: float = 1.0) -> str:
        r = self._client.post(
            ENDPOINT,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            },
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    def close(self) -> None:
        self._client.close()
