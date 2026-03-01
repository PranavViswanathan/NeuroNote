from __future__ import annotations

from pydantic import BaseModel, Field


class SaveNoteRequest(BaseModel):
    note_id: str = Field(min_length=1)
    content_json: dict[str, object] = Field(min_length=1)
    content_text: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class SaveNoteResponse(BaseModel):
    note_id: str = Field(min_length=1)
    saved_at: str = Field(min_length=1)
    version: int = Field(ge=1)


class GetNoteResponse(BaseModel):
    note_id: str = Field(min_length=1)
    content_json: dict[str, object] = Field(min_length=1)
    content_text: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)
    version: int = Field(ge=1)


class NoteSummary(BaseModel):
    note_id: str = Field(min_length=1)
    content_text: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)
    version: int = Field(ge=1)


class ListNotesResponse(BaseModel):
    items: list[NoteSummary]
    total: int = Field(ge=0)
