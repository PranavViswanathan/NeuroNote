from __future__ import annotations

from dataclasses import dataclass
import os


def _as_bool(raw_value: str | None, *, default: bool) -> bool:
    if raw_value is None:
        return default
    normalized = raw_value.strip().lower()
    return normalized in {"1", "true", "yes", "on"}


def _as_int(raw_value: str | None, *, default: int) -> int:
    if raw_value is None:
        return default
    return int(raw_value)


@dataclass(frozen=True, slots=True)
class NlpSettings:
    model_name: str
    enable_embeddings: bool
    process_min_text_len: int
    timeout_ms: int


def get_nlp_settings() -> NlpSettings:
    return NlpSettings(
        model_name=os.getenv("NLP_MODEL_NAME", "rule-based-small"),
        enable_embeddings=_as_bool(os.getenv("NLP_ENABLE_EMBEDDINGS"), default=True),
        process_min_text_len=_as_int(os.getenv("NLP_PROCESS_MIN_TEXT_LEN"), default=3),
        timeout_ms=_as_int(os.getenv("NLP_TIMEOUT_MS"), default=2000),
    )


__all__ = ["NlpSettings", "get_nlp_settings"]
