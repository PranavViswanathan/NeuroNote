from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.db.repositories.graph_repository import GraphRepository


def _unit_embedding(index: int) -> list[float]:
    embedding = [0.0] * 384
    embedding[index] = 1.0
    return embedding


@pytest.mark.integration
@pytest.mark.postgres
def test_graph_repository_upserts_nodes_and_edges(db_session: Session) -> None:
    dialect = db_session.bind.dialect.name if db_session.bind is not None else ""
    if dialect != "postgresql":
        pytest.skip("PostgreSQL-only graph test")

    repository = GraphRepository(db_session)
    with db_session.begin():
        repository.upsert_node(
            label="Concept",
            node_id="concept-1",
            properties={"name": "Machine Learning"},
        )
        repository.upsert_node(
            label="Concept",
            node_id="concept-2",
            properties={"name": "Statistics"},
        )
        repository.upsert_edge(
            source_id="concept-1",
            target_id="concept-2",
            relation_type="RELATED_TO",
            confidence=0.91,
        )

    neighborhood = repository.fetch_local_neighborhood(
        node_id="concept-1",
        max_hops=1,
        limit=10,
    )
    assert neighborhood


@pytest.mark.integration
@pytest.mark.postgres
def test_graph_repository_embedding_neighbors(db_session: Session) -> None:
    dialect = db_session.bind.dialect.name if db_session.bind is not None else ""
    if dialect != "postgresql":
        pytest.skip("PostgreSQL-only vector test")

    repository = GraphRepository(db_session)
    with db_session.begin():
        repository.upsert_embedding(
            item_id="concept-neighbor-a",
            item_type="concept",
            embedding=_unit_embedding(0),
        )
        repository.upsert_embedding(
            item_id="concept-neighbor-b",
            item_type="concept",
            embedding=_unit_embedding(1),
        )

    neighbors = repository.nearest_neighbors(
        item_type="concept",
        query_embedding=_unit_embedding(0),
        limit=2,
    )

    assert neighbors
    assert neighbors[0].item_id == "concept-neighbor-a"
    assert neighbors[0].distance == pytest.approx(0.0, abs=1e-6)
