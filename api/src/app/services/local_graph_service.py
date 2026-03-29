from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.note import Note
from app.nlp.pipeline import NoteNlpPipeline
from shared.contracts.python.v1.graph import LocalGraphResponse
from shared.contracts.python.v1.graph import LocalGraphEdge
from shared.contracts.python.v1.graph import LocalGraphFilters
from shared.contracts.python.v1.graph import LocalGraphMeta
from shared.contracts.python.v1.graph import LocalGraphNode

_VALID_INCLUDE_TYPES = {"note", "entity", "relation"}
_WIKI_LINK_PATTERN = re.compile(r"\[\[([^\[\]]+)\]\]")


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


class LocalGraphNoteNotFoundError(RuntimeError):
    pass


class LocalGraphService:
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
        rows = self._session.execute(
            select(Note.note_id, Note.note_title, Note.content_text).order_by(Note.note_id.asc())
        ).all()
        return [
            _NoteSnapshot(
                note_id=str(row[0]),
                note_title=str(row[1]),
                content_text=str(row[2]),
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

    def _compose_pipeline_text(self, note: _NoteSnapshot) -> str:
        title = note.note_title.strip()
        body = note.content_text.strip()
        if not title:
            return body
        if not body:
            return title
        return f"{title}\n\n{body}"

    def get_local_graph(self, query: LocalGraphQuery) -> LocalGraphResponse:
        include_types = self._normalize_include_types(query.include_types)
        include_type_set = set(include_types)

        notes = self._list_notes()
        notes_by_id = {note.note_id: note for note in notes}
        root_note = notes_by_id.get(query.note_id)
        if root_note is None:
            raise LocalGraphNoteNotFoundError(f"Note {query.note_id} was not found")

        title_index: dict[str, str] = {}
        for note in notes:
            title_index[self._normalize_title(note.note_title)] = note.note_id

        outgoing_links_by_note: dict[str, list[str]] = {}
        for indexed_note in notes:
            outgoing_ids: list[str] = []
            for linked_title in self._extract_wiki_links(indexed_note.content_text):
                target_id = title_index.get(linked_title)
                if target_id is None or target_id == indexed_note.note_id:
                    continue
                outgoing_ids.append(target_id)
            outgoing_links_by_note[indexed_note.note_id] = sorted(set(outgoing_ids))

        incoming_links_by_note: dict[str, list[str]] = {note.note_id: [] for note in notes}
        for source_id, targets in outgoing_links_by_note.items():
            for target_id in targets:
                incoming_links_by_note.setdefault(target_id, []).append(source_id)
        for note_id in incoming_links_by_note:
            incoming_links_by_note[note_id] = sorted(set(incoming_links_by_note[note_id]))

        visited_note_ids: set[str] = {query.note_id}
        frontier: set[str] = {query.note_id}
        edge_map: dict[tuple[str, str, str], LocalGraphEdge] = {}

        def _add_note_link_edge(source_note_id: str, target_note_id: str) -> None:
            if "relation" not in include_type_set:
                return
            key = (source_note_id, target_note_id, "LINKS_TO")
            if key in edge_map:
                return
            edge_map[key] = LocalGraphEdge(
                id=f"{source_note_id}->LINKS_TO->{target_note_id}",
                source=source_note_id,
                target=target_note_id,
                type="LINKS_TO",
                confidence=1.0,
                source_note_id=source_note_id,
            )

        for _depth in range(query.max_hops):
            next_frontier: set[str] = set()
            for note_id in sorted(frontier):
                for target_id in outgoing_links_by_note.get(note_id, []):
                    _add_note_link_edge(note_id, target_id)
                    if target_id not in visited_note_ids:
                        visited_note_ids.add(target_id)
                        next_frontier.add(target_id)

                for source_id in incoming_links_by_note.get(note_id, []):
                    _add_note_link_edge(source_id, note_id)
                    if source_id not in visited_note_ids:
                        visited_note_ids.add(source_id)
                        next_frontier.add(source_id)
            frontier = next_frontier
            if not frontier:
                break

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
                        "content_preview": graph_note.content_text[:140],
                    },
                )

        if "entity" in include_type_set:
            for note_id in sorted(visited_note_ids):
                graph_note = notes_by_id.get(note_id)
                if graph_note is None:
                    continue
                pipeline_text = self._compose_pipeline_text(graph_note)
                content_hash = hashlib.sha256(pipeline_text.encode("utf-8")).hexdigest()
                extraction = self._pipeline.extract(
                    note_id=graph_note.note_id,
                    content_text=pipeline_text,
                    content_hash=content_hash,
                )
                for entity in extraction.entities:
                    if float(entity.confidence) < query.min_confidence:
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

        return LocalGraphResponse(
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
