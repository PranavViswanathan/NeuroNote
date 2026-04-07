from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.block import Block
from app.db.repositories.block_repository import BlockRepository
from app.db.repositories.embedding_repository import EmbeddingRepository
from app.db.repositories.graph_repository import GraphRepository
from app.nlp.types import (
    ExtractedEntity,
    ExtractedEntityMention,
    ExtractedKeyphrase,
    ExtractedRelation,
)


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
    entity_mentions: list[ExtractedEntityMention]
    note_summary: str = ""


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


class GraphSyncService:
    """Synchronises NLP extraction results into the Apache AGE property graph.

    **Algorithm — delete-and-replace:**
    On every call to :meth:`sync`, all AGE nodes and edges whose ``source_note_id``
    matches the note being processed are deleted first.  The full set of nodes and
    edges is then re-created from the current extraction payload.  This guarantees
    idempotency: re-running sync for the same note (e.g. after a schema migration or
    a content edit) always produces a consistent graph state.

    **Graph schema:**

    Nodes
        - ``Note``     — one per note; id = ``note_id``
        - ``Subject``  — one per subject/notebook
        - ``Block``    — one per TipTap block; id = ``{note_id}:block:{block_uid}``
        - ``Entity``   — concept or named entity; id = ``concept-{slug}``
        - ``Keyphrase``— extracted key phrase
        - ``Relation`` — reified relation node when a typed relation is extracted

    Edges
        - ``BELONGS_TO`` — Note → Subject
        - ``CONTAINS``   — Note → Block
        - ``HAS_PARENT`` — Block → Block (tree hierarchy)
        - ``MENTIONS``   — Block → Entity; carries ``mention_text``, ``start_offset``,
                          ``end_offset``, ``source_note_id`` for provenance
        - ``LINKS_TO``   — Note → Note (wiki-link)
        - ``RELATED_TO`` — Note → Entity (keyphrases, resolved entities)
        - ``SUBJECT_OF`` / ``OBJECT_OF`` — for reified Relation nodes
    """

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

    def _block_node_id(self, *, note_id: str, block_uid: str) -> str:
        return f"{note_id}:block:{block_uid}"

    def _upsert_note_and_blocks(
        self,
        *,
        payload: GraphSyncPayload,
        now_iso: str,
    ) -> tuple[list[Block], dict[int, str], dict[str, str]]:
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
        note_props: dict[str, object] = {
            "name": payload.note_title,
            "source_note_id": payload.note_id,
            "content_hash": payload.content_hash,
            "updated_at": payload.updated_at,
            "created_at": now_iso,
        }
        if payload.note_summary:
            note_props["summary"] = payload.note_summary
        self._repository.upsert_node(
            label="Note",
            node_id=payload.note_id,
            properties=note_props,
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
        block_node_ids_by_index: dict[int, str] = {}
        block_node_ids_by_uid: dict[str, str] = {}
        block_node_props: list[dict[str, object]] = []
        for block in blocks:
            block_node_id = self._block_node_id(note_id=payload.note_id, block_uid=block.block_uid)
            block_node_ids_by_index[block.block_index] = block_node_id
            block_node_ids_by_uid[block.block_uid] = block_node_id
            block_node_props.append({
                "id": block_node_id,
                "block_uid": block.block_uid,
                "parent_block_uid": block.parent_block_uid,
                "sibling_order": block.sibling_order,
                "block_index": block.block_index,
                "content_hash": block.content_hash,
                "text": block.content_text,
                "source_note_id": payload.note_id,
                "created_at": now_iso,
                "updated_at": now_iso,
            })
        self._repository.upsert_nodes_batch(
            label="Block",
            nodes=block_node_props,
            graph_name=self._graph_name,
        )

        for block in blocks:
            block_node_id = block_node_ids_by_uid[block.block_uid]
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

            if block.parent_block_uid and block.parent_block_uid in block_node_ids_by_uid:
                parent_node_id = block_node_ids_by_uid[block.parent_block_uid]
                self._repository.upsert_typed_edge(
                    source_label="Block",
                    source_id=parent_node_id,
                    target_label="Block",
                    target_id=block_node_id,
                    relation_type="HAS_CHILD",
                    properties={
                        "source_note_id": payload.note_id,
                        "confidence": 1.0,
                        "created_at": now_iso,
                        "updated_at": now_iso,
                    },
                    graph_name=self._graph_name,
                )

        return blocks, block_node_ids_by_index, block_node_ids_by_uid

    def _upsert_mentions(
        self,
        *,
        blocks: list[Block],
        block_node_ids_by_index: dict[int, str],
        payload: GraphSyncPayload,
        now_iso: str,
    ) -> None:
        entity_by_id = {entity.entity_id: entity for entity in payload.entities}

        # Batch all Concept node upserts into a single AGE UNWIND query
        concept_node_props: list[dict[str, object]] = [
            {
                "id": keyphrase.phrase_id,
                "name": keyphrase.text,
                "score": keyphrase.score,
                "updated_at": now_iso,
            }
            for keyphrase in payload.keyphrases
        ]
        self._repository.upsert_nodes_batch(
            label="Concept",
            nodes=concept_node_props,
            graph_name=self._graph_name,
        )

        for keyphrase in payload.keyphrases:
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
                block_node_id = block_node_ids_by_index.get(block.block_index)
                if block_node_id is None:
                    continue
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

        entity_node_props: list[dict[str, object]] = []
        for entity in payload.entities:
            resolved = payload.resolved_entities.get(entity.entity_id)
            canonical_id = resolved.canonical_entity_id if resolved is not None else entity.entity_id
            canonical_name = resolved.canonical_name if resolved is not None else entity.text
            entity_node_props.append({
                "id": canonical_id,
                "name": canonical_name,
                "kind": entity.label,
                "updated_at": now_iso,
            })
        self._repository.upsert_nodes_batch(
            label="Entity",
            nodes=entity_node_props,
            graph_name=self._graph_name,
        )

        seen_mentions: set[tuple[str, str, int, int]] = set()
        for mention in payload.entity_mentions:
            mention_block_node_id = block_node_ids_by_index.get(mention.block_index)
            if mention_block_node_id is None:
                continue
            source_entity = entity_by_id.get(mention.entity_id)
            if source_entity is None:
                continue

            resolved = payload.resolved_entities.get(source_entity.entity_id)
            canonical_id = resolved.canonical_entity_id if resolved is not None else source_entity.entity_id
            mention_key = (
                mention_block_node_id,
                canonical_id,
                mention.start_offset,
                mention.end_offset,
            )
            if mention_key in seen_mentions:
                continue
            seen_mentions.add(mention_key)

            mention_confidence = (
                max(float(source_entity.confidence), float(resolved.confidence))
                if resolved is not None
                else float(source_entity.confidence)
            )
            mention_confidence = max(mention_confidence, float(mention.confidence))
            self._repository.upsert_typed_edge(
                source_label="Block",
                source_id=mention_block_node_id,
                target_label="Entity",
                target_id=canonical_id,
                relation_type="MENTIONS",
                properties={
                    "source_note_id": payload.note_id,
                    "confidence": mention_confidence,
                    "mention_text": mention.mention_text,
                    "start_offset": int(mention.start_offset),
                    "end_offset": int(mention.end_offset),
                    "created_at": now_iso,
                    "updated_at": now_iso,
                },
                graph_name=self._graph_name,
            )

        # Aggregate block-level mentions to Note→Entity edges (max confidence per entity).
        # This stores confidence directly on Note→Entity in AGE so future graph queries
        # can read it without re-running NLP.
        note_entity_max_conf: dict[str, float] = {}
        for mention in payload.entity_mentions:
            source_entity = entity_by_id.get(mention.entity_id)
            if source_entity is None:
                continue
            resolved = payload.resolved_entities.get(source_entity.entity_id)
            canonical_id = resolved.canonical_entity_id if resolved is not None else source_entity.entity_id
            conf = float(source_entity.confidence)
            if resolved is not None:
                conf = max(conf, float(resolved.confidence))
            conf = max(conf, float(mention.confidence))
            if canonical_id not in note_entity_max_conf or conf > note_entity_max_conf[canonical_id]:
                note_entity_max_conf[canonical_id] = conf

        for canonical_id, best_conf in note_entity_max_conf.items():
            self._repository.upsert_typed_edge(
                source_label="Note",
                source_id=payload.note_id,
                target_label="Entity",
                target_id=canonical_id,
                relation_type="MENTIONS",
                properties={
                    "source_note_id": payload.note_id,
                    "confidence": best_conf,
                    "created_at": now_iso,
                    "updated_at": now_iso,
                },
                graph_name=self._graph_name,
            )

    def _upsert_block_refs(
        self,
        *,
        blocks: list[Block],
        block_node_ids_by_uid: dict[str, str],
        payload: GraphSyncPayload,
        now_iso: str,
    ) -> None:
        block_repository = BlockRepository(self._session)
        ref_uids: set[str] = set()
        refs_by_source_uid: dict[str, list[str]] = {}

        for block in blocks:
            refs = block_repository.extract_block_refs_from_rich_content(dict(block.rich_content))
            if not refs:
                refs = block_repository.extract_block_refs(block.content_text)
            refs_by_source_uid[block.block_uid] = refs
            ref_uids.update(refs)

        if not ref_uids:
            return

        target_rows = block_repository.get_blocks_by_uid(list(ref_uids))
        target_node_ids = {
            row.block_uid: self._block_node_id(note_id=row.note_id, block_uid=row.block_uid)
            for row in target_rows
        }

        emitted_pairs: set[tuple[str, str]] = set()
        for source_block in blocks:
            source_node_id = block_node_ids_by_uid.get(source_block.block_uid)
            if source_node_id is None:
                continue
            for target_uid in refs_by_source_uid.get(source_block.block_uid, []):
                target_node_id = target_node_ids.get(target_uid)
                if target_node_id is None:
                    continue
                if source_node_id == target_node_id:
                    continue
                pair = (source_node_id, target_node_id)
                if pair in emitted_pairs:
                    continue
                emitted_pairs.add(pair)
                self._repository.upsert_typed_edge(
                    source_label="Block",
                    source_id=source_node_id,
                    target_label="Block",
                    target_id=target_node_id,
                    relation_type="REFERS_TO",
                    properties={
                        "source_note_id": payload.note_id,
                        "confidence": 1.0,
                        "created_at": now_iso,
                        "updated_at": now_iso,
                    },
                    graph_name=self._graph_name,
                )

    def _upsert_relations(self, *, payload: GraphSyncPayload, now_iso: str) -> None:
        _TYPED_RELATIONS = frozenset(
            {"IS_A", "PART_OF", "CAUSES", "CONTRASTS_WITH", "USES", "PRODUCES", "RELATED_TO"}
        )
        for relation in payload.relations:
            self._repository.upsert_node(
                label="Concept",
                node_id=relation.subject_id,
                properties={
                    "name": relation.subject_text,
                    "canonical_form": relation.subject_text,
                    "updated_at": now_iso,
                },
                graph_name=self._graph_name,
            )
            self._repository.upsert_node(
                label="Concept",
                node_id=relation.object_id,
                properties={
                    "name": relation.object_text,
                    "canonical_form": relation.object_text,
                    "updated_at": now_iso,
                },
                graph_name=self._graph_name,
            )
            edge_type = relation.predicate if relation.predicate in _TYPED_RELATIONS else "RELATED_TO"
            self._repository.upsert_typed_edge(
                source_label="Concept",
                source_id=relation.subject_id,
                target_label="Concept",
                target_id=relation.object_id,
                relation_type=edge_type,
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
        blocks, block_node_ids_by_index, block_node_ids_by_uid = self._upsert_note_and_blocks(
            payload=payload,
            now_iso=now_iso,
        )
        self._upsert_mentions(
            blocks=blocks,
            block_node_ids_by_index=block_node_ids_by_index,
            payload=payload,
            now_iso=now_iso,
        )
        self._upsert_block_refs(
            blocks=blocks,
            block_node_ids_by_uid=block_node_ids_by_uid,
            payload=payload,
            now_iso=now_iso,
        )
        self._upsert_relations(payload=payload, now_iso=now_iso)

        if payload.embedding is not None:
            EmbeddingRepository(self._session).upsert_embedding(
                item_id=payload.note_id,
                item_type="note",
                embedding=payload.embedding,
            )
