from __future__ import annotations

from app.nlp.config import get_nlp_settings


def test_nlp_settings_defaults_include_hybrid_controls(monkeypatch) -> None:
    monkeypatch.delenv("NLP_MODEL_NAME", raising=False)
    monkeypatch.delenv("NLP_EXTRACTION_PROFILE", raising=False)
    monkeypatch.delenv("NLP_ENABLE_REGEX_FALLBACK", raising=False)
    monkeypatch.delenv("NLP_ENTITY_SEED_TERMS", raising=False)

    settings = get_nlp_settings()

    assert settings.model_name == "rule-based-small"
    assert settings.extraction_profile == "rule-only"
    assert settings.enable_regex_fallback is True
    assert settings.entity_seed_terms


def test_nlp_settings_reads_profile_and_seed_terms(monkeypatch) -> None:
    monkeypatch.setenv("NLP_EXTRACTION_PROFILE", "hybrid-spacy")
    monkeypatch.setenv("NLP_ENABLE_REGEX_FALLBACK", "false")
    monkeypatch.setenv("NLP_ENTITY_SEED_TERMS", "graph reasoning, entity resolution,  machine learning ")

    settings = get_nlp_settings()

    assert settings.extraction_profile == "hybrid-spacy"
    assert settings.enable_regex_fallback is False
    assert settings.entity_seed_terms == (
        "graph reasoning",
        "entity resolution",
        "machine learning",
    )
