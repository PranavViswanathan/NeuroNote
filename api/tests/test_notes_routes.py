"""Integration tests for notes HTTP routes."""
from __future__ import annotations


# ---------------------------------------------------------------------------
# Payload helper
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


# ---------------------------------------------------------------------------
# PUT /v1/notes/{id}
# ---------------------------------------------------------------------------


def test_put_note_creates_note_returns_200(client):
    payload = make_note_payload()
    resp = client.put("/v1/notes/note-1", json=payload)

    assert resp.status_code == 200
    data = resp.json()
    assert data["note_id"] == "note-1"
    assert "saved_at" in data
    assert data["version"] == 1


def test_put_note_mismatched_path_and_payload_returns_400(client):
    payload = make_note_payload(note_id="note-payload")
    resp = client.put("/v1/notes/note-path", json=payload)

    assert resp.status_code == 400


def test_put_note_duplicate_title_returns_409(client):
    payload_a = make_note_payload(note_id="note-a", title="Unique Title")
    payload_b = make_note_payload(note_id="note-b", title="Unique Title")

    r1 = client.put("/v1/notes/note-a", json=payload_a)
    assert r1.status_code == 200

    r2 = client.put("/v1/notes/note-b", json=payload_b)
    assert r2.status_code == 409


# ---------------------------------------------------------------------------
# GET /v1/notes/{id}
# ---------------------------------------------------------------------------


def test_get_note_returns_note_data(client):
    payload = make_note_payload(note_id="note-g", title="Get Note")
    client.put("/v1/notes/note-g", json=payload)

    resp = client.get("/v1/notes/note-g")

    assert resp.status_code == 200
    data = resp.json()
    assert data["note_id"] == "note-g"
    assert data["note_title"] == "Get Note"


def test_get_note_missing_returns_404(client):
    resp = client.get("/v1/notes/does-not-exist")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /v1/notes
# ---------------------------------------------------------------------------


def test_list_notes_returns_correct_structure(client):
    client.put("/v1/notes/note-1", json=make_note_payload())

    resp = client.get("/v1/notes")

    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


def test_list_notes_search_filters_correctly(client):
    client.put("/v1/notes/note-a", json=make_note_payload(note_id="note-a", title="Machine Learning"))
    client.put("/v1/notes/note-b", json=make_note_payload(note_id="note-b", title="Cooking Recipes"))

    resp = client.get("/v1/notes?search=machine")

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["note_id"] == "note-a"


def test_list_notes_is_archived_filter(client):
    client.put("/v1/notes/note-active", json=make_note_payload(note_id="note-active", title="Active"))
    client.put(
        "/v1/notes/note-arch",
        json=make_note_payload(note_id="note-arch", title="Archived", is_archived=True),
    )

    resp = client.get("/v1/notes?is_archived=true")

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["note_id"] == "note-arch"


def test_list_notes_tag_filter(client):
    client.put(
        "/v1/notes/note-ml",
        json=make_note_payload(note_id="note-ml", title="ML Note", tags=["ml"]),
    )
    client.put(
        "/v1/notes/note-other",
        json=make_note_payload(note_id="note-other", title="Other Note", tags=[]),
    )

    resp = client.get("/v1/notes?tag=ml")

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["note_id"] == "note-ml"


# ---------------------------------------------------------------------------
# DELETE /v1/notes/{id}
# ---------------------------------------------------------------------------


def test_delete_note_returns_204(client):
    client.put("/v1/notes/note-del", json=make_note_payload(note_id="note-del", title="Delete Me"))

    resp = client.delete("/v1/notes/note-del")

    assert resp.status_code == 204


def test_delete_note_missing_returns_404(client):
    resp = client.delete("/v1/notes/ghost-note")
    assert resp.status_code == 404
