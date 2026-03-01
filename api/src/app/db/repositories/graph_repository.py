from __future__ import annotations

from dataclasses import dataclass
import json
import re

from sqlalchemy import text
from sqlalchemy.orm import Session

_GRAPH_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_LABEL_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(slots=True)
class EmbeddingNeighbor:
    item_id: str
    distance: float


class GraphRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def _validate_graph_name(self, graph_name: str) -> None:
        if not _GRAPH_NAME_PATTERN.fullmatch(graph_name):
            raise ValueError(f"Invalid AGE graph name: {graph_name!r}")

    def _validate_label(self, label: str) -> None:
        if not _LABEL_PATTERN.fullmatch(label):
            raise ValueError(f"Invalid label: {label!r}")

    def _cypher_map_literal(self, properties: dict[str, object]) -> str:
        items: list[str] = []
        for key, value in properties.items():
            self._validate_label(key)
            items.append(f"{key}: {json.dumps(value)}")
        return "{" + ", ".join(items) + "}"

    def ensure_graph_exists(self, *, graph_name: str = "neuronote") -> None:
        self._validate_graph_name(graph_name)

        self._session.execute(text("LOAD 'age'"))
        self._session.execute(text('SET search_path = ag_catalog, "$user", public'))

        graph_exists = self._session.execute(
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
            self._session.execute(
                text("SELECT ag_catalog.create_graph(:graph_name)"),
                {"graph_name": graph_name},
            )

    def upsert_node(
        self,
        *,
        label: str,
        node_id: str,
        properties: dict[str, object],
        graph_name: str = "neuronote",
    ) -> None:
        self._validate_label(label)
        self.ensure_graph_exists(graph_name=graph_name)

        node_id_json = json.dumps(node_id)
        properties_literal = self._cypher_map_literal(properties)
        query = f"""
        MERGE (n:{label} {{id: {node_id_json}}})
        SET n += {properties_literal}
        RETURN n
        """

        self._session.execute(
            text(
                """
                SELECT *
                FROM ag_catalog.cypher('%s', $$ %s $$) AS (value ag_catalog.agtype)
                """
                % (graph_name, query)
            )
        ).first()

    def upsert_edge(
        self,
        *,
        source_id: str,
        target_id: str,
        relation_type: str,
        confidence: float,
        graph_name: str = "neuronote",
    ) -> None:
        self._validate_label(relation_type)
        self.ensure_graph_exists(graph_name=graph_name)

        source_id_json = json.dumps(source_id)
        target_id_json = json.dumps(target_id)
        query = f"""
        MERGE (a:Concept {{id: {source_id_json}}})
        MERGE (b:Concept {{id: {target_id_json}}})
        MERGE (a)-[r:{relation_type}]->(b)
        SET r.confidence = {float(confidence)}
        RETURN r
        """

        self._session.execute(
            text(
                """
                SELECT *
                FROM ag_catalog.cypher('%s', $$ %s $$) AS (value ag_catalog.agtype)
                """
                % (graph_name, query)
            )
        ).first()

    def fetch_local_neighborhood(
        self,
        *,
        node_id: str,
        max_hops: int = 2,
        limit: int = 50,
        graph_name: str = "neuronote",
    ) -> list[str]:
        if max_hops < 1:
            raise ValueError("max_hops must be >= 1")
        if limit < 1:
            raise ValueError("limit must be >= 1")

        self.ensure_graph_exists(graph_name=graph_name)
        node_id_json = json.dumps(node_id)
        query = f"""
        MATCH p = (n {{id: {node_id_json}}})-[*1..{max_hops}]-(m)
        RETURN p
        LIMIT {limit}
        """

        rows = self._session.execute(
            text(
                """
                SELECT *
                FROM ag_catalog.cypher('%s', $$ %s $$) AS (value ag_catalog.agtype)
                """
                % (graph_name, query)
            )
        ).all()
        return [str(row[0]) for row in rows]

    def ensure_embedding_table(self) -> None:
        self._session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS note_embeddings (
                    embedding_id BIGSERIAL PRIMARY KEY,
                    item_id TEXT NOT NULL,
                    item_type TEXT NOT NULL,
                    embedding vector(384) NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE (item_id, item_type)
                )
                """
            )
        )

    def upsert_embedding(
        self,
        *,
        item_id: str,
        item_type: str,
        embedding: list[float],
    ) -> None:
        if len(embedding) != 384:
            raise ValueError("embedding must contain exactly 384 dimensions")

        self.ensure_embedding_table()
        vector_literal = "[" + ",".join(f"{value:.8f}" for value in embedding) + "]"

        self._session.execute(
            text(
                """
                INSERT INTO note_embeddings (item_id, item_type, embedding)
                VALUES (:item_id, :item_type, CAST(:embedding AS vector(384)))
                ON CONFLICT (item_id, item_type)
                DO UPDATE SET embedding = EXCLUDED.embedding, created_at = NOW()
                """
            ),
            {
                "item_id": item_id,
                "item_type": item_type,
                "embedding": vector_literal,
            },
        )

    def nearest_neighbors(
        self,
        *,
        item_type: str,
        query_embedding: list[float],
        limit: int = 5,
    ) -> list[EmbeddingNeighbor]:
        if len(query_embedding) != 384:
            raise ValueError("query_embedding must contain exactly 384 dimensions")
        if limit < 1:
            raise ValueError("limit must be >= 1")

        self.ensure_embedding_table()
        query_literal = "[" + ",".join(f"{value:.8f}" for value in query_embedding) + "]"

        rows = self._session.execute(
            text(
                """
                SELECT item_id, embedding <=> CAST(:query_embedding AS vector(384)) AS distance
                FROM note_embeddings
                WHERE item_type = :item_type
                ORDER BY embedding <=> CAST(:query_embedding AS vector(384))
                LIMIT :limit
                """
            ),
            {
                "query_embedding": query_literal,
                "item_type": item_type,
                "limit": limit,
            },
        ).all()

        return [
            EmbeddingNeighbor(item_id=str(row[0]), distance=float(row[1]))
            for row in rows
        ]
