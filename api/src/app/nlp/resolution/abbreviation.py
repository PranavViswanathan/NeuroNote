from __future__ import annotations

from dataclasses import dataclass

from app.nlp.resolution.normalization import normalize_entity_text


@dataclass(frozen=True, slots=True)
class AbbreviationMatch:
    expansion: str
    confidence: float


def find_abbreviation_expansion(*, entity_text: str, alias_index: dict[str, str]) -> AbbreviationMatch | None:
    """Resolve acronym-like forms (for example ML -> machine learning)."""
    normalized = normalize_entity_text(entity_text).replace(" ", "")
    if len(normalized) < 2:
        return None

    expansion = alias_index.get(normalized)
    if expansion is None:
        return None

    return AbbreviationMatch(
        expansion=normalize_entity_text(expansion),
        confidence=0.95,
    )
