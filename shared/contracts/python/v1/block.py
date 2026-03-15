from __future__ import annotations

from pydantic import BaseModel, Field


class BlockNode(BaseModel):
    block_uid: str = Field(min_length=1)
    note_id: str = Field(min_length=1)
    parent_block_uid: str | None = None
    sibling_order: int = Field(ge=0)
    block_index: int = Field(ge=0)
    content_text: str
    rich_content: dict[str, object]


class ListBlocksResponse(BaseModel):
    items: list[BlockNode]


class BlockSearchItem(BaseModel):
    block_uid: str = Field(min_length=1)
    note_id: str = Field(min_length=1)
    note_title: str = Field(min_length=1)
    content_text: str


class BlockSearchResponse(BaseModel):
    items: list[BlockSearchItem]


class BlockBacklinkItem(BaseModel):
    source_block_uid: str = Field(min_length=1)
    source_note_id: str = Field(min_length=1)
    source_note_title: str = Field(min_length=1)
    snippet: str
    updated_at: str = Field(min_length=1)


class BlockBacklinksResponse(BaseModel):
    block_uid: str = Field(min_length=1)
    items: list[BlockBacklinkItem]

