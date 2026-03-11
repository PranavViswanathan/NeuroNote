from __future__ import annotations

from difflib import SequenceMatcher

from app.nlp.resolution.normalization import normalize_entity_text


def fuzzy_similarity(a: str, b: str) -> float:
    """Return fuzzy similarity score in [0, 1]."""
    normalized_a = normalize_entity_text(a)
    normalized_b = normalize_entity_text(b)
    if not normalized_a and not normalized_b:
        return 1.0
    if not normalized_a or not normalized_b:
        return 0.0
    return SequenceMatcher(a=normalized_a, b=normalized_b).ratio()


def find_fuzzy_candidate(*, entity_text: str, candidates: list[str], threshold: float) -> tuple[str, float] | None:
    """Return best fuzzy candidate when threshold is met."""
    best_candidate = ""
    best_score = -1.0
    for candidate in candidates:
        score = fuzzy_similarity(entity_text, candidate)
        if score > best_score:
            best_score = score
            best_candidate = candidate

    if best_score >= threshold and best_candidate:
        return best_candidate, best_score
    return None
