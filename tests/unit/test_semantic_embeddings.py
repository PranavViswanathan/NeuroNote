"""Unit tests for semantic embeddings module."""
from __future__ import annotations

from unittest.mock import MagicMock, patch


from app.nlp.semantic_embeddings import SemanticEmbedder, build_semantic_embedding


def setup_function() -> None:
    # Reset singleton between tests
    SemanticEmbedder._instance = None


def test_build_semantic_embedding_returns_none_when_model_unavailable() -> None:
    SemanticEmbedder._instance = None
    with patch.dict("sys.modules", {"sentence_transformers": None}):
        result = build_semantic_embedding("hello world")
    assert result is None


def test_build_semantic_embedding_returns_float_list_when_model_available() -> None:
    SemanticEmbedder._instance = None
    mock_model = MagicMock()
    import numpy as np
    mock_model.encode.return_value = np.array([0.1] * 384, dtype="float32")

    with patch("app.nlp.semantic_embeddings.SemanticEmbedder.get", return_value=mock_model):
        result = build_semantic_embedding("the quick brown fox")

    assert result is not None
    assert len(result) == 384
    assert all(isinstance(v, float) for v in result)


def test_build_semantic_embedding_different_texts_produce_different_vectors() -> None:
    """Verifies the mock is called with different inputs — not a real semantic test."""
    SemanticEmbedder._instance = None
    import numpy as np

    call_count = [0]

    def fake_encode(text: str, **kwargs: object) -> object:
        call_count[0] += 1
        # Return different vectors for different texts
        seed = sum(ord(c) for c in text) % 256
        rng = np.random.default_rng(seed)
        return rng.random(384).astype("float32")

    mock_model = MagicMock()
    mock_model.encode.side_effect = fake_encode

    with patch("app.nlp.semantic_embeddings.SemanticEmbedder.get", return_value=mock_model):
        v1 = build_semantic_embedding("cat")
        v2 = build_semantic_embedding("quantum computing")

    assert v1 is not None
    assert v2 is not None
    assert v1 != v2


def test_build_semantic_embedding_returns_none_on_encode_error() -> None:
    SemanticEmbedder._instance = None
    mock_model = MagicMock()
    mock_model.encode.side_effect = RuntimeError("CUDA out of memory")

    with patch("app.nlp.semantic_embeddings.SemanticEmbedder.get", return_value=mock_model):
        result = build_semantic_embedding("some text")

    assert result is None
