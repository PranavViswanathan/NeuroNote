from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RankedResolutionCandidate:
    canonical_entity_id: str
    canonical_name: str
    matched_layer: str
    confidence: float
    lexical_specificity: int


_LAYER_WEIGHTS = {
    "alias_table": 1.0,
    "abbreviation": 0.92,
    "fuzzy": 0.82,
    "embedding": 0.74,
}


def rank_resolution_candidates(
    candidates: list[RankedResolutionCandidate],
) -> list[RankedResolutionCandidate]:
    def _score(item: RankedResolutionCandidate) -> float:
        base = _LAYER_WEIGHTS.get(item.matched_layer, 0.0)
        confidence_component = max(0.0, min(1.0, float(item.confidence))) * 0.25
        specificity_component = min(item.lexical_specificity, 4) * 0.01
        return base + confidence_component + specificity_component

    return sorted(
        candidates,
        key=lambda item: (
            -_score(item),
            item.canonical_entity_id,
            item.canonical_name,
            item.matched_layer,
        ),
    )

