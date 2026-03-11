from __future__ import annotations

from app.nlp.resolution.abbreviation import find_abbreviation_expansion
from app.nlp.resolution.embedding import find_embedding_candidate
from app.nlp.resolution.fuzzy import find_fuzzy_candidate, fuzzy_similarity
from app.nlp.resolution.normalization import normalize_entity_text


def test_normalize_entity_text_collapses_case_hyphen_and_whitespace() -> None:
    assert normalize_entity_text("  Machine-Learning__   ") == "machine learning"


def test_find_abbreviation_expansion_uses_alias_index() -> None:
    match = find_abbreviation_expansion(
        entity_text="ML",
        alias_index={"ml": "machine learning"},
    )

    assert match is not None
    assert match.expansion == "machine learning"
    assert match.confidence == 0.95


def test_find_fuzzy_candidate_respects_threshold_boundary() -> None:
    candidate_text = "machine learning"
    noisy_text = "machine learnng"
    score = fuzzy_similarity(noisy_text, candidate_text)

    should_match = find_fuzzy_candidate(
        entity_text=noisy_text,
        candidates=[candidate_text],
        threshold=max(0.0, score - 1e-6),
    )
    should_not_match = find_fuzzy_candidate(
        entity_text=noisy_text,
        candidates=[candidate_text],
        threshold=min(1.0, score + 1e-6),
    )

    assert should_match is not None
    assert should_match[0] == candidate_text
    assert should_match[1] == score
    assert should_not_match is None


def test_find_embedding_candidate_respects_threshold_boundary() -> None:
    candidate = find_embedding_candidate(
        entity_text="Graph Databases",
        candidates=["Graph Databases", "Linear Algebra"],
        threshold=0.0,
    )
    assert candidate is not None

    strict_miss = find_embedding_candidate(
        entity_text="Graph Databases",
        candidates=["Graph Databases", "Linear Algebra"],
        threshold=candidate[1] + 1e-6,
    )

    assert candidate[0] == "Graph Databases"
    assert strict_miss is None
