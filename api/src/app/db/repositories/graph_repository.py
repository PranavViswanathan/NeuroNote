from __future__ import annotations

import json
import re

from sqlalchemy import text
from sqlalchemy.orm import Session

_GRAPH_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_LABEL_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


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
            items.append(f"{key}: {json.dumps(value)}")
        return "{" + ", ".join(items) + "}"

    def _exec_cypher(self, graph_name: str, query: str) -> list:
        """Execute a Cypher query using exec_driver_sql with no parameters.

        AGE requires graph_name and query to be literal SQL string constants —
        bound parameters ($1/$2) are rejected at plan time with "a name constant
        is expected".  Both values are therefore embedded directly in the SQL.

        Dollar-quoting ($$ ... $$) handles the Cypher query so single-quotes in
        user content don't break the SQL string.

        exec_driver_sql bypasses SQLAlchemy's _pyformat_pattern scanner (which
        text() applies at compile time).  Passing parameters=None tells psycopg3
        to skip its own placeholder-scan step and send the SQL to PostgreSQL
        verbatim — so %(name)s patterns in user content are never mistaken for
        bind parameters by either layer.
        """
        sql = (
            "SELECT * FROM ag_catalog.cypher("
            f"'{graph_name}', "
            f"$${query}$$"
            ") AS (value ag_catalog.agtype)"
        )
        conn = self._session.connection()
        return list(conn.exec_driver_sql(sql, None).all())

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
        self._exec_cypher(graph_name, query)

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

        self._exec_cypher(graph_name, query)

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

        self._exec_cypher(graph_name, query)

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
        self._exec_cypher(graph_name, delete_edges_query)

        delete_nodes_query = f"""
        MATCH (n)
        WHERE n.source_note_id = {source_json}
        DETACH DELETE n
        RETURN 1
        """
        self._exec_cypher(graph_name, delete_nodes_query)

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

        rows = self._exec_cypher(graph_name, query)
        return [str(row[0]) for row in rows]

