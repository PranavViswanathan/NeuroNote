from __future__ import annotations

import math

import pytest

from app.nlp.config import NlpSettings
from app.nlp.embeddings import build_embedding
from app.nlp.pipeline import NoteNlpPipeline


def test_pipeline_extracts_entities_keyphrases_relations_and_embedding() -> None:
    pipeline = NoteNlpPipeline(
        settings=NlpSettings(
            model_name="rule-based-small",
            enable_embeddings=True,
            process_min_text_len=3,
            timeout_ms=2000,
        )
    )

    result = pipeline.extract(
        note_id="note-nlp-1",
        content_text="Machine Learning improves Pattern Discovery. Neural Networks support Data Science.",
        content_hash="hash-nlp-1",
    )

    assert result.note_id == "note-nlp-1"
    assert result.content_hash == "hash-nlp-1"
    assert result.entities
    assert any(entity.text == "Machine Learning" for entity in result.entities)
    assert result.keyphrases
    assert any(phrase.text == "machine learning" for phrase in result.keyphrases)
    assert result.relations
    assert any(relation.predicate == "IMPROVES" for relation in result.relations)
    assert result.embedding is not None
    assert len(result.embedding) == 384


def test_pipeline_respects_minimum_text_length_threshold() -> None:
    pipeline = NoteNlpPipeline(
        settings=NlpSettings(
            model_name="rule-based-small",
            enable_embeddings=True,
            process_min_text_len=100,
            timeout_ms=2000,
        )
    )

    result = pipeline.extract(
        note_id="note-nlp-2",
        content_text="Too short",
        content_hash="hash-nlp-2",
    )

    assert result.entities == []
    assert result.keyphrases == []
    assert result.relations == []
    assert result.embedding is None


def test_build_embedding_is_stable_and_normalized() -> None:
    first = build_embedding("graph databases connect entities")
    second = build_embedding("graph databases connect entities")

    assert first == second
    assert len(first) == 384
    norm = math.sqrt(sum(value * value for value in first))
    assert norm == pytest.approx(1.0, abs=1e-9)
