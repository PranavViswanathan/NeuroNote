from __future__ import annotations

import hashlib

import pytest

from app.db.engine import get_session_factory
from app.db.repositories.note_repository import NoteRepository
from app.nlp.types import NoteExtractionResult
from app.services.note_processing_service import NoteNotFoundError, NoteProcessingService
from shared.contracts.python.v1.process import ProcessNoteRequest


class _FakePipeline:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    def extract(
        self,
        *,
        note_id: str,
        content_text: str,
        content_hash: str,
    ) -> NoteExtractionResult:
        self.calls.append((note_id, content_text, content_hash))
        return NoteExtractionResult(
            note_id=note_id,
            content_hash=content_hash,
            entities=[],
            keyphrases=[],
            relations=[],
            embedding=[0.0] * 384,
        )


def test_process_note_raises_when_note_is_missing(configured_db: None) -> None:
    pipeline = _FakePipeline()
    service = NoteProcessingService(
        session_factory=get_session_factory(),
        pipeline=pipeline,
    )

    with pytest.raises(NoteNotFoundError):
        service.process_note(
            ProcessNoteRequest(
                note_id="missing-note",
                content_text="text",
                content_hash="hash",
                updated_at="2026-03-07T12:00:00Z",
            )
        )


def test_process_note_uses_latest_persisted_note_snapshot(configured_db: None) -> None:
    note_id = "note-process-1"
    persisted_text = "Machine Learning supports Entity Resolution"
    persisted_hash = hashlib.sha256(persisted_text.encode("utf-8")).hexdigest()

    session_factory = get_session_factory()
    with session_factory() as session:
        repository = NoteRepository(session)
        with session.begin():
            repository.upsert_note(
                note_id=note_id,
                content_json={"type": "doc", "content": []},
                content_text=persisted_text,
                updated_at="2026-03-07T12:01:00Z",
            )

    pipeline = _FakePipeline()
    service = NoteProcessingService(session_factory=session_factory, pipeline=pipeline)
    service.process_note(
        ProcessNoteRequest(
            note_id=note_id,
            content_text="stale payload",
            content_hash="stale-hash",
            updated_at="2026-03-07T12:02:00Z",
        )
    )

    assert pipeline.calls == [(note_id, persisted_text, persisted_hash)]
