from __future__ import annotations

import math

import pytest

from app.nlp.config import NlpSettings
from app.nlp.embeddings import build_embedding
from app.nlp.pipeline import NoteNlpPipeline
from app.nlp.types import BlockTextInput


def test_pipeline_extracts_entities_keyphrases_relations_and_embedding() -> None:
    pipeline = NoteNlpPipeline(
        settings=NlpSettings(
            model_name="rule-based-small",
            enable_embeddings=True,
            process_min_text_len=3,
            timeout_ms=2000,
            extraction_profile="rule-only",
            enable_regex_fallback=True,
            entity_seed_terms=(),
        )
    )

    result = pipeline.extract(
        note_id="note-nlp-1",
        content_text="Machine Learning improves Pattern Discovery. Neural Networks support Data Science.",
        content_hash="hash-nlp-1",
        blocks=[
            BlockTextInput(block_index=0, content_text="Machine Learning improves Pattern Discovery."),
            BlockTextInput(block_index=1, content_text="Neural Networks support Data Science."),
        ],
        dictionary_terms=["machine learning", "neural networks"],
    )

    assert result.note_id == "note-nlp-1"
    assert result.content_hash == "hash-nlp-1"
    assert result.entities
    assert any(entity.text == "Machine Learning" for entity in result.entities)
    assert result.entity_mentions
    assert result.entity_mentions[0].block_index == 0
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
            extraction_profile="rule-only",
            enable_regex_fallback=True,
            entity_seed_terms=(),
        )
    )

    result = pipeline.extract(
        note_id="note-nlp-2",
        content_text="Too short",
        content_hash="hash-nlp-2",
    )

    assert result.entities == []
    assert result.entity_mentions == []
    assert result.keyphrases == []
    assert result.relations == []
    assert result.embedding is None


class _FakeEnt:
    def __init__(self, *, text: str, start_char: int, end_char: int, label_: str = "ORG") -> None:
        self.text = text
        self.start_char = start_char
        self.end_char = end_char
        self.label_ = label_


class _FakeDoc:
    def __init__(self, ents: list[_FakeEnt]) -> None:
        self.ents = ents


class _FakeNlp:
    def __init__(self) -> None:
        self.pipe_names = ["ner"]

    def add_pipe(self, _name: str, _before: str | None = None) -> object:
        return self

    def get_pipe(self, _name: str) -> object:
        return self

    def add_patterns(self, _patterns: list[dict[str, object]]) -> None:
        return None

    def __call__(self, text: str) -> _FakeDoc:
        lowered = text.lower()
        target = "graph reasoning"
        start = lowered.find(target)
        if start < 0:
            return _FakeDoc([])
        return _FakeDoc(
            [
                _FakeEnt(
                    text=text[start : start + len(target)],
                    start_char=start,
                    end_char=start + len(target),
                )
            ]
        )


def test_pipeline_records_per_layer_extraction_counts(monkeypatch: pytest.MonkeyPatch) -> None:
    pipeline = NoteNlpPipeline(
        settings=NlpSettings(
            model_name="spacy:fake",
            enable_embeddings=False,
            process_min_text_len=1,
            timeout_ms=2000,
            extraction_profile="hybrid-spacy",
            enable_regex_fallback=True,
            entity_seed_terms=("entity resolution",),
        )
    )
    monkeypatch.setattr(pipeline, "_get_model_handle", lambda _model_name: _FakeNlp())

    result = pipeline.extract(
        note_id="note-nlp-layer-counts",
        content_text="graph reasoning improves retrieval",
        content_hash="hash-nlp-layer-counts",
        blocks=[
            BlockTextInput(block_index=0, content_text="graph reasoning improves retrieval"),
            BlockTextInput(block_index=1, content_text="entity resolution improves linking"),
        ],
        dictionary_terms=["graph reasoning"],
    )

    assert result.entities
    counts = pipeline.get_last_extraction_hit_counts()
    assert counts["dictionary_hits"] >= 2
    assert counts["spacy_hits"] >= 1
    assert counts["merged_mentions"] >= 2


def test_build_embedding_is_stable_and_normalized() -> None:
    first = build_embedding("graph databases connect entities")
    second = build_embedding("graph databases connect entities")

    assert first == second
    assert len(first) == 384
    norm = math.sqrt(sum(value * value for value in first))
    assert norm == pytest.approx(1.0, abs=1e-9)
