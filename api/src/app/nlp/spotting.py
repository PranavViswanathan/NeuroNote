from __future__ import annotations

from dataclasses import dataclass
import re

from app.nlp.types import BlockTextInput, ExtractedEntity, ExtractedEntityMention

_TITLE_CASE_PATTERN = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b")
_ACRONYM_PATTERN = re.compile(r"\b[A-Z]{2,10}\b")

_DICTIONARY_CONFIDENCE = 0.93
_TITLE_CASE_CONFIDENCE = 0.85
_ACRONYM_CONFIDENCE = 0.75


@dataclass(frozen=True, slots=True)
class _SpanCandidate:
    text: str
    label: str
    confidence: float
    start_offset: int
    end_offset: int


def _slugify(raw_text: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", raw_text.lower()).strip("-")
    return normalized or "entity"


def _normalize_term(term: str) -> str:
    return " ".join(term.strip().split())


def _dictionary_candidates(block_text: str, dictionary_terms: list[str]) -> list[_SpanCandidate]:
    candidates: list[_SpanCandidate] = []
    for raw_term in dictionary_terms:
        term = _normalize_term(raw_term)
        if len(term) < 2:
            continue
        pattern = re.compile(rf"(?<!\w){re.escape(term)}(?!\w)", flags=re.IGNORECASE)
        for match in pattern.finditer(block_text):
            candidates.append(
                _SpanCandidate(
                    text=match.group(0),
                    label="dictionary",
                    confidence=_DICTIONARY_CONFIDENCE,
                    start_offset=match.start(),
                    end_offset=match.end(),
                )
            )
    return candidates


def _fallback_candidates(block_text: str) -> list[_SpanCandidate]:
    candidates: list[_SpanCandidate] = []
    for match in _TITLE_CASE_PATTERN.finditer(block_text):
        candidates.append(
            _SpanCandidate(
                text=match.group(0),
                label="proper_noun",
                confidence=_TITLE_CASE_CONFIDENCE,
                start_offset=match.start(),
                end_offset=match.end(),
            )
        )
    for match in _ACRONYM_PATTERN.finditer(block_text):
        candidates.append(
            _SpanCandidate(
                text=match.group(0),
                label="acronym",
                confidence=_ACRONYM_CONFIDENCE,
                start_offset=match.start(),
                end_offset=match.end(),
            )
        )
    return candidates


def extract_entities_with_mentions(
    *,
    blocks: list[BlockTextInput],
    dictionary_terms: list[str] | None = None,
) -> tuple[list[ExtractedEntity], list[ExtractedEntityMention]]:
    entity_index: dict[str, ExtractedEntity] = {}
    mentions: list[ExtractedEntityMention] = []
    seen_mentions: set[tuple[str, int, int, int]] = set()
    dictionary_terms = dictionary_terms or []

    for block in sorted(blocks, key=lambda item: item.block_index):
        block_text = block.content_text
        if not block_text.strip():
            continue

        candidates = _dictionary_candidates(block_text, dictionary_terms)
        candidates.extend(_fallback_candidates(block_text))
        candidates.sort(key=lambda item: (item.start_offset, item.end_offset, item.text.lower()))

        for candidate in candidates:
            normalized_text = _normalize_term(candidate.text)
            if not normalized_text:
                continue
            key = normalized_text.lower()
            entity_id = f"entity-{_slugify(normalized_text)}"
            existing_entity = entity_index.get(key)
            if existing_entity is None or candidate.confidence > existing_entity.confidence:
                entity_index[key] = ExtractedEntity(
                    entity_id=entity_id,
                    text=normalized_text,
                    label=candidate.label,
                    confidence=candidate.confidence,
                )

            mention_key = (
                entity_id,
                block.block_index,
                candidate.start_offset,
                candidate.end_offset,
            )
            if mention_key in seen_mentions:
                continue
            seen_mentions.add(mention_key)
            mentions.append(
                ExtractedEntityMention(
                    entity_id=entity_id,
                    block_index=block.block_index,
                    mention_text=normalized_text,
                    start_offset=candidate.start_offset,
                    end_offset=candidate.end_offset,
                    confidence=candidate.confidence,
                )
            )

    entities = sorted(entity_index.values(), key=lambda item: item.entity_id)
    mentions.sort(
        key=lambda item: (
            item.block_index,
            item.start_offset,
            item.end_offset,
            item.entity_id,
        )
    )
    return entities, mentions

