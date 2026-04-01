from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.block import Block
from app.db.models.note import Note
from app.db.repositories.entity_alias_repository import EntityAliasRepository
from app.nlp.pipeline import NoteNlpPipeline
from app.nlp.types import BlockTextInput
from shared.contracts.python.v1.graph import GlobalGraphFilters
from shared.contracts.python.v1.graph import GlobalGraphMeta
from shared.contracts.python.v1.graph import GlobalGraphResponse
from shared.contracts.python.v1.graph import LocalGraphEdge
from shared.contracts.python.v1.graph import LocalGraphNode

_VALID_INCLUDE_TYPES = {"note", "entity", "relation"}
_WIKI_LINK_PATTERN = re.compile(r"\[\[([^\[\]]+)\]\]")


@dataclass(frozen=True, slots=True)
class GlobalGraphQuery:
    limit_nodes: int
    min_confidence: float
    include_types: list[str]


@dataclass(frozen=True, slots=True)
class _NoteSnapshot:
    note_id: str
    note_title: str
    content_text: str
    blocks: list[BlockTextInput]


class GlobalGraphService:
    def __init__(self, session: Session, *, pipeline: NoteNlpPipeline | None = None) -> None:
        self._session = session
        self._pipeline = pipeline or NoteNlpPipeline()

    def _normalize_title(self, value: str) -> str:
        return " ".join(value.split()).strip().lower()

    def _normalize_entity_key(self, value: str) -> str:
        cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return cleaned or "unknown"

    def _normalize_include_types(self, values: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for item in values:
            cleaned = item.strip().lower()
            if cleaned not in _VALID_INCLUDE_TYPES or cleaned in seen:
                continue
            seen.add(cleaned)
            normalized.append(cleaned)
        if not normalized:
            return ["note", "entity", "relation"]
        return normalized

    def _list_notes(self) -> list[_NoteSnapshot]:
        block_rows = self._session.execute(
            select(Block.note_id, Block.block_index, Block.content_text).order_by(
                Block.note_id.asc(),
                Block.block_index.asc(),
            )
        ).all()
        blocks_by_note_id: dict[str, list[BlockTextInput]] = {}
        for row in block_rows:
            blocks_by_note_id.setdefault(str(row[0]), []).append(
                BlockTextInput(
                    block_index=int(row[1]),
                    content_text=str(row[2]),
                )
            )

        rows = self._session.execute(
            select(Note.note_id, Note.note_title, Note.content_text).order_by(Note.note_id.asc())
        ).all()
        return [
            _NoteSnapshot(
                note_id=str(row[0]),
                note_title=str(row[1]),
                content_text=str(row[2]),
                blocks=list(blocks_by_note_id.get(str(row[0]), [])),
            )
            for row in rows
        ]

    def _extract_wiki_links(self, content_text: str) -> list[str]:
        links: list[str] = []
        seen: set[str] = set()
        for match in _WIKI_LINK_PATTERN.finditer(content_text):
            normalized = self._normalize_title(match.group(1))
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            links.append(normalized)
        return links

    def _build_dictionary_terms(self) -> list[str]:
        alias_records = EntityAliasRepository(self._session).list_alias_index()
        terms: list[str] = []
        seen: set[str] = set()
        for alias_text, record in alias_records.items():
            for term in (alias_text, record.canonical_name):
                normalized = " ".join(term.split()).strip()
                if not normalized:
                    continue
                key = normalized.lower()
                if key in seen:
                    continue
                seen.add(key)
                terms.append(normalized)
        return terms

    def _entity_is_note_noise(
        self,
        *,
        entity_label: str,
        note: _NoteSnapshot,
        linked_note_titles: set[str],
    ) -> bool:
        normalized_label = self._normalize_title(entity_label)
        if not normalized_label:
            return True
        if normalized_label == self._normalize_title(note.note_title):
            return True
        if normalized_label in linked_note_titles:
            return True
        return False

    def get_global_graph(self, query: GlobalGraphQuery) -> GlobalGraphResponse:
        include_types = self._normalize_include_types(query.include_types)
        include_type_set = set(include_types)

        notes = self._list_notes()
        dictionary_terms = self._build_dictionary_terms()
        total_notes = len(notes)

        title_index: dict[str, str] = {}
        for note in notes:
            title_index[self._normalize_title(note.note_title)] = note.note_id

        node_map: dict[str, LocalGraphNode] = {}
        edge_map: dict[tuple[str, str, str], LocalGraphEdge] = {}

        # Build LINKS_TO edges for all notes
        for note in notes:
            if "note" in include_type_set:
                node_map[note.note_id] = LocalGraphNode(
                    id=note.note_id,
                    type="note",
                    label=note.note_title,
                    confidence=None,
                    source_note_id=note.note_id,
                    metadata={
                        "note_id": note.note_id,
                        "content_preview": note.content_text[:140],
                    },
                )

            if "relation" in include_type_set:
                for linked_title in self._extract_wiki_links(note.content_text):
                    target_id = title_index.get(linked_title)
                    if target_id is None or target_id == note.note_id:
                        continue
                    key = (note.note_id, target_id, "LINKS_TO")
                    if key in edge_map:
                        continue
                    edge_map[key] = LocalGraphEdge(
                        id=f"{note.note_id}->LINKS_TO->{target_id}",
                        source=note.note_id,
                        target=target_id,
                        type="LINKS_TO",
                        confidence=1.0,
                        source_note_id=note.note_id,
                    )

        # Run entity extraction for all notes
        if "entity" in include_type_set:
            for note in notes:
                linked_note_titles = {
                    linked_title
                    for linked_title in self._extract_wiki_links(note.content_text)
                    if linked_title
                }
                pipeline_text = note.content_text.strip()
                extraction_blocks = note.blocks or [
                    BlockTextInput(block_index=0, content_text=note.content_text)
                ]
                if not pipeline_text:
                    pipeline_text = "\n\n".join(
                        block.content_text.strip()
                        for block in extraction_blocks
                        if block.content_text.strip()
                    )
                if not pipeline_text:
                    continue
                content_hash = hashlib.sha256(pipeline_text.encode("utf-8")).hexdigest()
                extraction = self._pipeline.extract(
                    note_id=note.note_id,
                    content_text=pipeline_text,
                    content_hash=content_hash,
                    blocks=extraction_blocks,
                    dictionary_terms=dictionary_terms,
                )
                for entity in extraction.entities:
                    if float(entity.confidence) < query.min_confidence:
                        continue
                    if self._entity_is_note_noise(
                        entity_label=entity.text,
                        note=note,
                        linked_note_titles=linked_note_titles,
                    ):
                        continue
                    entity_key = self._normalize_entity_key(entity.text)
                    entity_id = f"entity:{entity_key}"
                    if entity_id not in node_map:
                        node_map[entity_id] = LocalGraphNode(
                            id=entity_id,
                            type="entity",
                            label=entity.text,
                            confidence=float(entity.confidence),
                            source_note_id=note.note_id,
                            metadata={
                                "entity_id": entity.entity_id,
                                "entity_label": entity.label,
                            },
                        )
                    if "relation" not in include_type_set:
                        continue
                    mention_edge_key = (note.note_id, entity_id, "MENTIONS")
                    if mention_edge_key in edge_map:
                        continue
                    edge_map[mention_edge_key] = LocalGraphEdge(
                        id=f"{note.note_id}->MENTIONS->{entity_id}",
                        source=note.note_id,
                        target=entity_id,
                        type="MENTIONS",
                        confidence=float(entity.confidence),
                        source_note_id=note.note_id,
                    )

        nodes = sorted(node_map.values(), key=lambda item: (item.type, item.id))
        truncated = len(nodes) > query.limit_nodes

        if truncated:
            kept_ids = [node.id for node in nodes[: query.limit_nodes]]
            kept_id_set = set(kept_ids)
            nodes = [node_map[node_id] for node_id in kept_ids if node_id in node_map]
        else:
            kept_id_set = {node.id for node in nodes}

        edges = sorted(
            (
                edge
                for edge in edge_map.values()
                if edge.source in kept_id_set and edge.target in kept_id_set
            ),
            key=lambda item: (item.type, item.source, item.target, item.id),
        )

        return GlobalGraphResponse(
            nodes=nodes,
            edges=edges,
            meta=GlobalGraphMeta(
                total_notes=total_notes,
                applied_filters=GlobalGraphFilters(
                    limit_nodes=query.limit_nodes,
                    min_confidence=query.min_confidence,
                    include_types=include_types,
                ),
                truncated=truncated,
            ),
        )
