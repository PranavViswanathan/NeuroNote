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


def _as_profile(raw_value: str | None, *, default: str) -> str:
    if raw_value is None:
        return default
    normalized = raw_value.strip().lower()
    if normalized in {"rule-only", "hybrid-spacy", "llm-enhanced"}:
        return normalized
    return default


def _as_terms(raw_value: str | None, *, default: tuple[str, ...]) -> tuple[str, ...]:
    if raw_value is None:
        return default
    parts = [" ".join(item.split()).strip() for item in raw_value.split(",")]
    terms = tuple(item for item in parts if item)
    return terms or default


_DEFAULT_SEED_TERMS = (
    "machine learning",
    "entity resolution",
    "graph reasoning",
    "knowledge graph",
    "neural networks",
)


@dataclass(frozen=True, slots=True)
class NlpSettings:
    model_name: str
    enable_embeddings: bool
    process_min_text_len: int
    timeout_ms: int
    extraction_profile: str = "rule-only"
    enable_regex_fallback: bool = True
    entity_seed_terms: tuple[str, ...] = _DEFAULT_SEED_TERMS
    # LLM-enhanced profile settings
    llm_model: str = "claude-haiku-4-5-20251001"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.anthropic.com/v1/"
    llm_timeout_ms: int = 8000
    use_semantic_embeddings: bool = False


def get_nlp_settings() -> NlpSettings:
    return NlpSettings(
        model_name=os.getenv("NLP_MODEL_NAME", "rule-based-small"),
        enable_embeddings=_as_bool(os.getenv("NLP_ENABLE_EMBEDDINGS"), default=True),
        process_min_text_len=_as_int(os.getenv("NLP_PROCESS_MIN_TEXT_LEN"), default=3),
        timeout_ms=_as_int(os.getenv("NLP_TIMEOUT_MS"), default=2000),
        extraction_profile=_as_profile(
            os.getenv("NLP_EXTRACTION_PROFILE"),
            default="rule-only",
        ),
        enable_regex_fallback=_as_bool(
            os.getenv("NLP_ENABLE_REGEX_FALLBACK"),
            default=True,
        ),
        entity_seed_terms=_as_terms(
            os.getenv("NLP_ENTITY_SEED_TERMS"),
            default=_DEFAULT_SEED_TERMS,
        ),
        llm_model=os.getenv("NLP_LLM_MODEL", "claude-haiku-4-5-20251001"),
        llm_api_key=os.getenv("LLM_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or "",
        llm_base_url=os.getenv("LLM_BASE_URL", "https://api.anthropic.com/v1/"),
        llm_timeout_ms=_as_int(os.getenv("NLP_LLM_TIMEOUT_MS"), default=8000),
        use_semantic_embeddings=_as_bool(
            os.getenv("NLP_USE_SEMANTIC_EMBEDDINGS"), default=False
        ),
    )


__all__ = ["NlpSettings", "get_nlp_settings"]
