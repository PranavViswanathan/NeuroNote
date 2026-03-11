from __future__ import annotations

import app.db.engine as engine_module
from app.db.config import DatabaseSettings


def test_initialize_database_skips_when_auto_create_disabled(monkeypatch) -> None:
    settings = DatabaseSettings(
        database_url="sqlite+pysqlite:///tmp/test.db",
        db_echo=False,
        db_auto_create=False,
        require_postgres_extensions=False,
    )

    monkeypatch.setattr(engine_module, "get_database_settings", lambda: settings)

    called = {"create_all": False}

    def _fake_create_all(*_args: object, **_kwargs: object) -> None:
        called["create_all"] = True

    monkeypatch.setattr(engine_module.Base.metadata, "create_all", _fake_create_all)

    engine_module.initialize_database()

    assert called["create_all"] is False


def test_initialize_database_skips_postgres_even_when_auto_create_enabled(monkeypatch) -> None:
    settings = DatabaseSettings(
        database_url="postgresql+psycopg://user:pass@db:5432/neuronote",
        db_echo=False,
        db_auto_create=True,
        require_postgres_extensions=False,
    )

    monkeypatch.setattr(engine_module, "get_database_settings", lambda: settings)

    called = {"create_all": False, "get_engine": False}

    def _fake_create_all(*_args: object, **_kwargs: object) -> None:
        called["create_all"] = True

    def _fake_get_engine() -> object:
        called["get_engine"] = True
        return object()

    monkeypatch.setattr(engine_module.Base.metadata, "create_all", _fake_create_all)
    monkeypatch.setattr(engine_module, "get_engine", _fake_get_engine)

    engine_module.initialize_database()

    assert called["create_all"] is False
    assert called["get_engine"] is False


def test_initialize_database_creates_tables_for_sqlite_when_enabled(monkeypatch) -> None:
    settings = DatabaseSettings(
        database_url="sqlite+pysqlite:///tmp/test.db",
        db_echo=False,
        db_auto_create=True,
        require_postgres_extensions=False,
    )

    monkeypatch.setattr(engine_module, "get_database_settings", lambda: settings)

    fake_engine = object()
    called = {"create_all": False, "bind": None}

    def _fake_get_engine() -> object:
        return fake_engine

    def _fake_create_all(*_args: object, **kwargs: object) -> None:
        called["create_all"] = True
        called["bind"] = kwargs.get("bind")

    monkeypatch.setattr(engine_module, "get_engine", _fake_get_engine)
    monkeypatch.setattr(engine_module.Base.metadata, "create_all", _fake_create_all)

    engine_module.initialize_database()

    assert called["create_all"] is True
    assert called["bind"] is fake_engine
