from __future__ import annotations

from collections.abc import Iterator
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
API_SRC = ROOT / "api" / "src"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))


@pytest.fixture()
def configured_db(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    external_db_url = os.getenv("TEST_DATABASE_URL")
    if external_db_url:
        monkeypatch.setenv("DATABASE_URL", external_db_url)
    else:
        test_db_path = tmp_path / "api-test.db"
        monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{test_db_path}")
    monkeypatch.setenv("DB_AUTO_CREATE", "true")
    monkeypatch.setenv("REQUIRE_DB_EXTENSIONS", "false")

    from app.db.engine import initialize_database, reset_engine

    reset_engine()
    initialize_database()
    yield
    reset_engine()


@pytest.fixture()
def client(configured_db: None) -> Iterator[TestClient]:
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def db_session(configured_db: None) -> Iterator["Session"]:
    from app.db.engine import get_session_factory

    factory = get_session_factory()
    with factory() as session:
        yield session
