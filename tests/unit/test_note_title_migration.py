from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PATH = ROOT / "api" / "alembic" / "versions" / "20260311_0003_note_title.py"


class _FakeBind:
    def __init__(
        self,
        *,
        tables: set[str] | None = None,
        columns: dict[str, set[str]] | None = None,
    ) -> None:
        self.tables = set(tables or set())
        self.columns = {name: set(values) for name, values in (columns or {}).items()}


class _FakeInspector:
    def __init__(self, bind: _FakeBind) -> None:
        self._bind = bind

    def get_table_names(self) -> list[str]:
        return sorted(self._bind.tables)

    def get_columns(self, table_name: str) -> list[dict[str, str]]:
        return [{"name": name} for name in sorted(self._bind.columns.get(table_name, set()))]


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

    def execute(self, statement: object) -> None:
        self.calls.append(("execute", str(statement)))

    def alter_column(self, table_name: str, column_name: str, **_kwargs: object) -> None:
        self.calls.append(("alter_column", f"{table_name}.{column_name}"))

    def drop_column(self, table_name: str, column_name: str) -> None:
        self.calls.append(("drop_column", f"{table_name}.{column_name}"))
        self._bind.columns.setdefault(table_name, set()).discard(column_name)


def _load_migration_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("migration_20260311_0003", MIGRATION_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_upgrade_is_idempotent_when_note_title_column_exists(monkeypatch) -> None:
    module = _load_migration_module()
    bind = _FakeBind(tables={"notes"}, columns={"notes": {"note_title"}})
    fake_op = _FakeOp(bind)

    monkeypatch.setattr(module, "op", fake_op)
    monkeypatch.setattr(module.sa, "inspect", lambda received_bind: _FakeInspector(received_bind))

    module.upgrade()

    assert fake_op.calls == []


def test_upgrade_adds_note_title_column_when_missing(monkeypatch) -> None:
    module = _load_migration_module()
    bind = _FakeBind(tables={"notes"}, columns={"notes": {"note_id", "content_text"}})
    fake_op = _FakeOp(bind)

    monkeypatch.setattr(module, "op", fake_op)
    monkeypatch.setattr(module.sa, "inspect", lambda received_bind: _FakeInspector(received_bind))

    module.upgrade()

    assert ("add_column", "notes.note_title") in fake_op.calls

