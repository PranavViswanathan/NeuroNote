from __future__ import annotations

import hashlib
import time

from fastapi.testclient import TestClient


def _note_payload(note_id: str, text: str, updated_at: str) -> dict[str, object]:
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


def _process_payload(note_id: str, text: str, updated_at: str) -> dict[str, object]:
    return {
        "note_id": note_id,
        "content_text": text,
        "content_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "updated_at": updated_at,
    }


def _wait_for_terminal_status(client: TestClient, job_id: str) -> str:
    for _ in range(30):
        response = client.get(f"/v1/process-status/{job_id}")
        assert response.status_code == 200
        status = response.json()["status"]
        if status in {"completed", "failed"}:
            return str(status)
        time.sleep(0.01)
    return str(client.get(f"/v1/process-status/{job_id}").json()["status"])


def test_process_note_background_flow_completes(client: TestClient) -> None:
    note_id = "note-process-api-1"
    text = "Machine Learning improves pattern discovery in connected notes."
    updated_at = "2026-03-07T12:10:00Z"
    client.put(f"/v1/notes/{note_id}", json=_note_payload(note_id, text, updated_at))

    response = client.post(
        "/v1/process-note",
        json=_process_payload(note_id, text, updated_at),
    )
    assert response.status_code == 202

    job_id = response.json()["job_id"]
    status = _wait_for_terminal_status(client, job_id)
    assert status == "completed"


def test_process_note_coalesces_identical_note_version(client: TestClient) -> None:
    note_id = "note-process-api-2"
    text = "Entity resolution links aliases to canonical concepts."
    updated_at = "2026-03-07T12:11:00Z"
    payload = _process_payload(note_id, text, updated_at)

    client.put(f"/v1/notes/{note_id}", json=_note_payload(note_id, text, updated_at))
    first = client.post("/v1/process-note", json=payload)
    second = client.post("/v1/process-note", json=payload)

    assert first.status_code == 202
    assert second.status_code == 202
    assert first.json()["job_id"] == second.json()["job_id"]


def test_process_note_returns_404_for_unknown_note(client: TestClient) -> None:
    response = client.post(
        "/v1/process-note",
        json=_process_payload(
            note_id="note-process-api-missing",
            text="missing note payload",
            updated_at="2026-03-07T12:12:00Z",
        ),
    )
    assert response.status_code == 404


def test_process_status_missing_job_returns_404(client: TestClient) -> None:
    response = client.get("/v1/process-status/does-not-exist")
    assert response.status_code == 404
