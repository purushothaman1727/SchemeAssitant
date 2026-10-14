"""LLM client. Groq, OpenAI-compatible APIs and Ollama all speak /chat/completions."""
import logging
import time
from typing import Protocol

import httpx

from app.core.config import Settings

log = logging.getLogger("llm")


class LLMUnavailable(Exception):
    pass


class LLMClient(Protocol):
    name: str

    def complete(self, messages: list[dict], max_tokens: int = 700) -> str: ...


class NullLLM:
    """Used when no provider/key is configured; callers fall back to extractive answers."""

    name = "none"

    def complete(self, messages: list[dict], max_tokens: int = 700) -> str:
        raise LLMUnavailable("no LLM configured")


class ChatCompletionsClient:
    def __init__(self, base_url: str, model: str, api_key: str, timeout: int, name: str):
        self.base_url = base_url.rstrip("/")
        self.model, self.api_key, self.timeout, self.name = model, api_key, timeout, name

    def complete(self, messages: list[dict], max_tokens: int = 700) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        body = {"model": self.model, "messages": messages, "temperature": 0.1, "max_tokens": max_tokens}
        if self.model.startswith("openai/gpt-oss"):
            body["reasoning_effort"] = "low"  # fewer hidden tokens, faster, fits small TPM budgets
        r = self._post(body, headers)
        if r.status_code == 429:  # per-minute quota: wait briefly once, then give up
            time.sleep(_retry_after_seconds(r))
            r = self._post(body, headers)
        if r.status_code != 200:
            # Never log the response body: it can echo prompt content (profile data).
            log.warning("llm error", extra={"ctx": {"status": r.status_code, "provider": self.name}})
            raise LLMUnavailable(f"HTTP {r.status_code}")
        try:
            return r.json()["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, ValueError, AttributeError) as exc:
            raise LLMUnavailable("unexpected response shape") from exc

    def _post(self, body: dict, headers: dict) -> httpx.Response:
        try:
            return httpx.post(f"{self.base_url}/chat/completions", json=body, headers=headers,
                              timeout=self.timeout)
        except httpx.HTTPError as exc:
            raise LLMUnavailable(f"request failed: {type(exc).__name__}") from exc


def _retry_after_seconds(r: httpx.Response, cap: float = 20.0) -> float:
    try:
        return min(max(float(r.headers.get("retry-after", "")), 1.0), cap)
    except ValueError:
        return 6.0


def build_llm(settings: Settings) -> LLMClient:
    provider = settings.llm_provider.lower()
    if provider == "none":
        return NullLLM()
    if provider in ("groq", "openai_compatible") and not settings.llm_api_key:
        log.warning("LLM provider '%s' has no LLM_API_KEY; running without an LLM", provider)
        return NullLLM()
    base = settings.llm_base_url.rstrip("/")
    if provider == "ollama" and not base.endswith("/v1"):
        base += "/v1"
    return ChatCompletionsClient(base, settings.llm_model, settings.llm_api_key,
                                 settings.llm_timeout_seconds, provider)
