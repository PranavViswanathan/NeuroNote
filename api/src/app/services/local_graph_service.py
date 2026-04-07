from __future__ import annotations

from dataclasses import dataclass
import hashlib

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.graph_cache import get_cached, get_note_version, set_cached
from app.db.models.block import Block
from app.db.models.note import Note
from app.db.repositories.entity_alias_repository import EntityAliasRepository
from app.nlp.pipeline import NoteNlpPipeline
from app.nlp.types import BlockTextInput
from app.utils.text import (
    extract_wiki_link_titles,
    normalize_entity_key,
    normalize_include_types,
    normalize_title_key,
)
from shared.contracts.python.v1.graph import LocalGraphResponse
from shared.contracts.python.v1.graph import LocalGraphEdge
from shared.contracts.python.v1.graph import LocalGraphFilters
from shared.contracts.python.v1.graph import LocalGraphMeta
from shared.contracts.python.v1.graph import LocalGraphNode


@dataclass(frozen=True, slots=True)
class LocalGraphQuery:
    note_id: str
    max_hops: int
    limit_nodes: int
    min_confidence: float
    include_types: list[str]


@dataclass(frozen=True, slots=True)
class _NoteSnapshot:
    note_id: str
    note_title: str
    content_text: str
    subject_id: str
    blocks: list[BlockTextInput]


class LocalGraphNoteNotFoundError(RuntimeError):
    pass


