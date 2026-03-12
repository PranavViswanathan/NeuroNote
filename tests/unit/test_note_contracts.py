from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from shared.contracts.python.v1.note import (
    GetNoteResponse,
    ListNotesResponse,
    NoteSummary,
    SaveNoteRequest,
    SaveNoteResponse,
)

ROOT = Path(__file__).resolve().parents[2]


def test_save_note_request_accepts_valid_payload() -> None:
    request = SaveNoteRequest(
        note_id="note-1",
        note_title="Graph foundations",
        content_json={"type": "doc", "content": []},
        content_text="Knowledge graph note",
        updated_at="2026-03-01T10:00:00Z",
    )
    assert request.note_id == "note-1"


def test_save_note_request_rejects_empty_note_id() -> None:
    with pytest.raises(ValidationError):
        SaveNoteRequest(
            note_id="",
            note_title="Graph foundations",
            content_json={"type": "doc", "content": []},
            content_text="Knowledge graph note",
            updated_at="2026-03-01T10:00:00Z",
        )


def test_save_note_response_shape() -> None:
    response = SaveNoteResponse(
        note_id="note-1",
        saved_at="2026-03-01T10:00:00Z",
        version=1,
    )
    assert response.version == 1


def test_get_note_response_shape() -> None:
    response = GetNoteResponse(
        note_id="note-1",
        note_title="Graph foundations",
        content_json={"type": "doc", "content": []},
        content_text="Knowledge graph note",
        updated_at="2026-03-01T10:00:00Z",
        version=1,
    )
    assert response.note_id == "note-1"


def test_list_notes_response_shape() -> None:
    response = ListNotesResponse(
        items=[
            NoteSummary(
                note_id="note-1",
                note_title="Graph foundations",
                content_text="Knowledge graph note",
                updated_at="2026-03-01T10:00:00Z",
                version=1,
            )
        ],
        total=1,
    )
    assert response.total == 1


def test_ts_note_contract_contains_required_fields() -> None:
    ts_contract = (ROOT / "shared/contracts/ts/v1/note.ts").read_text()
    required_tokens = [
        "interface SaveNoteRequest",
        "note_id: string",
        "note_title: string",
        "content_json: Record<string, unknown>",
        "content_text: string",
        "updated_at: string",
        "interface SaveNoteResponse",
        "saved_at: string",
        "version: number",
        "interface GetNoteResponse",
        "interface NoteSummary",
        "interface ListNotesResponse",
        "items: NoteSummary[]",
        "total: number",
    ]

    for token in required_tokens:
        assert token in ts_contract, f"Missing token in TS note contract: {token}"
