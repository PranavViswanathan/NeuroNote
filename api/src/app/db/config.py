from __future__ import annotations

from dataclasses import dataclass
import os

DEFAULT_DATABASE_URL = "sqlite+pysqlite:///./api/dev.db"


def _as_bool(raw_value: str | None, *, default: bool) -> bool:
    if raw_value is None:
        return default
    normalized = raw_value.strip().lower()
    return normalized in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class DatabaseSettings:
    database_url: str
    db_echo: bool
    db_auto_create: bool
    require_postgres_extensions: bool


def get_database_settings() -> DatabaseSettings:
    return DatabaseSettings(
        database_url=os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL),
        db_echo=_as_bool(os.getenv("DB_ECHO"), default=False),
        db_auto_create=_as_bool(os.getenv("DB_AUTO_CREATE"), default=True),
        require_postgres_extensions=_as_bool(
            os.getenv("REQUIRE_DB_EXTENSIONS"),
            default=False,
        ),
    )


__all__ = ["DatabaseSettings", "get_database_settings", "DEFAULT_DATABASE_URL"]
