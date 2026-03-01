from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_process_note_queues_job(client: TestClient) -> None:
    payload = {
        "note_id": "note-1",
        "content_text": "Machine learning improves pattern discovery.",
        "content_hash": "hash-1",
        "updated_at": "2026-03-01T11:00:00Z",
    }

    response = client.post("/v1/process-note", json=payload)
    assert response.status_code == 202

    body = response.json()
    assert body["status"] == "queued"
    assert isinstance(body["job_id"], str)


def test_process_status_returns_existing_job(client: TestClient) -> None:
    payload = {
        "note_id": "note-2",
        "content_text": "Knowledge graphs represent entities and relations.",
        "content_hash": "hash-2",
        "updated_at": "2026-03-01T11:01:00Z",
    }
    created = client.post("/v1/process-note", json=payload).json()

    response = client.get(f"/v1/process-status/{created['job_id']}")
    assert response.status_code == 200

    status_body = response.json()
    assert status_body["job_id"] == created["job_id"]
    assert status_body["status"] == "queued"


def test_process_note_rejects_invalid_payload(client: TestClient) -> None:
    payload = {
        "note_id": "",
        "content_text": "",
    }
    response = client.post("/v1/process-note", json=payload)
    assert response.status_code == 422


def test_process_status_missing_job_returns_404(client: TestClient) -> None:
    response = client.get("/v1/process-status/does-not-exist")
    assert response.status_code == 404
