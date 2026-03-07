from __future__ import annotations

import re

from app.nlp.types import ExtractedEntity

_TITLE_CASE_PATTERN = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b")
_ACRONYM_PATTERN = re.compile(r"\b[A-Z]{2,10}\b")


def _slugify(raw_text: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", raw_text.lower()).strip("-")
    return normalized or "entity"


def extract_entities(text: str) -> list[ExtractedEntity]:
    entities: list[ExtractedEntity] = []
    seen: set[str] = set()

    for match in _TITLE_CASE_PATTERN.findall(text):
        key = match.lower()
        if key in seen:
            continue
        seen.add(key)
        entities.append(
            ExtractedEntity(
                entity_id=f"entity-{_slugify(match)}",
                text=match,
                label="proper_noun",
                confidence=0.85,
            )
        )

    for match in _ACRONYM_PATTERN.findall(text):
        key = match.lower()
        if key in seen:
            continue
        seen.add(key)
        entities.append(
            ExtractedEntity(
                entity_id=f"entity-{_slugify(match)}",
                text=match,
                label="acronym",
                confidence=0.75,
            )
        )

    return entities
