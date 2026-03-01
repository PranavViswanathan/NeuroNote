from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.db.extensions import check_age_capability, check_pgvector_capability


@pytest.mark.integration
@pytest.mark.postgres
def test_pgvector_capability_check(db_session: Session) -> None:
    dialect = db_session.bind.dialect.name if db_session.bind is not None else ""
    if dialect != "postgresql":
        pytest.skip("PostgreSQL-only extension test")

    check_pgvector_capability(db_session)


@pytest.mark.integration
@pytest.mark.postgres
def test_age_capability_check(db_session: Session) -> None:
    dialect = db_session.bind.dialect.name if db_session.bind is not None else ""
    if dialect != "postgresql":
        pytest.skip("PostgreSQL-only extension test")

    check_age_capability(db_session)
