from __future__ import annotations

import time

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from app.db.models.note import Note
from app.db.repositories.note_repository import NoteRepository


def test_upsert_note_increments_version(db_session: Session) -> None:
    repository = NoteRepository(db_session)

    with db_session.begin():
        first = repository.upsert_note(
            note_id="note-repo-1",
            note_title="First title",
            subject_id="inbox",
            tags=[],
            is_pinned=False,
            is_archived=False,
            content_json={"type": "doc", "content": []},
            content_text="First",
            updated_at="2026-03-01T12:00:00Z",
        )

    with db_session.begin():
        second = repository.upsert_note(
            note_id="note-repo-1",
            note_title="Second title",
            subject_id="inbox",
            tags=[],
            is_pinned=False,
            is_archived=False,
            content_json={"type": "doc", "content": [{"type": "paragraph"}]},
            content_text="Second",
            updated_at="2026-03-01T12:01:00Z",
        )

    assert first.version == 1
    assert second.version == 2
    assert second.note_title == "Second title"


def test_get_note_returns_latest_record(db_session: Session) -> None:
    repository = NoteRepository(db_session)

    with db_session.begin():
        repository.upsert_note(
            note_id="note-repo-2",
            note_title="Stored title",
            subject_id="inbox",
            tags=[],
            is_pinned=False,
            is_archived=False,
            content_json={"type": "doc", "content": []},
            content_text="Stored value",
            updated_at="2026-03-01T12:00:00Z",
        )

    result = repository.get_note("note-repo-2")
    assert result is not None
    assert result.note_title == "Stored title"
    assert result.content_text == "Stored value"
    assert result.version == 1


def test_transaction_rollback_undoes_note_write(db_session: Session) -> None:
    repository = NoteRepository(db_session)

    with pytest.raises(RuntimeError):
        with db_session.begin():
            repository.upsert_note(
                note_id="note-rollback",
                note_title="Rollback title",
                subject_id="inbox",
                tags=[],
                is_pinned=False,
                is_archived=False,
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
            note_title="List title A",
            subject_id="inbox",
            tags=[],
            is_pinned=False,
            is_archived=False,
            content_json={"type": "doc", "content": []},
            content_text="A",
            updated_at="2026-03-01T12:00:00Z",
        )
        repository.upsert_note(
            note_id="note-list-b",
            note_title="List title B",
            subject_id="inbox",
            tags=[],
            is_pinned=False,
            is_archived=False,
            content_json={"type": "doc", "content": []},
            content_text="B",
            updated_at="2026-03-01T12:01:00Z",
        )

    items, total = repository.list_notes(limit=1, offset=0)
    assert total == 2
    assert len(items) == 1
    assert items[0].note_title in {"List title A", "List title B"}


def test_delete_note_returns_true_when_deleted(db_session: Session) -> None:
    repository = NoteRepository(db_session)

    with db_session.begin():
        repository.upsert_note(
            note_id="note-delete-repo",
            note_title="Delete title",
            subject_id="inbox",
            tags=[],
            is_pinned=False,
            is_archived=False,
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
            note_title="Initial title",
            subject_id="inbox",
            tags=[],
            is_pinned=False,
            is_archived=False,
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
            note_title="Updated title",
            subject_id="inbox",
            tags=[],
            is_pinned=False,
            is_archived=False,
            content_json={"type": "doc", "content": [{"type": "paragraph"}]},
            content_text="Updated",
            updated_at="2026-03-01T12:01:00Z",
        )

    second_row = db_session.get(Note, "note-saved-at")
    assert second_row is not None
    second_saved_at = second_row.saved_at
    assert second_saved_at.isoformat() != first_saved_at.isoformat()


def test_upsert_note_persists_subject_tags_and_flags(db_session: Session) -> None:
    repository = NoteRepository(db_session)

    with db_session.begin():
        repository.upsert_note(
            note_id="note-org-1",
            note_title="Org title",
            subject_id="ml",
            tags=["graph", "ml", "graph"],
            is_pinned=True,
            is_archived=False,
            content_json={"type": "doc", "content": []},
            content_text="Organization data",
            updated_at="2026-03-01T12:02:00Z",
        )

    result = repository.get_note("note-org-1")
    assert result is not None
    assert result.subject_id == "ml"
    assert set(result.tags) == {"graph", "ml"}
    assert result.is_pinned is True
    assert result.is_archived is False


def test_list_notes_filters_and_sorts_by_workspace_fields(db_session: Session) -> None:
    repository = NoteRepository(db_session)

    with db_session.begin():
        repository.upsert_note(
            note_id="note-filter-a",
            note_title="Graph foundations",
            subject_id="ml",
            tags=["graph", "ai"],
            is_pinned=True,
            is_archived=False,
            content_json={"type": "doc", "content": []},
            content_text="Graph learning system",
            updated_at="2026-03-01T12:03:00Z",
        )
        repository.upsert_note(
            note_id="note-filter-b",
            note_title="Archived note",
            subject_id="math",
            tags=["algebra"],
            is_pinned=False,
            is_archived=True,
            content_json={"type": "doc", "content": []},
            content_text="Archived payload",
            updated_at="2026-03-01T12:04:00Z",
        )
        repository.upsert_note(
            note_id="note-filter-c",
            note_title="Graph updates",
            subject_id="ml",
            tags=["graph"],
            is_pinned=False,
            is_archived=False,
            content_json={"type": "doc", "content": []},
            content_text="Recent active note",
            updated_at="2026-03-01T12:05:00Z",
        )

    filtered_items, filtered_total = repository.list_notes(
        limit=10,
        offset=0,
        search="graph",
        subject_id="ml",
        tag="graph",
        is_archived=False,
    )
    assert filtered_total == 2
    assert [item.note_id for item in filtered_items] == ["note-filter-a", "note-filter-c"]

    archived_items, archived_total = repository.list_notes(
        limit=10,
        offset=0,
        is_archived=True,
    )
    assert archived_total == 1
    assert archived_items[0].note_id == "note-filter-b"


def test_list_query_avoids_distinct_on_json_rows_for_postgres(db_session: Session) -> None:
    repository = NoteRepository(db_session)
    query = repository._build_list_query(  # noqa: SLF001 - targeted regression guard
        search=None,
        subject_id=None,
        tag="graph",
        is_archived=False,
        is_pinned=None,
    )
    compiled = str(
        query.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    ).upper()
    assert "DISTINCT" not in compiled
    assert "EXISTS" in compiled
