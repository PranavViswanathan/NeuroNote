from __future__ import annotations

from dataclasses import dataclass
import re

from sqlalchemy.orm import Session, sessionmaker

from app.db.engine import get_session_factory
from app.db.repositories.entity_alias_repository import EntityAliasRepository
from app.db.repositories.graph_repository import GraphRepository
from app.db.repositories.note_repository import NoteRepository
from app.nlp.pipeline import NoteNlpPipeline
from app.nlp.resolution.resolver import CanonicalAlias, EntityResolver
from shared.contracts.python.v1.process import ProcessNoteRequest

_DEFAULT_GRAPH_NAME = "neuronote"
_RELATION_TYPE_PATTERN = re.compile(r"[^A-Za-z0-9_]+")


class NoteNotFoundError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ProcessedNoteSnapshot:
    note_id: str
    content_text: str
    content_hash: str


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
            return ProcessedNoteSnapshot(
                note_id=note.note_id,
                content_text=note.content_text,
                content_hash=note.content_hash,
            )

    def _is_postgres(self, session: Session) -> bool:
        if session.bind is None:
            return False
        return session.bind.dialect.name == "postgresql"

    def _normalize_relation_type(self, raw_predicate: str) -> str:
        normalized = _RELATION_TYPE_PATTERN.sub("_", raw_predicate.upper()).strip("_")
        return normalized or "RELATED_TO"

    def _build_resolver(self, repository: EntityAliasRepository) -> EntityResolver:
        alias_records = repository.list_alias_index()
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
        result = self._pipeline.extract(
            note_id=snapshot.note_id,
            content_text=snapshot.content_text,
            content_hash=snapshot.content_hash,
        )

        with self._session_factory() as session:
            if not self._is_postgres(session):
                return

            repository = GraphRepository(session)
            with session.begin():
                alias_repository = EntityAliasRepository(session)
                resolution_batch = self._build_resolver(alias_repository).resolve(result.entities)
                resolved_index = {
                    item.source_entity_id: item
                    for item in resolution_batch.resolved
                }

                for entity in result.entities:
                    resolved = resolved_index.get(entity.entity_id)
                    canonical_id = (
                        resolved.canonical_entity_id if resolved is not None else entity.entity_id
                    )
                    canonical_name = (
                        resolved.canonical_name if resolved is not None else entity.text
                    )
                    canonical_confidence = (
                        max(entity.confidence, resolved.confidence)
                        if resolved is not None
                        else entity.confidence
                    )
                    repository.upsert_node(
                        label="Entity",
                        node_id=canonical_id,
                        properties={
                            "name": canonical_name,
                            "kind": entity.label,
                            "confidence": canonical_confidence,
                            "source_note_id": snapshot.note_id,
                        },
                        graph_name=self._graph_name,
                    )

                for keyphrase in result.keyphrases:
                    repository.upsert_node(
                        label="Concept",
                        node_id=keyphrase.phrase_id,
                        properties={
                            "name": keyphrase.text,
                            "score": keyphrase.score,
                            "source_note_id": snapshot.note_id,
                        },
                        graph_name=self._graph_name,
                    )

                for relation in result.relations:
                    repository.upsert_node(
                        label="Concept",
                        node_id=relation.subject_id,
                        properties={
                            "name": relation.subject_text,
                            "source_note_id": snapshot.note_id,
                        },
                        graph_name=self._graph_name,
                    )
                    repository.upsert_node(
                        label="Concept",
                        node_id=relation.object_id,
                        properties={
                            "name": relation.object_text,
                            "source_note_id": snapshot.note_id,
                        },
                        graph_name=self._graph_name,
                    )
                    repository.upsert_edge(
                        source_id=relation.subject_id,
                        target_id=relation.object_id,
                        relation_type=self._normalize_relation_type(relation.predicate),
                        confidence=relation.confidence,
                        graph_name=self._graph_name,
                    )

                if result.embedding is not None:
                    repository.upsert_embedding(
                        item_id=snapshot.note_id,
                        item_type="note",
                        embedding=result.embedding,
                    )

    def process_note(self, payload: ProcessNoteRequest) -> None:
        snapshot = self._load_snapshot(payload.note_id)
        self._persist_graph_and_vector(snapshot=snapshot)
