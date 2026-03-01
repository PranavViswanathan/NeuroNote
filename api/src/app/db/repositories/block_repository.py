from __future__ import annotations

import hashlib

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db.models.block import Block


def _extract_plain_text(node: object) -> str:
    if isinstance(node, dict):
        text_value = node.get("text")
        if isinstance(text_value, str):
            return text_value
        content = node.get("content")
        if isinstance(content, list):
            return "".join(_extract_plain_text(item) for item in content)
        return ""
    if isinstance(node, list):
        return "".join(_extract_plain_text(item) for item in node)
    return ""


def _extract_blocks(content_json: dict[str, object], *, fallback_text: str) -> list[tuple[int, dict[str, object], str]]:
    raw_content = content_json.get("content")
    if not isinstance(raw_content, list):
        return [(0, content_json, fallback_text)]

    blocks: list[tuple[int, dict[str, object], str]] = []
    for block_index, node in enumerate(raw_content):
        if not isinstance(node, dict):
            continue
        block_text = _extract_plain_text(node).strip()
        blocks.append((block_index, node, block_text))

    if blocks:
        return blocks
    return [(0, content_json, fallback_text)]


class BlockRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def replace_blocks(
        self,
        *,
        note_id: str,
        content_json: dict[str, object],
        fallback_text: str,
    ) -> None:
        self._session.execute(delete(Block).where(Block.note_id == note_id))

        for block_index, rich_content, block_text in _extract_blocks(
            content_json,
            fallback_text=fallback_text,
        ):
            block_hash = hashlib.sha256(block_text.encode("utf-8")).hexdigest()
            self._session.add(
                Block(
                    note_id=note_id,
                    block_index=block_index,
                    content_text=block_text,
                    content_hash=block_hash,
                    rich_content=rich_content,
                )
            )