class LocalGraphService:
    def __init__(self, session: Session, *, pipeline: NoteNlpPipeline | None = None) -> None:
        self._session = session
        self._pipeline = pipeline or NoteNlpPipeline()

    @staticmethod
    def _normalize_title(value: str) -> str:
        return normalize_title_key(value)

    @staticmethod
    def _normalize_entity_key(value: str) -> str:
        return normalize_entity_key(value)

    @staticmethod
    def _normalize_include_types(values: list[str]) -> list[str]:
        return normalize_include_types(values)

    def _fetch_reachable_notes(self, seed_id: str, max_hops: int) -> list[_NoteSnapshot]:
        """Load only notes reachable from seed_id within max_hops via wiki-links.

        Outgoing links are resolved with a targeted SQL fetch by normalized title.
        Incoming links (notes that link TO a frontier note) are found with a
        per-hop ILIKE scan — still O(n) for incoming, but blocks are never loaded
        for notes outside the reachable set.
        """
        # note_id -> (note_title, content_text, subject_id)
        visited: dict[str, tuple[str, str, str]] = {}

        seed_row = self._session.execute(
            select(Note.note_id, Note.note_title, Note.content_text, Note.subject_id)
            .where(Note.note_id == seed_id)
        ).first()
        if seed_row is None:
            return []

        visited[str(seed_row[0])] = (str(seed_row[1]), str(seed_row[2]), str(seed_row[3]) if seed_row[3] else "inbox")
        frontier_ids: set[str] = {str(seed_row[0])}

        for _hop in range(max_hops):
            if not frontier_ids:
                break

            # --- outgoing: SQL fetch by wiki-link title match ---
            outgoing_titles: set[str] = set()
            for fid in frontier_ids:
                _, content, _ = visited[fid]
                for t in self._extract_wiki_links(content):
                    outgoing_titles.add(t)

            new_ids: set[str] = set()
            if outgoing_titles:
                out_rows = self._session.execute(
                    select(Note.note_id, Note.note_title, Note.content_text, Note.subject_id)
                    .where(func.lower(Note.note_title).in_(list(outgoing_titles)))
                    .where(Note.note_id.not_in(list(visited.keys())))
                ).all()
                for r in out_rows:
                    nid = str(r[0])
                    visited[nid] = (str(r[1]), str(r[2]), str(r[3]) if r[3] else "inbox")
                    new_ids.add(nid)

            # --- incoming: ILIKE scan for notes linking TO frontier notes ---
            frontier_titles = [self._normalize_title(visited[fid][0]) for fid in frontier_ids]
            if frontier_titles:
                like_clauses = [
                    Note.content_text.ilike(f"%[[{t}]]%") for t in frontier_titles
                ]
                in_rows = self._session.execute(
                    select(Note.note_id, Note.note_title, Note.content_text, Note.subject_id)
                    .where(or_(*like_clauses))
                    .where(Note.note_id.not_in(list(visited.keys())))
                ).all()
                for r in in_rows:
                    nid = str(r[0])
                    visited[nid] = (str(r[1]), str(r[2]), str(r[3]) if r[3] else "inbox")
                    new_ids.add(nid)

            frontier_ids = new_ids

        # Load blocks only for the reachable notes
        visited_ids = list(visited.keys())
        block_rows = self._session.execute(
            select(Block.note_id, Block.block_index, Block.content_text)
            .where(Block.note_id.in_(visited_ids))
            .order_by(Block.note_id.asc(), Block.block_index.asc())
        ).all()
        blocks_by_note_id: dict[str, list[BlockTextInput]] = {}
        for r in block_rows:  # type: ignore[assignment]
            blocks_by_note_id.setdefault(str(r[0]), []).append(
                BlockTextInput(block_index=int(r[1]), content_text=str(r[2]))
            )

        return [
            _NoteSnapshot(
                note_id=nid,
                note_title=title,
                content_text=content,
                subject_id=subject_id,
                blocks=blocks_by_note_id.get(nid, []),
            )
            for nid, (title, content, subject_id) in visited.items()
        ]

    @staticmethod
    def _extract_wiki_links(content_text: str) -> list[str]:
        return extract_wiki_link_titles(content_text)

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

    def get_local_graph(self, query: LocalGraphQuery) -> LocalGraphResponse:
        include_types = self._normalize_include_types(query.include_types)

        note_version = get_note_version(self._session, query.note_id)
        cache_key = (
            f"local:{query.note_id}:{query.max_hops}:{query.min_confidence}"
            f":{query.limit_nodes}:{'|'.join(sorted(include_types))}:{note_version}"
        )
        cached = get_cached(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]

        include_type_set = set(include_types)

        notes = self._fetch_reachable_notes(query.note_id, query.max_hops)
        dictionary_terms = self._build_dictionary_terms()
        notes_by_id = {note.note_id: note for note in notes}
        if query.note_id not in notes_by_id:
            raise LocalGraphNoteNotFoundError(f"Note {query.note_id} was not found")

        # Title index is built only from reachable notes; links to out-of-scope
        # notes simply won't resolve, which is the correct behaviour.
        title_index: dict[str, str] = {
            self._normalize_title(note.note_title): note.note_id for note in notes
        }
        visited_note_ids: set[str] = set(notes_by_id.keys())

        # Build LINKS_TO edges from the reachable set
        edge_map: dict[tuple[str, str, str], LocalGraphEdge] = {}
        if "relation" in include_type_set:
            for note in notes:
                for linked_title in self._extract_wiki_links(note.content_text):
                    target_id = title_index.get(linked_title)
                    if target_id is None or target_id == note.note_id:
                        continue
                    key = (note.note_id, target_id, "LINKS_TO")
                    if key not in edge_map:
                        edge_map[key] = LocalGraphEdge(
                            id=f"{note.note_id}->LINKS_TO->{target_id}",
                            source=note.note_id,
                            target=target_id,
                            type="LINKS_TO",
                            confidence=1.0,
                            source_note_id=note.note_id,
                        )

        node_map: dict[str, LocalGraphNode] = {}
        if "note" in include_type_set:
            for note_id in sorted(visited_note_ids):
                graph_note = notes_by_id.get(note_id)
                if graph_note is None:
                    continue
                node_map[note_id] = LocalGraphNode(
                    id=graph_note.note_id,
                    type="note",
                    label=graph_note.note_title,
                    confidence=None,
                    source_note_id=graph_note.note_id,
                    metadata={
                        "note_id": graph_note.note_id,
                        "subject_id": graph_note.subject_id,
                        "content_preview": graph_note.content_text[:140],
                    },
                )

        if "entity" in include_type_set:
            for note_id in sorted(visited_note_ids):
                graph_note = notes_by_id.get(note_id)
                if graph_note is None:
                    continue
                linked_note_titles = {
                    linked_title
                    for linked_title in self._extract_wiki_links(graph_note.content_text)
                    if linked_title
                }
                pipeline_text = graph_note.content_text.strip()
                extraction_blocks = graph_note.blocks or [
                    BlockTextInput(block_index=0, content_text=graph_note.content_text)
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
                    note_id=graph_note.note_id,
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
                        note=graph_note,
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
                            source_note_id=graph_note.note_id,
                            metadata={
                                "entity_id": entity.entity_id,
                                "entity_label": entity.label,
                            },
                        )
                    if "relation" not in include_type_set:
                        continue
                    mention_edge_key = (graph_note.note_id, entity_id, "MENTIONS")
                    if mention_edge_key in edge_map:
                        continue
                    edge_map[mention_edge_key] = LocalGraphEdge(
                        id=f"{graph_note.note_id}->MENTIONS->{entity_id}",
                        source=graph_note.note_id,
                        target=entity_id,
                        type="MENTIONS",
                        confidence=float(entity.confidence),
                        source_note_id=graph_note.note_id,
                    )

        nodes = sorted(node_map.values(), key=lambda item: (item.type, item.id))
        truncated = len(nodes) > query.limit_nodes

        if truncated:
            kept_ids = [node.id for node in nodes[: query.limit_nodes]]
            if query.note_id in node_map and query.note_id not in kept_ids:
                kept_ids = [query.note_id, *kept_ids[:-1]]
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

        response = LocalGraphResponse(
            nodes=nodes,
            edges=edges,
            meta=LocalGraphMeta(
                root_note_id=query.note_id,
                applied_filters=LocalGraphFilters(
                    max_hops=query.max_hops,
                    limit_nodes=query.limit_nodes,
                    min_confidence=query.min_confidence,
                    include_types=include_types,
                ),
                truncated=truncated,
            ),
        )
        set_cached(cache_key, response)
        return response
