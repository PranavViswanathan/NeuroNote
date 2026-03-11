from __future__ import annotations

from fastapi.testclient import TestClient


def test_confirm_alias_persists_mapping(client: TestClient) -> None:
    response = client.post(
        "/v1/entity-aliases/confirm",
        json={
            "alias_text": "ML",
            "canonical_entity_id": "concept-machine-learning",
            "canonical_name": "Machine Learning",
            "confidence": 0.92,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["alias_text"] == "ml"
    assert body["canonical_entity_id"] == "concept-machine-learning"
    assert body["source"] == "user_confirmed"


def test_confirm_alias_conflict_keeps_higher_confidence_mapping(client: TestClient) -> None:
    first = client.post(
        "/v1/entity-aliases/confirm",
        json={
            "alias_text": "AI",
            "canonical_entity_id": "concept-artificial-intelligence",
            "canonical_name": "Artificial Intelligence",
            "confidence": 0.96,
        },
    )
    assert first.status_code == 200

    second = client.post(
        "/v1/entity-aliases/confirm",
        json={
            "alias_text": "AI",
            "canonical_entity_id": "concept-applied-inference",
            "canonical_name": "Applied Inference",
            "confidence": 0.5,
        },
    )
    assert second.status_code == 200

    body = second.json()
    assert body["canonical_entity_id"] == "concept-artificial-intelligence"


def test_alias_calibration_stats_are_reported(client: TestClient) -> None:
    client.post(
        "/v1/entity-aliases/confirm",
        json={
            "alias_text": "KG",
            "canonical_entity_id": "concept-knowledge-graph",
            "canonical_name": "Knowledge Graph",
            "confidence": 0.9,
        },
    )
    client.post(
        "/v1/entity-aliases/confirm",
        json={
            "alias_text": "NLP",
            "canonical_entity_id": "concept-natural-language-processing",
            "canonical_name": "Natural Language Processing",
            "confidence": 0.8,
        },
    )

    response = client.get("/v1/entity-aliases/calibration")
    assert response.status_code == 200

    body = response.json()
    assert body["total_aliases"] == 2
    assert body["avg_confidence"] == 0.85


def test_resolve_preview_exposes_unresolved_entities(client: TestClient) -> None:
    client.post(
        "/v1/entity-aliases/confirm",
        json={
            "alias_text": "Machine Learning",
            "canonical_entity_id": "concept-machine-learning",
            "canonical_name": "Machine Learning",
            "confidence": 0.95,
        },
    )

    response = client.post(
        "/v1/entity-aliases/resolve-preview",
        json={
            "entities": [
                {
                    "entity_id": "entity-1",
                    "text": "Machine-Learning",
                    "label": "proper_noun",
                    "confidence": 0.8,
                },
                {
                    "entity_id": "entity-2",
                    "text": "xqzv_123",
                    "label": "acronym",
                    "confidence": 0.4,
                },
            ]
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["resolved"]) == 1
    assert body["resolved"][0]["canonical_entity_id"] == "concept-machine-learning"
    assert len(body["unresolved"]) == 1
    assert body["unresolved"][0]["source_entity_id"] == "entity-2"
