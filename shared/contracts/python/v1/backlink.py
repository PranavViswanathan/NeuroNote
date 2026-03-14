from __future__ import annotations

from pydantic import BaseModel, Field


class BacklinkItem(BaseModel):
    source_note_id: str = Field(min_length=1)
    source_note_title: str = Field(min_length=1)
    matched_title: str = Field(min_length=1)
    snippet: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class BacklinksResponse(BaseModel):
    note_id: str = Field(min_length=1)
    items: list[BacklinkItem]
