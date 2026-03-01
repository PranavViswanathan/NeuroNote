from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from threading import Lock


@dataclass(slots=True)
class StoredNote:
    note_id: str
    content_json: dict[str, object]
    content_text: str
    updated_at: str
    version: int


_NOTE_STORE: dict[str, StoredNote] = {}
_LOCK = Lock()


def upsert_note(
    note_id: str,
    content_json: dict[str, object],
    content_text: str,
    updated_at: str,
) -> StoredNote:
    with _LOCK:
        existing = _NOTE_STORE.get(note_id)
        next_version = 1 if existing is None else existing.version + 1
        record = StoredNote(
            note_id=note_id,
            content_json=deepcopy(content_json),
            content_text=content_text,
            updated_at=updated_at,
            version=next_version,
        )
        _NOTE_STORE[note_id] = record
        return record


def get_note(note_id: str) -> StoredNote | None:
    with _LOCK:
        record = _NOTE_STORE.get(note_id)
        if record is None:
            return None
        return StoredNote(
            note_id=record.note_id,
            content_json=deepcopy(record.content_json),
            content_text=record.content_text,
            updated_at=record.updated_at,
            version=record.version,
        )
