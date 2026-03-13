from __future__ import annotations

from pydantic import BaseModel, Field


class NoteExportResponse(BaseModel):
    note_id: str = Field(min_length=1)
    filename: str = Field(min_length=1)
