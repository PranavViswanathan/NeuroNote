from __future__ import annotations

from app.db.config import DEFAULT_DATABASE_URL, get_database_settings


def test_db_auto_create_defaults_to_false(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DB_ECHO", raising=False)
    monkeypatch.delenv("DB_AUTO_CREATE", raising=False)
    monkeypatch.delenv("REQUIRE_DB_EXTENSIONS", raising=False)

    settings = get_database_settings()

    assert settings.database_url == DEFAULT_DATABASE_URL
    assert settings.db_echo is False
    assert settings.db_auto_create is False
    assert settings.require_postgres_extensions is False


def test_db_auto_create_can_be_enabled_explicitly(monkeypatch) -> None:
    monkeypatch.setenv("DB_AUTO_CREATE", "true")

    settings = get_database_settings()

    assert settings.db_auto_create is True


def test_db_auto_create_can_be_disabled_explicitly(monkeypatch) -> None:
    monkeypatch.setenv("DB_AUTO_CREATE", "false")

    settings = get_database_settings()

    assert settings.db_auto_create is False
