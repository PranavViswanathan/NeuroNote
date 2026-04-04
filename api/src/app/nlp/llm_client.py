"""Thin LLM client over any OpenAI-compatible endpoint.

Both sync and async. ``complete()`` returns the response text or ``None`` on any error.
Never raises.
"""
from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)


class LLMClient:
    """Sync completion via the openai SDK."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str,
        timeout_s: float = 15.0,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url
        self._timeout_s = timeout_s

    def complete(self, *, system: str, user: str, max_tokens: int) -> str | None:
        try:
            import openai

            client = openai.OpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
                timeout=self._timeout_s,
            )
            resp = client.chat.completions.create(
                model=self._model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            return resp.choices[0].message.content
        except Exception:
            _LOGGER.debug("LLMClient.complete failed", exc_info=True)
            return None


class AsyncLLMClient:
    """Async completion via the openai SDK."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str,
        timeout_s: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url
        self._timeout_s = timeout_s

    async def complete(self, *, system: str, user: str, max_tokens: int) -> str | None:
        try:
            import openai

            client = openai.AsyncOpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
                timeout=self._timeout_s,
            )
            resp = await client.chat.completions.create(
                model=self._model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            return resp.choices[0].message.content
        except Exception:
            _LOGGER.debug("AsyncLLMClient.complete failed", exc_info=True)
            return None


__all__ = ["LLMClient", "AsyncLLMClient"]
