from __future__ import annotations

import time

import pytest
from sqlalchemy.orm import Session

from app.db.models.note import Note
from app.db.repositories.note_repository import NoteRepository


def test_upsert_note_increments_version(db_session: Session) -> None:
    repository = NoteRepository(db_session)

    with db_session.begin():
        first = repository.upsert_note(
            note_id="note-repo-1",
            content_json={"type": "doc", "content": []},
            content_text="First",
            updated_at="2026-03-01T12:00:00Z",
        )

    with db_session.begin():
        second = repository.upsert_note(
            note_id="note-repo-1",
            content_json={"type": "doc", "content": [{"type": "paragraph"}]},
            content_text="Second",
            updated_at="2026-03-01T12:01:00Z",
        )

    assert first.version == 1
    assert second.version == 2


def test_get_note_returns_latest_record(db_session: Session) -> None:
    repository = NoteRepository(db_session)

    with db_session.begin():
        repository.upsert_note(
            note_id="note-repo-2",
            content_json={"type": "doc", "content": []},
            content_text="Stored value",
            updated_at="2026-03-01T12:00:00Z",
        )

    result = repository.get_note("note-repo-2")
    assert result is not None
    assert result.content_text == "Stored value"
    assert result.version == 1


def test_transaction_rollback_undoes_note_write(db_session: Session) -> None:
    repository = NoteRepository(db_session)

    with pytest.raises(RuntimeError):
        with db_session.begin():
            repository.upsert_note(
                note_id="note-rollback",
                content_json={"type": "doc", "content": []},
                content_text="Should rollback",
                updated_at="2026-03-01T12:00:00Z",
            )
            raise RuntimeError("force rollback")

    assert repository.get_note("note-rollback") is None


def test_list_notes_returns_total_and_respects_pagination(db_session: Session) -> None:
    repository = NoteRepository(db_session)

    with db_session.begin():
        repository.upsert_note(
            note_id="note-list-a",
            content_json={"type": "doc", "content": []},
            content_text="A",
            updated_at="2026-03-01T12:00:00Z",
        )
        repository.upsert_note(
            note_id="note-list-b",
            content_json={"type": "doc", "content": []},
            content_text="B",
            updated_at="2026-03-01T12:01:00Z",
        )

    items, total = repository.list_notes(limit=1, offset=0)
    assert total == 2
    assert len(items) == 1


def test_delete_note_returns_true_when_deleted(db_session: Session) -> None:
    repository = NoteRepository(db_session)

    with db_session.begin():
        repository.upsert_note(
            note_id="note-delete-repo",
            content_json={"type": "doc", "content": []},
            content_text="To delete",
            updated_at="2026-03-01T12:00:00Z",
        )

    with db_session.begin():
        deleted = repository.delete_note("note-delete-repo")
    assert deleted is True
    assert repository.get_note("note-delete-repo") is None


def test_saved_at_timestamp_updates_on_subsequent_upserts(db_session: Session) -> None:
    repository = NoteRepository(db_session)

    with db_session.begin():
        repository.upsert_note(
            note_id="note-saved-at",
            content_json={"type": "doc", "content": []},
            content_text="Initial",
            updated_at="2026-03-01T12:00:00Z",
        )

    first_row = db_session.get(Note, "note-saved-at")
    assert first_row is not None
    first_saved_at = first_row.saved_at
    db_session.rollback()
    time.sleep(0.01)

    with db_session.begin():
        repository.upsert_note(
            note_id="note-saved-at",
            content_json={"type": "doc", "content": [{"type": "paragraph"}]},
            content_text="Updated",
            updated_at="2026-03-01T12:01:00Z",
        )

    second_row = db_session.get(Note, "note-saved-at")
    assert second_row is not None
    second_saved_at = second_row.saved_at
    assert second_saved_at.isoformat() != first_saved_at.isoformat()
