from __future__ import annotations

from fastapi.testclient import TestClient


def _payload(note_id: str, note_title: str, text: str, updated_at: str) -> dict[str, object]:
    return {
        "note_id": note_id,
        "note_title": note_title,
        "subject_id": "inbox",
        "tags": [],
        "is_pinned": False,
        "is_archived": False,
        "content_json": {
            "type": "doc",
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": text}]},
            ],
        },
        "content_text": text,
        "updated_at": updated_at,
    }


def test_local_graph_returns_note_neighbors_and_metadata(client: TestClient) -> None:
    client.put(
        "/v1/notes/local-root",
        json=_payload(
            "local-root",
            "Root Note",
            "Machine Learning links to [[Neighbor Note]]",
            "2026-03-15T16:00:00Z",
        ),
    )
    client.put(
        "/v1/notes/local-neighbor",
        json=_payload(
            "local-neighbor",
            "Neighbor Note",
            "Neighbor body",
            "2026-03-15T16:01:00Z",
        ),
    )
    client.put(
        "/v1/notes/local-inbound",
        json=_payload(
            "local-inbound",
            "Inbound Note",
            "Inbound points to [[Root Note]]",
            "2026-03-15T16:02:00Z",
        ),
    )

    response = client.get(
        "/v1/graph/local/local-root",
        params={
            "max_hops": 1,
            "limit_nodes": 80,
            "min_confidence": 0,
            "include_types": "note,entity,relation",
        },
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["meta"]["root_note_id"] == "local-root"
    assert payload["meta"]["truncated"] is False
    assert payload["meta"]["applied_filters"] == {
        "max_hops": 1,
        "limit_nodes": 80,
        "min_confidence": 0.0,
        "include_types": ["note", "entity", "relation"],
    }

    node_ids = {node["id"] for node in payload["nodes"]}
    assert "local-root" in node_ids
    assert "local-neighbor" in node_ids
    assert "local-inbound" in node_ids

    sorted_nodes = sorted(payload["nodes"], key=lambda item: (item["type"], item["id"]))
    assert payload["nodes"] == sorted_nodes

    edge_pairs = {(edge["source"], edge["target"], edge["type"]) for edge in payload["edges"]}
    assert ("local-root", "local-neighbor", "LINKS_TO") in edge_pairs
    assert ("local-inbound", "local-root", "LINKS_TO") in edge_pairs


def test_local_graph_respects_node_limit_and_marks_truncated(client: TestClient) -> None:
    client.put(
        "/v1/notes/local-limit-root",
        json=_payload(
            "local-limit-root",
            "Limit Root",
            "Links to [[Limit Neighbor]]",
            "2026-03-15T16:10:00Z",
        ),
    )
    client.put(
        "/v1/notes/local-limit-neighbor",
        json=_payload(
            "local-limit-neighbor",
            "Limit Neighbor",
            "Neighbor body",
            "2026-03-15T16:11:00Z",
        ),
    )

    response = client.get(
        "/v1/graph/local/local-limit-root",
        params={"limit_nodes": 1, "include_types": "note,relation"},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["nodes"]) == 1
    assert body["meta"]["truncated"] is True
    assert len(body["edges"]) == 0


def test_local_graph_returns_404_for_unknown_note(client: TestClient) -> None:
    response = client.get("/v1/graph/local/missing-note")
    assert response.status_code == 404
