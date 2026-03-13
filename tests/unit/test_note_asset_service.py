from __future__ import annotations

from app.services import note_asset_service


def test_reconcile_note_assets_is_noop_when_table_missing(monkeypatch, db_session) -> None:
    monkeypatch.setattr(note_asset_service, "note_assets_table_exists", lambda _session: False)

    result = note_asset_service.reconcile_note_assets_for_note(
        note_id="note-1",
        content_json={"type": "doc", "content": []},
        session=db_session,
    )

    assert result == []
