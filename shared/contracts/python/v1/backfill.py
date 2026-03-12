from __future__ import annotations

from pydantic import BaseModel, Field


class BackfillStatusResponse(BaseModel):
    total_notes: int = Field(ge=0)
    processed_notes: int = Field(ge=0)
    failed_notes: int = Field(ge=0)
    in_progress: bool

