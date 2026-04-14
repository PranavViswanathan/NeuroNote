"""Entity resolution service.

Builds the alias and abbreviation indexes required by EntityResolver and
provides a single, session-scoped entry point for resolving entity batches.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.repositories.entity_alias_repository import AliasRecord, EntityAliasRepository
from app.nlp.resolution.resolver import CanonicalAlias, EntityResolver, ResolutionBatch
from app.nlp.types import ExtractedEntity


class EntityResolutionService:
    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def build_resolver(alias_records: dict[str, AliasRecord]) -> EntityResolver:
        """Build an EntityResolver from a pre-loaded alias record map.

        Abbreviation index only includes aliases that are single tokens of
        2–10 characters (e.g. "ML", "NLP"), matching the heuristic used when
        the route and NoteProcessingService were separate.
        """
        alias_index: dict[str, CanonicalAlias] = {}
        abbreviation_index: dict[str, str] = {}
        for alias_text, record in alias_records.items():
            alias_index[alias_text] = CanonicalAlias(
                canonical_entity_id=record.canonical_entity_id,
                canonical_name=record.canonical_name,
            )
            if " " not in alias_text and 1 < len(alias_text) <= 10:
                abbreviation_index[alias_text.replace(" ", "")] = record.canonical_name
        return EntityResolver(
            alias_index=alias_index,
            abbreviation_index=abbreviation_index,
        )

    def preview_resolution(self, entities: list[ExtractedEntity]) -> ResolutionBatch:
        """Resolve a batch of entities against the current alias table."""
        alias_records = EntityAliasRepository(self._session).list_alias_index()
        return self.build_resolver(alias_records).resolve(entities)
