"""Unit tests for SLMExtractor and the llm-enhanced pipeline branch."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.nlp.slm_extractor import SLMExtractor, SLMExtractionResult, _parse_result


# ── _parse_result ────────────────────────────────────────────────────────────

def test_parse_result_happy_path() -> None:
    raw = """{
        "concepts": [
            {"text": "Machine Learning", "confidence": 0.95},
            {"text": "backpropagation", "confidence": 0.88}
        ],
        "relations": [
            {"source": "backpropagation", "type": "USES", "target": "machine learning", "confidence": 0.85}
        ],
        "summary": "Notes on ML training via backpropagation."
    }"""
    result = _parse_result(raw)
    assert result is not None
    assert len(result.concepts) == 2
    # concepts are normalised to lowercase
    assert result.concepts[0].text == "machine learning"
    assert result.concepts[1].text == "backpropagation"
    assert result.concepts[0].confidence == pytest.approx(0.95)
    assert len(result.relations) == 1
    assert result.relations[0].type == "USES"
    assert result.relations[0].source == "backpropagation"
    assert result.summary == "Notes on ML training via backpropagation."


def test_parse_result_invalid_relation_type_dropped() -> None:
    raw = """{
        "concepts": [{"text": "neural network", "confidence": 0.9}],
        "relations": [
            {"source": "neural network", "type": "INVENTED_BY", "target": "turing", "confidence": 0.7}
        ],
        "summary": "A note."
    }"""
    result = _parse_result(raw)
    assert result is not None
    assert result.relations == []


def test_parse_result_invalid_json_returns_none() -> None:
    assert _parse_result("not json at all") is None


def test_parse_result_non_dict_returns_none() -> None:
    assert _parse_result("[1, 2, 3]") is None


def test_parse_result_empty_concept_text_skipped() -> None:
    raw = '{"concepts": [{"text": "", "confidence": 0.9}], "relations": [], "summary": ""}'
    result = _parse_result(raw)
    assert result is not None
    assert result.concepts == []


def test_parse_result_confidence_clamped() -> None:
    raw = '{"concepts": [{"text": "test", "confidence": 9.9}], "relations": [], "summary": ""}'
    result = _parse_result(raw)
    assert result is not None
    assert result.concepts[0].confidence == pytest.approx(1.0)


# ── SLMExtractor ─────────────────────────────────────────────────────────────

def _make_mock_anthropic_response(text: str) -> MagicMock:
    content_block = MagicMock()
    content_block.text = text
    message = MagicMock()
    message.content = [content_block]
    return message


def test_slm_extractor_returns_result_on_success() -> None:
    good_json = """{
        "concepts": [{"text": "transformer", "confidence": 0.92}],
        "relations": [],
        "summary": "Transformers use self-attention."
    }"""
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_mock_anthropic_response(good_json)

    mock_anthropic_module = MagicMock()
    mock_anthropic_module.Anthropic.return_value = mock_client

    extractor = SLMExtractor(model="claude-haiku-4-5-20251001", api_key="test-key")

    with patch.dict("sys.modules", {"anthropic": mock_anthropic_module}):
        result = extractor.extract(
            title="Transformers",
            content="Transformers use self-attention for sequence modelling.",
            known_concepts=["neural network", "attention mechanism"],
        )

    assert result is not None
    assert result.concepts[0].text == "transformer"
    assert result.summary == "Transformers use self-attention."


def test_slm_extractor_returns_none_on_api_error() -> None:
    extractor = SLMExtractor(model="claude-haiku-4-5-20251001", api_key="test-key")

    mock_anthropic_module = MagicMock()
    mock_anthropic_module.Anthropic.return_value.messages.create.side_effect = RuntimeError("rate limit")

    with patch.dict("sys.modules", {"anthropic": mock_anthropic_module}):
        result = extractor.extract(title="Any", content="Any content", known_concepts=[])

    assert result is None


def test_slm_extractor_returns_none_when_anthropic_not_installed() -> None:
    import sys

    extractor = SLMExtractor(model="claude-haiku-4-5-20251001", api_key="test-key")

    # Temporarily remove anthropic from sys.modules and block re-import
    saved = sys.modules.pop("anthropic", None)
    try:
        with patch("builtins.__import__", side_effect=ImportError("No module named 'anthropic'")):
            result = extractor.extract(title="Any", content="Any content", known_concepts=[])
    finally:
        if saved is not None:
            sys.modules["anthropic"] = saved

    assert result is None


# ── llm-enhanced pipeline branch ─────────────────────────────────────────────

def test_pipeline_llm_enhanced_uses_slm_result() -> None:
    from app.nlp.config import NlpSettings
    from app.nlp.pipeline import NoteNlpPipeline

    slm_result = SLMExtractionResult(
        concepts=[],
        relations=[],
        summary="A test summary.",
    )
    mock_extractor = MagicMock()
    mock_extractor.extract.return_value = slm_result

    settings = NlpSettings(
        model_name="rule-based-small",
        enable_embeddings=False,
        process_min_text_len=1,
        timeout_ms=5000,
        extraction_profile="llm-enhanced",
        llm_api_key="test-key",
        llm_model="claude-haiku-4-5-20251001",
        use_semantic_embeddings=False,
    )
    pipeline = NoteNlpPipeline(settings=settings)
    pipeline._slm_extractor = mock_extractor

    result = pipeline.extract(
        note_id="note-llm-1",
        title="Test Note",
        content_text="Some test content about neural networks.",
        content_hash="hash-llm-1",
    )

    mock_extractor.extract.assert_called_once()
    assert result.summary == "A test summary."
    assert result.note_id == "note-llm-1"


def test_pipeline_llm_enhanced_falls_back_to_rule_based_on_slm_none() -> None:
    from app.nlp.config import NlpSettings
    from app.nlp.pipeline import NoteNlpPipeline

    mock_extractor = MagicMock()
    mock_extractor.extract.return_value = None  # SLM failed

    settings = NlpSettings(
        model_name="rule-based-small",
        enable_embeddings=False,
        process_min_text_len=1,
        timeout_ms=5000,
        extraction_profile="llm-enhanced",
        llm_api_key="test-key",
        llm_model="claude-haiku-4-5-20251001",
        use_semantic_embeddings=False,
    )
    pipeline = NoteNlpPipeline(settings=settings)
    pipeline._slm_extractor = mock_extractor

    # Should not raise; falls through to rule-based path
    result = pipeline.extract(
        note_id="note-fallback-1",
        title="Fallback Note",
        content_text="Machine learning is a field of artificial intelligence.",
        content_hash="hash-fallback-1",
    )

    assert result.note_id == "note-fallback-1"
    assert result.summary == ""  # rule-based produces no summary


def test_pipeline_llm_enhanced_concepts_are_lowercase() -> None:
    from app.nlp.config import NlpSettings
    from app.nlp.pipeline import NoteNlpPipeline
    from app.nlp.slm_extractor import SLMConcept

    slm_result = SLMExtractionResult(
        concepts=[
            SLMConcept(text="machine learning", confidence=0.9),
            SLMConcept(text="neural network", confidence=0.85),
        ],
        relations=[],
        summary="",
    )
    mock_extractor = MagicMock()
    mock_extractor.extract.return_value = slm_result

    settings = NlpSettings(
        model_name="rule-based-small",
        enable_embeddings=False,
        process_min_text_len=1,
        timeout_ms=5000,
        extraction_profile="llm-enhanced",
        llm_api_key="test-key",
        llm_model="claude-haiku-4-5-20251001",
        use_semantic_embeddings=False,
    )
    pipeline = NoteNlpPipeline(settings=settings)
    pipeline._slm_extractor = mock_extractor

    result = pipeline.extract(
        note_id="note-case-1",
        title="ML Note",
        content_text="Machine Learning and Neural Networks.",
        content_hash="hash-case-1",
    )

    entity_texts = [e.text for e in result.entities]
    assert all(t == t.lower() for t in entity_texts), f"Non-lowercase concepts: {entity_texts}"
