from __future__ import annotations

from dataclasses import dataclass

from app.nlp.resolution.abbreviation import find_abbreviation_expansion
from app.nlp.resolution.embedding import find_embedding_candidate
from app.nlp.resolution.fuzzy import find_fuzzy_candidate
from app.nlp.resolution.normalization import normalize_entity_text
from app.nlp.types import ExtractedEntity


@dataclass(frozen=True, slots=True)
class CanonicalAlias:
    canonical_entity_id: str
    canonical_name: str


@dataclass(frozen=True, slots=True)
class ResolvedEntity:
    source_entity_id: str
    source_text: str
    canonical_entity_id: str
    canonical_name: str
    confidence: float
    matched_layer: str


@dataclass(frozen=True, slots=True)
class UnresolvedEntity:
    source_entity_id: str
    source_text: str


@dataclass(frozen=True, slots=True)
class ResolutionBatch:
    resolved: list[ResolvedEntity]
    unresolved: list[UnresolvedEntity]


class EntityResolver:
    def __init__(
        self,
        *,
        alias_index: dict[str, CanonicalAlias] | None = None,
        abbreviation_index: dict[str, str] | None = None,
        fuzzy_threshold: float = 0.9,
        embedding_threshold: float = 0.85,
    ) -> None:
        self._alias_index = {
            normalize_entity_text(alias_key): alias
            for alias_key, alias in (alias_index or {}).items()
            if normalize_entity_text(alias_key)
        }
        self._abbreviation_index = {
            normalize_entity_text(alias_key).replace(" ", ""): normalize_entity_text(expansion)
            for alias_key, expansion in (abbreviation_index or {}).items()
            if normalize_entity_text(alias_key) and normalize_entity_text(expansion)
        }
        self._fuzzy_threshold = fuzzy_threshold
        self._embedding_threshold = embedding_threshold

    def _resolve_alias(self, alias_key: str) -> CanonicalAlias | None:
        return self._alias_index.get(normalize_entity_text(alias_key))

    def _append_resolved(
        self,
        *,
        resolved: list[ResolvedEntity],
        entity: ExtractedEntity,
        alias: CanonicalAlias,
        confidence: float,
        matched_layer: str,
    ) -> None:
        resolved.append(
            ResolvedEntity(
                source_entity_id=entity.entity_id,
                source_text=entity.text,
                canonical_entity_id=alias.canonical_entity_id,
                canonical_name=alias.canonical_name,
                confidence=confidence,
                matched_layer=matched_layer,
            )
        )

    def resolve(self, entities: list[ExtractedEntity]) -> ResolutionBatch:
        resolved: list[ResolvedEntity] = []
        unresolved: list[UnresolvedEntity] = []

        alias_candidates = list(self._alias_index.keys())
        for entity in entities:
            normalized_entity_text = normalize_entity_text(entity.text)
            if not normalized_entity_text:
                unresolved.append(
                    UnresolvedEntity(
                        source_entity_id=entity.entity_id,
                        source_text=entity.text,
                    )
                )
                continue

            direct_alias = self._resolve_alias(normalized_entity_text)
            if direct_alias is not None:
                self._append_resolved(
                    resolved=resolved,
                    entity=entity,
                    alias=direct_alias,
                    confidence=1.0,
                    matched_layer="alias_table",
                )
                continue

            abbreviation = find_abbreviation_expansion(
                entity_text=entity.text,
                alias_index=self._abbreviation_index,
            )
            if abbreviation is not None:
                abbreviation_alias = self._resolve_alias(abbreviation.expansion)
                if abbreviation_alias is not None:
                    self._append_resolved(
                        resolved=resolved,
                        entity=entity,
                        alias=abbreviation_alias,
                        confidence=abbreviation.confidence,
                        matched_layer="abbreviation",
                    )
                    continue

            fuzzy_match = find_fuzzy_candidate(
                entity_text=normalized_entity_text,
                candidates=alias_candidates,
                threshold=self._fuzzy_threshold,
            )
            if fuzzy_match is not None:
                fuzzy_alias = self._resolve_alias(fuzzy_match[0])
                if fuzzy_alias is not None:
                    self._append_resolved(
                        resolved=resolved,
                        entity=entity,
                        alias=fuzzy_alias,
                        confidence=fuzzy_match[1],
                        matched_layer="fuzzy",
                    )
                    continue

            embedding_match = find_embedding_candidate(
                entity_text=normalized_entity_text,
                candidates=alias_candidates,
                threshold=self._embedding_threshold,
            )
            if embedding_match is not None:
                embedding_alias = self._resolve_alias(embedding_match[0])
                if embedding_alias is not None:
                    self._append_resolved(
                        resolved=resolved,
                        entity=entity,
                        alias=embedding_alias,
                        confidence=embedding_match[1],
                        matched_layer="embedding",
                    )
                    continue

            unresolved.append(
                UnresolvedEntity(
                    source_entity_id=entity.entity_id,
                    source_text=entity.text,
                )
            )

        return ResolutionBatch(
            resolved=resolved,
            unresolved=unresolved,
        )
