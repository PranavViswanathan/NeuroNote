from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.db.models.block import Block
from app.db.engine import get_session_factory
from app.db.repositories.entity_alias_repository import AliasRecord, EntityAliasRepository
from app.db.repositories.note_repository import NoteRepository
from app.nlp.concept_registry import get_known_concepts, register_concepts
from app.nlp.pipeline import NoteNlpPipeline
from app.nlp.resolution.resolver import CanonicalAlias, EntityResolver
from app.nlp.types import BlockTextInput
from app.services.graph_sync_service import (
    CanonicalEntityMapping,
    GraphSyncPayload,
    GraphSyncService,
)
from shared.contracts.python.v1.process import ProcessNoteRequest

_DEFAULT_GRAPH_NAME = "neuronote"


class NoteNotFoundError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ProcessedNoteSnapshot:
    note_id: str
    subject_id: str
    note_title: str
    content_text: str
    content_hash: str
    updated_at: str
    blocks: list[BlockTextInput]


class NoteProcessingService:
    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session] | None = None,
        pipeline: NoteNlpPipeline | None = None,
        graph_name: str = _DEFAULT_GRAPH_NAME,
    ) -> None:
        self._session_factory = session_factory or get_session_factory()
        self._pipeline = pipeline or NoteNlpPipeline()
        self._graph_name = graph_name

    def _load_snapshot(self, note_id: str) -> ProcessedNoteSnapshot:
        with self._session_factory() as session:
            note = NoteRepository(session).get_note(note_id)
            if note is None:
                raise NoteNotFoundError(f"Note {note_id} was not found")
            blocks = session.execute(
                select(Block).where(Block.note_id == note_id).order_by(Block.block_index.asc())
            ).scalars()
            block_inputs = [
                BlockTextInput(
                    block_index=block.block_index,
                    content_text=block.content_text,
                )
                for block in blocks
            ]
            return ProcessedNoteSnapshot(
                note_id=note.note_id,
                subject_id=note.subject_id,
                note_title=note.note_title,
                content_text=note.content_text,
                content_hash=note.content_hash,
                updated_at=note.updated_at,
                blocks=block_inputs,
            )

    def _is_postgres(self, session: Session) -> bool:
        if session.bind is None:
            return False
        return session.bind.dialect.name == "postgresql"

    def _compose_pipeline_text(self, snapshot: ProcessedNoteSnapshot) -> str:
        title = snapshot.note_title.strip()
        body = snapshot.content_text.strip()
        if not title:
            return body
        if not body:
            return title
        return f"{title}\n\n{body}"

    def _load_alias_records(self) -> dict[str, AliasRecord]:
        with self._session_factory() as session:
            return EntityAliasRepository(session).list_alias_index()

    def _build_dictionary_terms(self, alias_records: dict[str, AliasRecord]) -> list[str]:
        terms: list[str] = []
        for alias_text, record in alias_records.items():
            terms.append(alias_text)
            terms.append(record.canonical_name)
        seen: set[str] = set()
        ordered_terms: list[str] = []
        for term in terms:
            normalized = " ".join(term.split()).strip()
            if not normalized:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            ordered_terms.append(normalized)
        return ordered_terms

    def _build_resolver(self, alias_records: dict[str, AliasRecord]) -> EntityResolver:
        alias_index = {
            alias_text: CanonicalAlias(
                canonical_entity_id=record.canonical_entity_id,
                canonical_name=record.canonical_name,
            )
            for alias_text, record in alias_records.items()
        }
        abbreviation_index = {
            alias_text.replace(" ", ""): record.canonical_name
            for alias_text, record in alias_records.items()
            if " " not in alias_text and 1 < len(alias_text) <= 10
        }
        return EntityResolver(
            alias_index=alias_index,
            abbreviation_index=abbreviation_index,
        )

    def _persist_graph_and_vector(self, *, snapshot: ProcessedNoteSnapshot) -> None:
        alias_records = self._load_alias_records()
        # Merge entity-alias terms with all concepts extracted from previous notes.
        # This feeds the SLM its own prior output as "known concepts", closing the
        # normalisation loop: once "machine learning" is extracted once, future calls
        # see it and reuse that exact form instead of producing "ML" or "machine-learning".
        base_terms = self._build_dictionary_terms(alias_records)
        known = get_known_concepts()
        dictionary_terms = base_terms + [c for c in known if c not in set(t.lower() for t in base_terms)]

        result = self._pipeline.extract(
            note_id=snapshot.note_id,
            title=snapshot.note_title,
            content_text=self._compose_pipeline_text(snapshot),
            content_hash=snapshot.content_hash,
            blocks=snapshot.blocks,
            dictionary_terms=dictionary_terms,
        )

        # Register newly extracted concepts so subsequent notes see them.
        if result.entities:
            register_concepts([(e.text, e.entity_id) for e in result.entities if e.label == "concept"])
        resolution_batch = self._build_resolver(alias_records).resolve(result.entities)

        with self._session_factory() as session:
            if not self._is_postgres(session):
                return

            with session.begin():
                resolved_index: dict[str, CanonicalEntityMapping] = {
                    item.source_entity_id: CanonicalEntityMapping(
                        canonical_entity_id=item.canonical_entity_id,
                        canonical_name=item.canonical_name,
                        confidence=float(item.confidence),
                    )
                    for item in resolution_batch.resolved
                }
                GraphSyncService(
                    session=session,
                    graph_name=self._graph_name,
                ).sync_note_graph(
                    GraphSyncPayload(
                        note_id=snapshot.note_id,
                        note_title=snapshot.note_title,
                        subject_id=snapshot.subject_id,
                        content_hash=snapshot.content_hash,
                        updated_at=snapshot.updated_at,
                        entities=result.entities,
                        keyphrases=result.keyphrases,
                        relations=result.relations,
                        resolved_entities=resolved_index,
                        embedding=result.embedding,
                        entity_mentions=result.entity_mentions,
                        note_summary=result.summary,
                    )
                )

    def process_note(self, payload: ProcessNoteRequest) -> None:
        snapshot = self._load_snapshot(payload.note_id)
        self._persist_graph_and_vector(snapshot=snapshot)
