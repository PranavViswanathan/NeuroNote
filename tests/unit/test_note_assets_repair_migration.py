from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PATH = ROOT / "api" / "alembic" / "versions" / "20260314_0007_note_assets_repair.py"


class _FakeBind:
    def __init__(
        self,
        *,
        tables_by_schema: dict[str | None, set[str]] | None = None,
        indexes_by_schema: dict[tuple[str | None, str], set[str]] | None = None,
    ) -> None:
        self.tables_by_schema = {
            schema: set(tables) for schema, tables in (tables_by_schema or {}).items()
        }
        self.indexes_by_schema = {
            (schema, table): set(indexes)
            for (schema, table), indexes in (indexes_by_schema or {}).items()
        }


class _FakeInspector:
    def __init__(self, bind: _FakeBind) -> None:
        self._bind = bind

    def get_table_names(self, schema: str | None = None) -> list[str]:
        return sorted(self._bind.tables_by_schema.get(schema, set()))

    def get_indexes(self, table_name: str, schema: str | None = None) -> list[dict[str, str]]:
        indexes = self._bind.indexes_by_schema.get((schema, table_name), set())
        return [{"name": name} for name in sorted(indexes)]


class _FakeOp:
    def __init__(self, bind: _FakeBind) -> None:
        self._bind = bind
        self.calls: list[tuple[str, str]] = []

    def get_bind(self) -> _FakeBind:
        return self._bind

    def create_table(self, table_name: str, *_columns: object, **kwargs: object) -> None:
        schema = kwargs.get("schema")
        schema_name = str(schema) if isinstance(schema, str) else None
        self.calls.append(("create_table", f"{schema_name}.{table_name}" if schema_name else table_name))
        self._bind.tables_by_schema.setdefault(schema_name, set()).add(table_name)

    def create_index(self, index_name: str, table_name: str, _columns: list[str], **kwargs: object) -> None:
        schema = kwargs.get("schema")
        schema_name = str(schema) if isinstance(schema, str) else None
        self.calls.append(
            (
                "create_index",
                f"{schema_name}.{table_name}.{index_name}" if schema_name else f"{table_name}.{index_name}",
            )
        )
        self._bind.indexes_by_schema.setdefault((schema_name, table_name), set()).add(index_name)


def _load_migration_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("migration_20260314_0007", MIGRATION_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_upgrade_creates_public_note_assets_when_missing(monkeypatch) -> None:
    module = _load_migration_module()
    bind = _FakeBind(
        tables_by_schema={
            "public": {"notes", "blocks"},
            None: {"notes", "blocks"},
        },
        indexes_by_schema={},
    )
    fake_op = _FakeOp(bind)

    monkeypatch.setattr(module, "op", fake_op)
    monkeypatch.setattr(module.sa, "inspect", lambda received_bind: _FakeInspector(received_bind))

    module.upgrade()
    assert ("create_table", "public.note_assets") in fake_op.calls
    assert ("create_index", "public.note_assets.ix_note_assets_note_id") in fake_op.calls


def test_upgrade_is_idempotent_when_public_note_assets_exists(monkeypatch) -> None:
    module = _load_migration_module()
    bind = _FakeBind(
        tables_by_schema={
            "public": {"notes", "note_assets"},
            None: {"notes", "note_assets"},
        },
        indexes_by_schema={
            ("public", "note_assets"): {"ix_note_assets_note_id"},
        },
    )
    fake_op = _FakeOp(bind)

    monkeypatch.setattr(module, "op", fake_op)
    monkeypatch.setattr(module.sa, "inspect", lambda received_bind: _FakeInspector(received_bind))

    module.upgrade()
    assert fake_op.calls == []
