from __future__ import annotations

import os
import tempfile

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import Base
from app.db.repositories.block_repository import BlockRepository
from app.db.repositories.note_repository import NoteRepository


@pytest.fixture(scope="function")
def db_engine():
    """
    Create a temporary file-based SQLite engine per test.

    We use a file-based database (rather than :memory:) because
    `note_assets_table_exists` calls `inspect(engine)` which opens a second
    connection. With in-memory SQLite + StaticPool the pool reset on that
    second connection issues a ROLLBACK that silently discards uncommitted
    data. A file-based SQLite database avoids this because connections are
    independent.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db_url = f"sqlite+pysqlite:///{db_path}"
    os.environ["DATABASE_URL"] = db_url
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture
def session(db_engine):
    """Session for direct repository tests."""
    factory = sessionmaker(bind=db_engine, autoflush=False, expire_on_commit=False)
    sess = factory()
    yield sess
    sess.rollback()
    sess.close()


@pytest.fixture
def note_repo(session):
    return NoteRepository(session)


@pytest.fixture
def block_repo(session):
    return BlockRepository(session)


@pytest.fixture
def client(db_engine):
    """
    HTTP test client fixture.

    The dependency override yields a fresh session per request so that route
    handlers can call session.begin() without hitting the SQLAlchemy autobegin
    conflict.
    """
    from app.db.session import get_db_session
    from app.main import app

    _factory = sessionmaker(bind=db_engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        sess = _factory()
        try:
            yield sess
        finally:
            sess.close()

    app.dependency_overrides[get_db_session] = override_get_db
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers shared across test modules
# ---------------------------------------------------------------------------

def make_note_payload(
    note_id: str = "note-1",
    title: str = "Test Note",
    subject_id: str = "inbox",
    tags: list[str] | None = None,
    content_text: str = "test content",
    is_pinned: bool = False,
    is_archived: bool = False,
) -> dict:
    return {
        "note_id": note_id,
        "note_title": title,
        "subject_id": subject_id,
        "tags": tags or [],
        "is_pinned": is_pinned,
        "is_archived": is_archived,
        "content_json": {"type": "doc", "content": []},
        "content_text": content_text,
        "updated_at": "2026-01-01T00:00:00Z",
    }
