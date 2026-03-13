from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.repositories.note_asset_repository import NoteAssetRepository
from app.db.repositories.note_repository import NoteRepository


def test_note_asset_repository_crud_flow(db_session: Session) -> None:
    with db_session.begin():
        NoteRepository(db_session).upsert_note(
            note_id="note-assets-1",
            note_title="Assets",
            subject_id="inbox",
            tags=[],
            is_pinned=False,
            is_archived=False,
            content_json={"type": "doc", "content": []},
            content_text="text",
            updated_at="2026-03-13T10:00:00Z",
        )

    repository = NoteAssetRepository(db_session)
    created = repository.create_asset(
        asset_id="asset-1",
        note_id="note-assets-1",
        mime_type="image/png",
        file_ext="png",
        byte_size=10,
        relative_path="note-assets-1/asset-1.png",
    )

    assert created.asset_id == "asset-1"
    loaded = repository.get_asset("asset-1")
    assert loaded is not None
    assert loaded.relative_path == "note-assets-1/asset-1.png"

    assert repository.mark_deleted("asset-1") is True
    deleted = repository.get_asset("asset-1")
    assert deleted is not None
    assert deleted.deleted_at is not None
