from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status

from app.core.note_store import get_note, upsert_note
from shared.contracts.python.v1.note import (
    GetNoteResponse,
    SaveNoteRequest,
    SaveNoteResponse,
)

router = APIRouter()


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


@router.put("/notes/{note_id}", response_model=SaveNoteResponse)
def put_note(note_id: str, payload: SaveNoteRequest) -> SaveNoteResponse:
    if note_id != payload.note_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path note_id must match payload note_id",
        )

    record = upsert_note(
        note_id=payload.note_id,
        content_json=payload.content_json,
        content_text=payload.content_text,
        updated_at=payload.updated_at,
    )
    return SaveNoteResponse(
        note_id=record.note_id,
        saved_at=_utc_now_iso(),
        version=record.version,
    )


@router.get("/notes/{note_id}", response_model=GetNoteResponse)
def fetch_note(note_id: str) -> GetNoteResponse:
    record = get_note(note_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note {note_id} was not found",
        )
    return GetNoteResponse(
        note_id=record.note_id,
        content_json=record.content_json,
        content_text=record.content_text,
        updated_at=record.updated_at,
        version=record.version,
    )
