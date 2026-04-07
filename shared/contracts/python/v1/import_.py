from __future__ import annotations

from pydantic import BaseModel, Field


class ImportNoteRequest(BaseModel):
    filename: str = Field(min_length=1)
    content: str = Field(min_length=1)
    subject_id: str = Field(default="inbox", min_length=1)


class ImportNoteResponse(BaseModel):
    note_id: str
    note_title: str
    saved_at: str
