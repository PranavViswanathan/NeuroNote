from __future__ import annotations

from typing import cast

import pytest
from sqlalchemy.orm import Session

from app.db.extensions import MissingDatabaseExtensionsError, validate_required_extensions


class _FakeResult:
    def __init__(self, rows: list[tuple[str]]) -> None:
        self._rows = rows

    def all(self) -> list[tuple[str]]:
        return self._rows


class _FakeDialect:
    name = "postgresql"


class _FakeBind:
    dialect = _FakeDialect()


class _FakeSession:
    bind = _FakeBind()

    def execute(self, *_args: object, **_kwargs: object) -> _FakeResult:
        return _FakeResult([("age",)])


def test_validate_required_extensions_noop_on_sqlite(db_session: Session) -> None:
    validate_required_extensions(db_session)


def test_validate_required_extensions_raises_for_missing_postgres_extensions() -> None:
    fake = cast(Session, _FakeSession())

    with pytest.raises(MissingDatabaseExtensionsError):
        validate_required_extensions(fake)
