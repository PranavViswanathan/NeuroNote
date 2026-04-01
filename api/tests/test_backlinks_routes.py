"""Integration tests for backlinks and block HTTP routes."""
from __future__ import annotations


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _note_payload(
    note_id: str,
    title: str,
    content_text: str = "some content",
    tags: list[str] | None = None,
) -> dict:
    return {
        "note_id": note_id,
        "note_title": title,
        "subject_id": "inbox",
        "tags": tags or [],
        "is_pinned": False,
        "is_archived": False,
        "content_json": {"type": "doc", "content": []},
        "content_text": content_text,
        "updated_at": "2026-01-01T00:00:00Z",
    }


def _note_payload_with_blocks(
    note_id: str,
    title: str,
    block_text: str,
    block_uid: str,
) -> dict:
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
                    "attrs": {"blockUid": block_uid},
                    "content": [{"type": "text", "text": block_text}],
                }
            ],
        },
        "content_text": block_text,
        "updated_at": "2026-01-01T00:00:00Z",
    }


# ---------------------------------------------------------------------------
# GET /v1/notes/{id}/backlinks
# ---------------------------------------------------------------------------


def test_backlinks_for_existing_note_no_backlinks(client):
    client.put("/v1/notes/note-t", json=_note_payload("note-t", "Target"))

    resp = client.get("/v1/notes/note-t/backlinks")

    assert resp.status_code == 200
    data = resp.json()
    assert data["note_id"] == "note-t"
    assert data["items"] == []


def test_backlinks_returns_item_when_linked(client):
    client.put("/v1/notes/note-target", json=_note_payload("note-target", "Target Note"))
    client.put(
        "/v1/notes/note-source",
        json=_note_payload(
            "note-source",
            "Source Note",
            content_text="See [[Target Note]] for details",
        ),
    )

    resp = client.get("/v1/notes/note-target/backlinks")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["source_note_id"] == "note-source"


def test_backlinks_for_missing_note_returns_404(client):
    resp = client.get("/v1/notes/does-not-exist/backlinks")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /v1/notes/{id}/blocks
# ---------------------------------------------------------------------------


def test_list_blocks_for_note(client):
    payload = _note_payload_with_blocks("note-b", "Block Note", "Hello block", "uid-block1")
    client.put("/v1/notes/note-b", json=payload)

    resp = client.get("/v1/notes/note-b/blocks")

    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert len(data["items"]) >= 1
    assert data["items"][0]["block_uid"] == "uid-block1"


# ---------------------------------------------------------------------------
# GET /v1/blocks/search
# ---------------------------------------------------------------------------


def test_search_blocks_returns_matching(client):
    payload = _note_payload_with_blocks(
        "note-search", "Search Note", "backpropagation algorithm", "uid-bp"
    )
    client.put("/v1/notes/note-search", json=payload)

    resp = client.get("/v1/blocks/search?q=backpropagation")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) >= 1
    assert any(item["block_uid"] == "uid-bp" for item in data["items"])


def test_search_blocks_no_query_returns_recent(client):
    payload = _note_payload_with_blocks(
        "note-recent", "Recent Note", "some text", "uid-recent"
    )
    client.put("/v1/notes/note-recent", json=payload)

    resp = client.get("/v1/blocks/search")

    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data


# ---------------------------------------------------------------------------
# GET /v1/blocks/{uid}/backlinks
# ---------------------------------------------------------------------------


def test_block_backlinks_unknown_uid_returns_404(client):
    resp = client.get("/v1/blocks/no-such-uid/backlinks")
    assert resp.status_code == 404


def test_block_backlinks_returns_items_when_referenced(client):
    target_uid = "uid-target-blk"
    ref_uid = "uid-ref-blk"

    # Create target note with a block
    client.put(
        "/v1/notes/note-target",
        json=_note_payload_with_blocks("note-target", "Target BL Note", "I am the target", target_uid),
    )

    # Create source note whose block text references the target uid via ((...))
    ref_text = f"See ((uid-target-blk)) for details"
    client.put(
        "/v1/notes/note-ref",
        json=_note_payload_with_blocks("note-ref", "Ref BL Note", ref_text, ref_uid),
    )

    resp = client.get(f"/v1/blocks/{target_uid}/backlinks")

    assert resp.status_code == 200
    data = resp.json()
    assert data["block_uid"] == target_uid
    assert "items" in data
    assert len(data["items"]) >= 1
    assert any(item["source_block_uid"] == ref_uid for item in data["items"])
