from __future__ import annotations

from app.nlp.resolution.ranking import RankedResolutionCandidate, rank_resolution_candidates


def test_ranker_prefers_higher_weighted_layer_and_confidence() -> None:
    ranked = rank_resolution_candidates(
        [
            RankedResolutionCandidate(
                canonical_entity_id="concept-b",
                canonical_name="Beta",
                matched_layer="fuzzy",
                confidence=0.95,
                lexical_specificity=2,
            ),
            RankedResolutionCandidate(
                canonical_entity_id="concept-a",
                canonical_name="Alpha",
                matched_layer="alias_table",
                confidence=0.8,
                lexical_specificity=1,
            ),
        ]
    )

    assert ranked[0].canonical_entity_id == "concept-a"


def test_ranker_uses_stable_tiebreak_for_equal_scores() -> None:
    ranked = rank_resolution_candidates(
        [
            RankedResolutionCandidate(
                canonical_entity_id="concept-z",
                canonical_name="Zulu",
                matched_layer="fuzzy",
                confidence=0.8,
                lexical_specificity=1,
            ),
            RankedResolutionCandidate(
                canonical_entity_id="concept-a",
                canonical_name="Alpha",
                matched_layer="fuzzy",
                confidence=0.8,
                lexical_specificity=1,
            ),
        ]
    )

    assert [item.canonical_entity_id for item in ranked] == ["concept-a", "concept-z"]

