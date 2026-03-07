from __future__ import annotations

from dataclasses import dataclass
import hashlib

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.note import Note
from app.db.models.subject import Subject
from app.db.repositories.block_repository import BlockRepository

DEFAULT_SUBJECT_ID = "inbox"
DEFAULT_SUBJECT_NAME = "Inbox"


@dataclass(slots=True)
class NoteRecord:
    note_id: str
    content_json: dict[str, object]
    content_text: str
    content_hash: str
    updated_at: str
    version: int


@dataclass(slots=True)
class NoteSummaryRecord:
    note_id: str
    content_text: str
    updated_at: str
    version: int


class NoteRepository:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._blocks = BlockRepository(session)

    def _ensure_default_subject(self) -> None:
        default_subject = self._session.get(Subject, DEFAULT_SUBJECT_ID)
        if default_subject is not None:
            return
        self._session.add(
            Subject(
                id=DEFAULT_SUBJECT_ID,
                name=DEFAULT_SUBJECT_NAME,
            )
        )
        self._session.flush()

    def upsert_note(
        self,
        *,
        note_id: str,
        content_json: dict[str, object],
        content_text: str,
        updated_at: str,
    ) -> NoteRecord:
        self._ensure_default_subject()

        existing = self._session.execute(
            select(Note).where(Note.note_id == note_id),
        ).scalar_one_or_none()

        content_hash = hashlib.sha256(content_text.encode("utf-8")).hexdigest()
        if existing is None:
            existing = Note(
                note_id=note_id,
                subject_id=DEFAULT_SUBJECT_ID,
                content_json=content_json,
                content_text=content_text,
                content_hash=content_hash,
                updated_at=updated_at,
                version=1,
            )
            self._session.add(existing)
        else:
            existing.content_json = content_json
            existing.content_text = content_text
            existing.content_hash = content_hash
            existing.updated_at = updated_at
            existing.version += 1

        self._session.flush()
        self._blocks.replace_blocks(
            note_id=note_id,
            content_json=content_json,
            fallback_text=content_text,
        )

        return NoteRecord(
            note_id=existing.note_id,
            content_json=dict(existing.content_json),
            content_text=existing.content_text,
            content_hash=existing.content_hash,
            updated_at=existing.updated_at,
            version=existing.version,
        )

    def get_note(self, note_id: str) -> NoteRecord | None:
        existing = self._session.execute(
            select(Note).where(Note.note_id == note_id),
        ).scalar_one_or_none()
        if existing is None:
            return None

        return NoteRecord(
            note_id=existing.note_id,
            content_json=dict(existing.content_json),
            content_text=existing.content_text,
            content_hash=existing.content_hash,
            updated_at=existing.updated_at,
            version=existing.version,
        )

    def list_notes(self, *, limit: int, offset: int) -> tuple[list[NoteSummaryRecord], int]:
        rows = self._session.execute(
            select(Note)
            .order_by(Note.saved_at.desc(), Note.note_id.asc())
            .limit(limit)
            .offset(offset),
        ).scalars()

        total = self._session.execute(
            select(func.count()).select_from(Note),
        ).scalar_one()

        items = [
            NoteSummaryRecord(
                note_id=row.note_id,
                content_text=row.content_text,
                updated_at=row.updated_at,
                version=row.version,
            )
            for row in rows
        ]
        return items, int(total)

    def delete_note(self, note_id: str) -> bool:
        existing = self._session.get(Note, note_id)
        if existing is None:
            return False

        self._session.delete(existing)
        self._session.flush()
        return True
