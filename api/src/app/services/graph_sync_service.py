from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.block import Block
from app.db.repositories.graph_repository import GraphRepository
from app.nlp.types import ExtractedEntity, ExtractedKeyphrase, ExtractedRelation


@dataclass(frozen=True, slots=True)
class CanonicalEntityMapping:
    canonical_entity_id: str
    canonical_name: str
    confidence: float


@dataclass(frozen=True, slots=True)
class GraphSyncPayload:
    note_id: str
    note_title: str
    subject_id: str
    content_hash: str
    updated_at: str
    entities: list[ExtractedEntity]
    keyphrases: list[ExtractedKeyphrase]
    relations: list[ExtractedRelation]
    resolved_entities: dict[str, CanonicalEntityMapping]
    embedding: list[float] | None


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


class GraphSyncService:
    def __init__(
        self,
        *,
        session: Session,
        graph_name: str = "neuronote",
    ) -> None:
        self._session = session
        self._repository = GraphRepository(session)
        self._graph_name = graph_name

    def _iter_blocks(self, note_id: str) -> list[Block]:
        return list(
            self._session.execute(
                select(Block)
                .where(Block.note_id == note_id)
                .order_by(Block.block_index.asc()),
            ).scalars()
        )

    def _upsert_note_and_blocks(self, *, payload: GraphSyncPayload, now_iso: str) -> list[Block]:
        self._repository.delete_source_artifacts(
            source_note_id=payload.note_id,
            graph_name=self._graph_name,
        )
        self._repository.upsert_node(
            label="Subject",
            node_id=payload.subject_id,
            properties={
                "name": payload.subject_id,
                "updated_at": now_iso,
            },
            graph_name=self._graph_name,
        )
        self._repository.upsert_node(
            label="Note",
            node_id=payload.note_id,
            properties={
                "name": payload.note_title,
                "source_note_id": payload.note_id,
                "content_hash": payload.content_hash,
                "updated_at": payload.updated_at,
                "created_at": now_iso,
            },
            graph_name=self._graph_name,
        )
        self._repository.upsert_typed_edge(
            source_label="Note",
            source_id=payload.note_id,
            target_label="Subject",
            target_id=payload.subject_id,
            relation_type="BELONGS_TO",
            properties={
                "source_note_id": payload.note_id,
                "confidence": 1.0,
                "created_at": now_iso,
                "updated_at": now_iso,
            },
            graph_name=self._graph_name,
        )

        blocks = self._iter_blocks(payload.note_id)
        for block in blocks:
            block_node_id = f"{payload.note_id}:block:{block.block_index}"
            self._repository.upsert_node(
                label="Block",
                node_id=block_node_id,
                properties={
                    "block_index": block.block_index,
                    "content_hash": block.content_hash,
                    "text": block.content_text,
                    "source_note_id": payload.note_id,
                    "created_at": now_iso,
                    "updated_at": now_iso,
                },
                graph_name=self._graph_name,
            )
            self._repository.upsert_typed_edge(
                source_label="Note",
                source_id=payload.note_id,
                target_label="Block",
                target_id=block_node_id,
                relation_type="CONTAINS",
                properties={
                    "source_note_id": payload.note_id,
                    "confidence": 1.0,
                    "created_at": now_iso,
                    "updated_at": now_iso,
                },
                graph_name=self._graph_name,
            )

        return blocks

    def _upsert_mentions(
        self,
        *,
        blocks: list[Block],
        payload: GraphSyncPayload,
        now_iso: str,
    ) -> None:
        for keyphrase in payload.keyphrases:
            self._repository.upsert_node(
                label="Concept",
                node_id=keyphrase.phrase_id,
                properties={
                    "name": keyphrase.text,
                    "score": keyphrase.score,
                    "updated_at": now_iso,
                },
                graph_name=self._graph_name,
            )
            self._repository.upsert_typed_edge(
                source_label="Concept",
                source_id=keyphrase.phrase_id,
                target_label="Subject",
                target_id=payload.subject_id,
                relation_type="APPEARS_IN",
                properties={
                    "source_note_id": payload.note_id,
                    "confidence": float(keyphrase.score),
                    "created_at": now_iso,
                    "updated_at": now_iso,
                },
                graph_name=self._graph_name,
            )
            for block in blocks:
                if keyphrase.text.lower() not in block.content_text.lower():
                    continue
                block_node_id = f"{payload.note_id}:block:{block.block_index}"
                self._repository.upsert_typed_edge(
                    source_label="Block",
                    source_id=block_node_id,
                    target_label="Concept",
                    target_id=keyphrase.phrase_id,
                    relation_type="MENTIONS",
                    properties={
                        "source_note_id": payload.note_id,
                        "confidence": float(keyphrase.score),
                        "created_at": now_iso,
                        "updated_at": now_iso,
                    },
                    graph_name=self._graph_name,
                )

        for entity in payload.entities:
            resolved = payload.resolved_entities.get(entity.entity_id)
            canonical_id = resolved.canonical_entity_id if resolved is not None else entity.entity_id
            canonical_name = resolved.canonical_name if resolved is not None else entity.text
            confidence = (
                max(float(entity.confidence), float(resolved.confidence))
                if resolved is not None
                else float(entity.confidence)
            )
            self._repository.upsert_node(
                label="Entity",
                node_id=canonical_id,
                properties={
                    "name": canonical_name,
                    "kind": entity.label,
                    "updated_at": now_iso,
                },
                graph_name=self._graph_name,
            )
            for block in blocks:
                if entity.text.lower() not in block.content_text.lower():
                    continue
                block_node_id = f"{payload.note_id}:block:{block.block_index}"
                self._repository.upsert_typed_edge(
                    source_label="Block",
                    source_id=block_node_id,
                    target_label="Entity",
                    target_id=canonical_id,
                    relation_type="MENTIONS",
                    properties={
                        "source_note_id": payload.note_id,
                        "confidence": confidence,
                        "created_at": now_iso,
                        "updated_at": now_iso,
                    },
                    graph_name=self._graph_name,
                )

    def _upsert_relations(self, *, payload: GraphSyncPayload, now_iso: str) -> None:
        for relation in payload.relations:
            self._repository.upsert_node(
                label="Concept",
                node_id=relation.subject_id,
                properties={
                    "name": relation.subject_text,
                    "updated_at": now_iso,
                },
                graph_name=self._graph_name,
            )
            self._repository.upsert_node(
                label="Concept",
                node_id=relation.object_id,
                properties={
                    "name": relation.object_text,
                    "updated_at": now_iso,
                },
                graph_name=self._graph_name,
            )
            self._repository.upsert_typed_edge(
                source_label="Concept",
                source_id=relation.subject_id,
                target_label="Concept",
                target_id=relation.object_id,
                relation_type="RELATED_TO",
                properties={
                    "source_note_id": payload.note_id,
                    "confidence": float(relation.confidence),
                    "predicate": relation.predicate,
                    "created_at": now_iso,
                    "updated_at": now_iso,
                },
                graph_name=self._graph_name,
            )
            self._repository.upsert_typed_edge(
                source_label="Concept",
                source_id=relation.subject_id,
                target_label="Subject",
                target_id=payload.subject_id,
                relation_type="APPEARS_IN",
                properties={
                    "source_note_id": payload.note_id,
                    "confidence": float(relation.confidence),
                    "created_at": now_iso,
                    "updated_at": now_iso,
                },
                graph_name=self._graph_name,
            )
            self._repository.upsert_typed_edge(
                source_label="Concept",
                source_id=relation.object_id,
                target_label="Subject",
                target_id=payload.subject_id,
                relation_type="APPEARS_IN",
                properties={
                    "source_note_id": payload.note_id,
                    "confidence": float(relation.confidence),
                    "created_at": now_iso,
                    "updated_at": now_iso,
                },
                graph_name=self._graph_name,
            )

    def sync_note_graph(self, payload: GraphSyncPayload) -> None:
        now_iso = _utc_now_iso()
        blocks = self._upsert_note_and_blocks(payload=payload, now_iso=now_iso)
        self._upsert_mentions(blocks=blocks, payload=payload, now_iso=now_iso)
        self._upsert_relations(payload=payload, now_iso=now_iso)

        if payload.embedding is not None:
            self._repository.upsert_embedding(
                item_id=payload.note_id,
                item_type="note",
                embedding=payload.embedding,
            )

