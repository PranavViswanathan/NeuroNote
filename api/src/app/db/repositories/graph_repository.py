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
        # Track which graph names have been confirmed to exist this session so
        # LOAD 'age' + SET search_path + graph-existence check only fire once.
        self._age_ready_graphs: set[str] = set()

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
            # Escape % so SQLAlchemy's text() doesn't interpret %(name)s patterns
            # in user content as bind parameters. SQLAlchemy converts %% → % before
            # sending to PostgreSQL, so the stored value is unchanged.
            json_value = json.dumps(value).replace("%", "%%")
            items.append(f"{key}: {json_value}")
        return "{" + ", ".join(items) + "}"

    def ensure_graph_exists(self, *, graph_name: str = "neuronote") -> None:
        self._validate_graph_name(graph_name)

        if graph_name in self._age_ready_graphs:
            return  # Already set up for this session — skip the 3 round-trips.

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

        self._age_ready_graphs.add(graph_name)

    def upsert_nodes_batch(
        self,
        *,
        label: str,
        nodes: list[dict[str, object]],
        graph_name: str = "neuronote",
    ) -> None:
        """Upsert multiple nodes of the same label in a single AGE UNWIND query.

        Each dict in `nodes` must contain an ``id`` key used as the MERGE key;
        all other keys become node properties.
        Reduces n individual round-trips down to 1 for homogeneous node batches.
        Falls back to individual upserts for a single-node list to keep call
        sites simple.
        """
        if not nodes:
            return
        if len(nodes) == 1:
            row = nodes[0]
            node_id = str(row["id"])
            self.upsert_node(label=label, node_id=node_id, properties=row, graph_name=graph_name)
            return

        self._validate_label(label)
        self.ensure_graph_exists(graph_name=graph_name)

        row_literals = ", ".join(self._cypher_map_literal(row) for row in nodes)
        query = f"""
        UNWIND [{row_literals}] AS row
        MERGE (n:{label} {{id: row.id}})
        SET n += row
        RETURN count(n)
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
        self.upsert_typed_edge(
            source_label="Concept",
            source_id=source_id,
            target_label="Concept",
            target_id=target_id,
            relation_type=relation_type,
            properties={"confidence": float(confidence)},
            graph_name=graph_name,
        )

    def upsert_typed_edge(
        self,
        *,
        source_label: str,
        source_id: str,
        target_label: str,
        target_id: str,
        relation_type: str,
        properties: dict[str, object] | None = None,
        graph_name: str = "neuronote",
    ) -> None:
        self._validate_label(source_label)
        self._validate_label(target_label)
        self._validate_label(relation_type)
        self.ensure_graph_exists(graph_name=graph_name)

        source_id_json = json.dumps(source_id)
        target_id_json = json.dumps(target_id)
        relation_properties = self._cypher_map_literal(properties or {})
        query = f"""
        MERGE (a:{source_label} {{id: {source_id_json}}})
        MERGE (b:{target_label} {{id: {target_id_json}}})
        MERGE (a)-[r:{relation_type}]->(b)
        SET r += {relation_properties}
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

    def delete_source_artifacts(
        self,
        *,
        source_note_id: str,
        graph_name: str = "neuronote",
    ) -> None:
        self.ensure_graph_exists(graph_name=graph_name)
        source_json = json.dumps(source_note_id)

        delete_edges_query = f"""
        MATCH ()-[r]-()
        WHERE r.source_note_id = {source_json}
        DELETE r
        RETURN 1
        """
        self._session.execute(
            text(
                """
                SELECT *
                FROM ag_catalog.cypher('%s', $$ %s $$) AS (value ag_catalog.agtype)
                """
                % (graph_name, delete_edges_query)
            )
        ).all()

        delete_nodes_query = f"""
        MATCH (n)
        WHERE n.source_note_id = {source_json}
        DETACH DELETE n
        RETURN 1
        """
        self._session.execute(
            text(
                """
                SELECT *
                FROM ag_catalog.cypher('%s', $$ %s $$) AS (value ag_catalog.agtype)
                """
                % (graph_name, delete_nodes_query)
            )
        ).all()

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

    def upsert_embedding(
        self,
        *,
        item_id: str,
        item_type: str,
        embedding: list[float],
    ) -> None:
        if len(embedding) != 384:
            raise ValueError("embedding must contain exactly 384 dimensions")

        vector_literal = "[" + ",".join(f"{value:.8f}" for value in embedding) + "]"

        self._session.execute(
            text(
                """
                INSERT INTO public.note_embeddings (item_id, item_type, embedding)
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

        query_literal = "[" + ",".join(f"{value:.8f}" for value in query_embedding) + "]"

        rows = self._session.execute(
            text(
                """
                SELECT item_id, embedding <=> CAST(:query_embedding AS vector(384)) AS distance
                FROM public.note_embeddings
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
