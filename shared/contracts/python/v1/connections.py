from __future__ import annotations

from pydantic import BaseModel, Field


class NoteConnectionItem(BaseModel):
    related_note_id: str = Field(min_length=1)
    related_note_title: str
    strength: float = Field(ge=0.0, le=1.0)
    via_concepts: list[str] = Field(default_factory=list)


class NoteConnectionsResponse(BaseModel):
    note_id: str = Field(min_length=1)
    connections: list[NoteConnectionItem]
