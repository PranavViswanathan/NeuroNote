from __future__ import annotations

from app.db.engine import get_session_factory
from app.db.repositories.note_repository import NoteRepository
from app.nlp.types import ExtractedRelation
from app.services import graph_sync_service as graph_sync_module
from app.services.graph_sync_service import GraphSyncPayload, GraphSyncService


def test_graph_sync_collapses_relation_edges_to_related_to(
    configured_db: None,
    monkeypatch,
) -> None:
    session_factory = get_session_factory()
    with session_factory() as session:
        with session.begin():
            NoteRepository(session).upsert_note(
                note_id="sync-note-1",
                note_title="Sync title",
                content_json={
                    "type": "doc",
                    "content": [
                        {"type": "paragraph", "content": [{"type": "text", "text": "A B"}]},
                    ],
                },
                content_text="A B",
                updated_at="2026-03-11T12:10:00Z",
            )

    captured_relation_types: list[str] = []

    class _FakeGraphRepository:
        def __init__(self, _session) -> None:
            return

        def delete_source_artifacts(self, **_kwargs) -> None:
            return

        def upsert_node(self, **_kwargs) -> None:
            return

        def upsert_typed_edge(self, **kwargs) -> None:
            if kwargs["source_label"] == "Concept" and kwargs["target_label"] == "Concept":
                captured_relation_types.append(str(kwargs["relation_type"]))

        def upsert_embedding(self, **_kwargs) -> None:
            return

    monkeypatch.setattr(graph_sync_module, "GraphRepository", _FakeGraphRepository)

    with session_factory() as session:
        with session.begin():
            GraphSyncService(session=session).sync_note_graph(
                GraphSyncPayload(
                    note_id="sync-note-1",
                    note_title="Sync title",
                    subject_id="inbox",
                    content_hash="hash-sync-1",
                    updated_at="2026-03-11T12:10:00Z",
                    entities=[],
                    keyphrases=[],
                    relations=[
                        ExtractedRelation(
                            subject_id="concept-a",
                            subject_text="A",
                            predicate="supports",
                            object_id="concept-b",
                            object_text="B",
                            confidence=0.9,
                        )
                    ],
                    resolved_entities={},
                    embedding=None,
                )
            )

    assert captured_relation_types == ["RELATED_TO"]

