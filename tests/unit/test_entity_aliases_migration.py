from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PATH = ROOT / "api" / "alembic" / "versions" / "20260307_0002_entity_aliases.py"


class _FakeBind:
    def __init__(
        self,
        *,
        tables: set[str] | None = None,
        indexes: dict[str, set[str]] | None = None,
    ) -> None:
        self.tables = set(tables or set())
        self.indexes = {name: set(values) for name, values in (indexes or {}).items()}


class _FakeInspector:
    def __init__(self, bind: _FakeBind) -> None:
        self._bind = bind

    def get_table_names(self) -> list[str]:
        return sorted(self._bind.tables)

    def get_indexes(self, table_name: str) -> list[dict[str, str]]:
        return [{"name": name} for name in sorted(self._bind.indexes.get(table_name, set()))]


class _FakeOp:
    def __init__(self, bind: _FakeBind) -> None:
        self._bind = bind
        self.calls: list[tuple[str, str]] = []

    def get_bind(self) -> _FakeBind:
        return self._bind

    def create_table(self, table_name: str, *_args: object, **_kwargs: object) -> None:
        self.calls.append(("create_table", table_name))
        self._bind.tables.add(table_name)
        self._bind.indexes.setdefault(table_name, set())

    def create_index(
        self,
        index_name: str,
        table_name: str,
        _columns: list[str],
        **_kwargs: object,
    ) -> None:
        self.calls.append(("create_index", index_name))
        self._bind.indexes.setdefault(table_name, set()).add(index_name)

    def drop_index(self, index_name: str, **_kwargs: object) -> None:
        self.calls.append(("drop_index", index_name))
        for index_set in self._bind.indexes.values():
            index_set.discard(index_name)

    def drop_table(self, table_name: str) -> None:
        self.calls.append(("drop_table", table_name))
        self._bind.tables.discard(table_name)
        self._bind.indexes.pop(table_name, None)


def _load_migration_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("migration_20260307_0002", MIGRATION_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_upgrade_is_idempotent_when_table_and_indexes_already_exist(monkeypatch) -> None:
    module = _load_migration_module()
    bind = _FakeBind(
        tables={"entity_aliases"},
        indexes={
            "entity_aliases": {
                "ix_entity_aliases_alias_text",
                "ix_entity_aliases_canonical_entity_id",
            }
        },
    )
    fake_op = _FakeOp(bind)

    monkeypatch.setattr(module, "op", fake_op)
    monkeypatch.setattr(module.sa, "inspect", lambda received_bind: _FakeInspector(received_bind))

    module.upgrade()

    assert fake_op.calls == []


def test_upgrade_creates_missing_table_and_indexes(monkeypatch) -> None:
    module = _load_migration_module()
    bind = _FakeBind()
    fake_op = _FakeOp(bind)

    monkeypatch.setattr(module, "op", fake_op)
    monkeypatch.setattr(module.sa, "inspect", lambda received_bind: _FakeInspector(received_bind))

    module.upgrade()

    assert ("create_table", "entity_aliases") in fake_op.calls
    assert ("create_index", "ix_entity_aliases_alias_text") in fake_op.calls
    assert ("create_index", "ix_entity_aliases_canonical_entity_id") in fake_op.calls


def test_downgrade_skips_when_table_is_missing(monkeypatch) -> None:
    module = _load_migration_module()
    bind = _FakeBind()
    fake_op = _FakeOp(bind)

    monkeypatch.setattr(module, "op", fake_op)
    monkeypatch.setattr(module.sa, "inspect", lambda received_bind: _FakeInspector(received_bind))

    module.downgrade()

    assert fake_op.calls == []
