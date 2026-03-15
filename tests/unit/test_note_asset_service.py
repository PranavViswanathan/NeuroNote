from __future__ import annotations

from sqlalchemy.exc import ProgrammingError

from app.services import note_asset_service


def test_reconcile_note_assets_is_noop_when_table_missing(monkeypatch, db_session) -> None:
    monkeypatch.setattr(note_asset_service, "note_assets_table_exists", lambda _session: False)

    result = note_asset_service.reconcile_note_assets_for_note(
        note_id="note-1",
        content_json={"type": "doc", "content": []},
        session=db_session,
    )

    assert result == []


def test_note_assets_table_exists_uses_postgres_regclass_probe() -> None:
    class _FakeDialect:
        name = "postgresql"

    class _FakeResult:
        def __init__(self, value: object) -> None:
            self._value = value

        def scalar_one_or_none(self) -> object:
            return self._value

    class _FakeConnection:
        def __init__(self, value: object, executed: list[str]) -> None:
            self._value = value
            self._executed = executed

        def __enter__(self) -> _FakeConnection:
            return self

        def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
            return None

        def execute(self, statement: object) -> _FakeResult:
            self._executed.append(str(statement))
            return _FakeResult(self._value)

    class _FakeBind:
        dialect = _FakeDialect()

        def __init__(self, value: object, executed: list[str]) -> None:
            self._value = value
            self._executed = executed

        def connect(self) -> _FakeConnection:
            return _FakeConnection(self._value, self._executed)

    class _FakeSession:
        def __init__(self, value: object) -> None:
            self._value = value
            self.executed: list[str] = []
            self.execute_called = False

        def get_bind(self) -> _FakeBind:
            return _FakeBind(self._value, self.executed)

        def execute(self, statement: object) -> _FakeResult:
            self.execute_called = True
            self.executed.append(str(statement))
            return _FakeResult(self._value)

    session_with_table = _FakeSession("public.note_assets")
    assert note_asset_service.note_assets_table_exists(session_with_table) is True
    assert any("to_regclass" in statement for statement in session_with_table.executed)
    assert session_with_table.execute_called is False

    session_without_table = _FakeSession(None)
    assert note_asset_service.note_assets_table_exists(session_without_table) is False
    assert session_without_table.execute_called is False


def test_reconcile_note_assets_is_noop_when_repo_hits_missing_table(
    monkeypatch,
    db_session,
) -> None:
    class _FailingRepository:
        def __init__(self, _session) -> None:
            pass

        def list_active_assets_for_note(self, _note_id: str):
            raise ProgrammingError(
                "SELECT * FROM note_assets",
                {},
                Exception('relation "note_assets" does not exist'),
            )

    monkeypatch.setattr(note_asset_service, "note_assets_table_exists", lambda _session: True)
    monkeypatch.setattr(note_asset_service, "NoteAssetRepository", _FailingRepository)

    result = note_asset_service.reconcile_note_assets_for_note(
        note_id="note-1",
        content_json={"type": "doc", "content": []},
        session=db_session,
    )

    assert result == []


def test_reconcile_note_assets_is_noop_when_delete_mark_hits_missing_table(
    monkeypatch,
    db_session,
) -> None:
    from app.db.repositories.note_asset_repository import NoteAssetRecord

    class _FailingRepository:
        def __init__(self, _session) -> None:
            pass

        def list_active_assets_for_note(self, _note_id: str):
            return [
                NoteAssetRecord(
                    asset_id="asset-1",
                    note_id="note-1",
                    mime_type="image/png",
                    file_ext="png",
                    byte_size=12,
                    relative_path="note-1/asset-1.png",
                    deleted_at=None,
                )
            ]

        def mark_deleted_many(self, _asset_ids: set[str]) -> int:
            raise ProgrammingError(
                "UPDATE note_assets SET deleted_at = now()",
                {},
                Exception('relation "note_assets" does not exist'),
            )

    monkeypatch.setattr(note_asset_service, "note_assets_table_exists", lambda _session: True)
    monkeypatch.setattr(note_asset_service, "NoteAssetRepository", _FailingRepository)

    result = note_asset_service.reconcile_note_assets_for_note(
        note_id="note-1",
        content_json={"type": "doc", "content": []},
        session=db_session,
    )

    assert result == []
