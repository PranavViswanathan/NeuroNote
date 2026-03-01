from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _payload(note_id: str, text: str, updated_at: str) -> dict[str, object]:
    return {
        "note_id": note_id,
        "content_json": {
            "type": "doc",
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": text}]},
            ],
        },
        "content_text": text,
        "updated_at": updated_at,
    }


def test_put_note_saves_and_versions() -> None:
    first = client.put("/v1/notes/note-e1", json=_payload("note-e1", "First text", "2026-03-01T12:00:00Z"))
    assert first.status_code == 200
    assert first.json()["note_id"] == "note-e1"
    assert first.json()["version"] == 1

    second = client.put(
        "/v1/notes/note-e1",
        json=_payload("note-e1", "Updated text", "2026-03-01T12:01:00Z"),
    )
    assert second.status_code == 200
    assert second.json()["version"] == 2


def test_get_note_returns_saved_payload() -> None:
    client.put("/v1/notes/note-fetch", json=_payload("note-fetch", "Fetch text", "2026-03-01T12:02:00Z"))

    response = client.get("/v1/notes/note-fetch")
    assert response.status_code == 200
    body = response.json()
    assert body["note_id"] == "note-fetch"
    assert body["content_text"] == "Fetch text"
    assert body["version"] == 1


def test_put_note_rejects_path_payload_mismatch() -> None:
    response = client.put(
        "/v1/notes/path-note",
        json=_payload("body-note", "Mismatch", "2026-03-01T12:03:00Z"),
    )
    assert response.status_code == 400


def test_get_note_returns_404_for_unknown_note() -> None:
    response = client.get("/v1/notes/does-not-exist")
    assert response.status_code == 404


def test_put_note_rejects_invalid_payload() -> None:
    response = client.put(
        "/v1/notes/note-invalid",
        json={
            "note_id": "",
            "content_json": {},
            "content_text": "",
            "updated_at": "",
        },
    )
    assert response.status_code == 422
