"""Note import service.

Handles file-content parsing, note ID generation, plain-text extraction,
and note persistence for the import endpoint.  FastAPI concerns (BackgroundTasks,
HTTPException) remain in the route layer.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.db.repositories.note_repository import NoteRepository
from app.import_.markdown_parser import (
    extract_title_from_markdown,
    parse_markdown_to_tiptap,
    parse_plaintext_to_tiptap,
)


class UnsupportedFileTypeError(ValueError):
    """Raised when the imported file extension is not recognised."""


@dataclass(frozen=True, slots=True)
class ImportedNote:
    note_id: str
    note_title: str
    content_hash: str
    updated_at: str
    content_text: str


class NoteImportService:
    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def parse_content(content: str, *, ext: str) -> tuple[dict[str, object], str]:
        """Parse raw file content into (tiptap_json, title).

        Raises UnsupportedFileTypeError for unrecognised extensions.
        """
        if ext == "md":
            content_json = parse_markdown_to_tiptap(content)
            title = extract_title_from_markdown(content)
        elif ext in ("txt", ""):
            content_json = parse_plaintext_to_tiptap(content)
            first_line = content.strip().split("\n")[0].strip()
            title = first_line[:120] if first_line else "Untitled"
        else:
            raise UnsupportedFileTypeError(
                f"Unsupported file type: .{ext}. Only .md and .txt are supported."
            )
        return content_json, title

    @staticmethod
    def extract_plain_text(content_json: dict[str, object]) -> str:
        """Flatten TipTap JSON to a plain-text string for search indexing."""
        parts: list[str] = []
        nodes = content_json.get("content", [])
        if not isinstance(nodes, list):
            return " "
        for node in nodes:
            if not isinstance(node, dict):
                continue
            for child in node.get("content", []):
                if not isinstance(child, dict):
                    continue
                if child.get("type") == "text":
                    text = child.get("text", "")
                    if isinstance(text, str):
                        parts.append(text)
        return " ".join(parts).strip() or " "

    def import_note(
        self,
        *,
        filename: str,
        content: str,
        subject_id: str,
    ) -> ImportedNote:
        """Parse, persist, and return metadata for a newly imported note."""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        content_json, title = self.parse_content(content, ext=ext)
        plain_text = self.extract_plain_text(content_json)
        note_id = f"note-{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(UTC).isoformat()

        saved = NoteRepository(self._session).upsert_note(
            note_id=note_id,
            note_title=title,
            subject_id=subject_id,
            tags=[],
            is_pinned=False,
            is_archived=False,
            content_json=content_json,
            content_text=plain_text,
            updated_at=now_iso,
        )
        return ImportedNote(
            note_id=note_id,
            note_title=title,
            content_hash=saved.content_hash,
            updated_at=now_iso,
            content_text=plain_text,
        )
