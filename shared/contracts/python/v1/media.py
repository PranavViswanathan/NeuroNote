from __future__ import annotations

from pydantic import BaseModel, Field


class UploadImageRequest(BaseModel):
    note_id: str = Field(min_length=1)
    filename: str = Field(min_length=1)
    mime_type: str = Field(min_length=1)
    content_base64: str = Field(min_length=1)


class UploadImageResponse(BaseModel):
    asset_id: str = Field(min_length=1)
    note_id: str = Field(min_length=1)
    src: str = Field(min_length=1)
    mime_type: str = Field(min_length=1)
    byte_size: int = Field(ge=1)


class DeleteImageResponse(BaseModel):
    asset_id: str = Field(min_length=1)
    deleted: bool
