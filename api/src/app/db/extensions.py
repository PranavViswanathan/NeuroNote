from __future__ import annotations

import re

from sqlalchemy import text
from sqlalchemy.orm import Session

REQUIRED_POSTGRES_EXTENSIONS = {"age", "vector"}
_GRAPH_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class MissingDatabaseExtensionsError(RuntimeError):
    """Raised when a PostgreSQL deployment lacks required extensions."""


def _dialect_name(session: Session) -> str:
    if session.bind is None:
        return ""
    return session.bind.dialect.name


def fetch_installed_extensions(session: Session) -> set[str]:
    rows = session.execute(
        text(
            """
            SELECT extname
            FROM pg_extension
            WHERE extname IN ('age', 'vector')
            """
        )
    ).all()
    return {row[0] for row in rows}


def validate_required_extensions(session: Session) -> None:
    if _dialect_name(session) != "postgresql":
        return

    installed = fetch_installed_extensions(session)
    missing = REQUIRED_POSTGRES_EXTENSIONS - installed
    if missing:
        joined = ", ".join(sorted(missing))
        raise MissingDatabaseExtensionsError(
            f"Missing required PostgreSQL extensions: {joined}",
        )


def check_pgvector_capability(session: Session) -> None:
    session.execute(
        text(
            """
            CREATE TEMP TABLE _neuronote_vector_check (
                id INTEGER PRIMARY KEY,
                embedding vector(3) NOT NULL
            )
            """
        )
    )
    session.execute(
        text(
            """
            INSERT INTO _neuronote_vector_check (id, embedding)
            VALUES (1, '[1,0,0]'::vector), (2, '[0,1,0]'::vector)
            """
        )
    )
    session.execute(
        text(
            """
            SELECT id
            FROM _neuronote_vector_check
            ORDER BY embedding <=> '[1,0,0]'::vector
            LIMIT 1
            """
        )
    ).first()
    session.execute(text("DROP TABLE _neuronote_vector_check"))


def check_age_capability(session: Session, *, graph_name: str = "neuronote") -> None:
    if not _GRAPH_NAME_PATTERN.fullmatch(graph_name):
        raise ValueError(f"Invalid AGE graph name: {graph_name!r}")

    session.execute(text("LOAD 'age'"))
    session.execute(text('SET search_path = ag_catalog, "$user", public'))

    graph_exists = session.execute(
        text(
            """
            SELECT 1
            FROM ag_catalog.ag_graph
            WHERE name = :graph_name
            LIMIT 1
            """
        ),
        {"graph_name": graph_name},
    ).first()

    if graph_exists is None:
        session.execute(
            text("SELECT ag_catalog.create_graph(:graph_name)"),
            {"graph_name": graph_name},
        )

    session.execute(
        text(
            """
            SELECT *
            FROM ag_catalog.cypher('%s', $$ RETURN 1 $$) AS (value ag_catalog.agtype)
            """
            % graph_name
        )
    ).first()
