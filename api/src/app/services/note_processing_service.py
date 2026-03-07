from __future__ import annotations

from dataclasses import dataclass
import re

from sqlalchemy.orm import Session, sessionmaker

from app.db.engine import get_session_factory
from app.db.repositories.graph_repository import GraphRepository
from app.db.repositories.note_repository import NoteRepository
from app.nlp.pipeline import NoteNlpPipeline
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
                for entity in result.entities:
                    repository.upsert_node(
                        label="Entity",
                        node_id=entity.entity_id,
                        properties={
                            "name": entity.text,
                            "kind": entity.label,
                            "confidence": entity.confidence,
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
