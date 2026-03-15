from __future__ import annotations

from fastapi.testclient import TestClient


def _note_payload(note_id: str, title: str, text: str, updated_at: str) -> dict[str, object]:
    return {
        "note_id": note_id,
        "note_title": title,
        "subject_id": "inbox",
        "tags": [],
        "is_pinned": False,
        "is_archived": False,
        "content_json": {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": text}],
                }
            ],
        },
        "content_text": text,
        "updated_at": updated_at,
    }


def test_list_blocks_endpoint_returns_note_blocks(client: TestClient) -> None:
    client.put(
        "/v1/notes/blocks-note-1",
        json=_note_payload("blocks-note-1", "Blocks", "Graph block", "2026-03-14T13:00:00Z"),
    )

    response = client.get("/v1/notes/blocks-note-1/blocks")
    assert response.status_code == 200
    body = response.json()
    assert body["items"]
    assert body["items"][0]["note_id"] == "blocks-note-1"
    assert body["items"][0]["block_uid"]


def test_search_blocks_endpoint_scopes_to_note(client: TestClient) -> None:
    client.put(
        "/v1/notes/search-note-a",
        json=_note_payload("search-note-a", "Search A", "Graph alpha", "2026-03-14T13:01:00Z"),
    )
    client.put(
        "/v1/notes/search-note-b",
        json=_note_payload("search-note-b", "Search B", "Graph beta", "2026-03-14T13:02:00Z"),
    )

    response = client.get("/v1/blocks/search?q=graph&note_id=search-note-a")
    assert response.status_code == 200
    body = response.json()
    assert body["items"]
    assert all(item["note_id"] == "search-note-a" for item in body["items"])


def test_search_blocks_endpoint_supports_empty_query_for_recent_blocks(client: TestClient) -> None:
    client.put(
        "/v1/notes/search-recent-a",
        json=_note_payload("search-recent-a", "Recent A", "Alpha text", "2026-03-14T13:05:00Z"),
    )
    client.put(
        "/v1/notes/search-recent-b",
        json=_note_payload("search-recent-b", "Recent B", "Beta text", "2026-03-14T13:06:00Z"),
    )

    response = client.get("/v1/blocks/search?q=&limit=5")
    assert response.status_code == 200
    body = response.json()
    assert body["items"]


def test_block_backlinks_endpoint_returns_sources(client: TestClient) -> None:
    client.put(
        "/v1/notes/backlink-target-note",
        json=_note_payload(
            "backlink-target-note",
            "Backlink Target",
            "Target body",
            "2026-03-14T13:03:00Z",
        ),
    )
    target_blocks_response = client.get("/v1/notes/backlink-target-note/blocks")
    target_block_uid = target_blocks_response.json()["items"][0]["block_uid"]

    client.put(
        "/v1/notes/backlink-source-note",
        json=_note_payload(
            "backlink-source-note",
            "Backlink Source",
            f"Link to (({target_block_uid}))",
            "2026-03-14T13:04:00Z",
        ),
    )

    response = client.get(f"/v1/blocks/{target_block_uid}/backlinks")
    assert response.status_code == 200
    body = response.json()
    assert body["block_uid"] == target_block_uid
    assert [item["source_note_id"] for item in body["items"]] == ["backlink-source-note"]


def test_block_backlinks_endpoint_returns_404_for_unknown_block(client: TestClient) -> None:
    response = client.get("/v1/blocks/does-not-exist/backlinks")
    assert response.status_code == 404
