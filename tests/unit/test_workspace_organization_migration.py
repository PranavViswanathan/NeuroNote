from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PATH = ROOT / "api" / "alembic" / "versions" / "20260312_0004_workspace_organization.py"


class _FakeBind:
    def __init__(
        self,
        *,
        tables: set[str] | None = None,
        columns: dict[str, set[str]] | None = None,
        indexes: dict[str, set[str]] | None = None,
    ) -> None:
        self.tables = set(tables or set())
        self.columns = {name: set(values) for name, values in (columns or {}).items()}
        self.indexes = {name: set(values) for name, values in (indexes or {}).items()}


class _FakeInspector:
    def __init__(self, bind: _FakeBind) -> None:
        self._bind = bind

    def get_table_names(self) -> list[str]:
        return sorted(self._bind.tables)

    def get_columns(self, table_name: str) -> list[dict[str, str]]:
        return [{"name": name} for name in sorted(self._bind.columns.get(table_name, set()))]

    def get_indexes(self, table_name: str) -> list[dict[str, str]]:
        return [{"name": name} for name in sorted(self._bind.indexes.get(table_name, set()))]


class _FakeOp:
    def __init__(self, bind: _FakeBind) -> None:
        self._bind = bind
        self.calls: list[tuple[str, str]] = []

    def get_bind(self) -> _FakeBind:
        return self._bind

    def add_column(self, table_name: str, column: object) -> None:
        column_name = str(getattr(column, "name"))
        self.calls.append(("add_column", f"{table_name}.{column_name}"))
        self._bind.columns.setdefault(table_name, set()).add(column_name)

    def create_table(self, table_name: str, *columns: object, **_kwargs: object) -> None:
        self.calls.append(("create_table", table_name))
        self._bind.tables.add(table_name)
        table_columns = self._bind.columns.setdefault(table_name, set())
        for column in columns:
            name = getattr(column, "name", None)
            if isinstance(name, str):
                table_columns.add(name)

    def create_index(
        self,
        index_name: str,
        table_name: str,
        _columns: list[str],
        **_kwargs: object,
    ) -> None:
        self.calls.append(("create_index", f"{table_name}.{index_name}"))
        self._bind.indexes.setdefault(table_name, set()).add(index_name)

    def drop_index(self, index_name: str, table_name: str, **_kwargs: object) -> None:
        self.calls.append(("drop_index", f"{table_name}.{index_name}"))
        self._bind.indexes.setdefault(table_name, set()).discard(index_name)

    def drop_table(self, table_name: str) -> None:
        self.calls.append(("drop_table", table_name))
        self._bind.tables.discard(table_name)

    def drop_column(self, table_name: str, column_name: str) -> None:
        self.calls.append(("drop_column", f"{table_name}.{column_name}"))
        self._bind.columns.setdefault(table_name, set()).discard(column_name)



def _load_migration_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("migration_20260312_0004", MIGRATION_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_upgrade_is_idempotent_when_schema_already_matches(monkeypatch) -> None:
    module = _load_migration_module()
    bind = _FakeBind(
        tables={"notes", "note_tags"},
        columns={"notes": {"is_pinned", "is_archived"}},
        indexes={"note_tags": {"ix_note_tags_note_id", "ix_note_tags_tag_id"}},
    )
    fake_op = _FakeOp(bind)

    monkeypatch.setattr(module, "op", fake_op)
    monkeypatch.setattr(module.sa, "inspect", lambda received_bind: _FakeInspector(received_bind))

    module.upgrade()

    assert fake_op.calls == []


def test_upgrade_adds_missing_columns_and_note_tags_table(monkeypatch) -> None:
    module = _load_migration_module()
    bind = _FakeBind(tables={"notes", "tags"}, columns={"notes": {"note_id"}})
    fake_op = _FakeOp(bind)

    monkeypatch.setattr(module, "op", fake_op)
    monkeypatch.setattr(module.sa, "inspect", lambda received_bind: _FakeInspector(received_bind))

    module.upgrade()

    assert ("add_column", "notes.is_pinned") in fake_op.calls
    assert ("add_column", "notes.is_archived") in fake_op.calls
    assert ("create_table", "note_tags") in fake_op.calls
    assert any(call == ("create_index", "note_tags.ix_note_tags_note_id") for call in fake_op.calls)


def test_downgrade_removes_note_tags_then_columns(monkeypatch) -> None:
    module = _load_migration_module()
    bind = _FakeBind(
        tables={"notes", "tags", "note_tags"},
        columns={"notes": {"note_id", "is_pinned", "is_archived"}},
        indexes={"note_tags": {"ix_note_tags_note_id", "ix_note_tags_tag_id"}},
    )
    fake_op = _FakeOp(bind)

    monkeypatch.setattr(module, "op", fake_op)
    monkeypatch.setattr(module.sa, "inspect", lambda received_bind: _FakeInspector(received_bind))

    module.downgrade()

    assert any(call == ("drop_index", "note_tags.ix_note_tags_note_id") for call in fake_op.calls)
    assert ("drop_table", "note_tags") in fake_op.calls
    assert ("drop_column", "notes.is_pinned") in fake_op.calls
    assert ("drop_column", "notes.is_archived") in fake_op.calls
