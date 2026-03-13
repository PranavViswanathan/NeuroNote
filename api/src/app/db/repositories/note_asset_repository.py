from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.note_asset import NoteAsset


@dataclass(slots=True)
class NoteAssetRecord:
    asset_id: str
    note_id: str
    mime_type: str
    file_ext: str
    byte_size: int
    relative_path: str
    deleted_at: datetime | None


class NoteAssetRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_asset(
        self,
        *,
        asset_id: str,
        note_id: str,
        mime_type: str,
        file_ext: str,
        byte_size: int,
        relative_path: str,
    ) -> NoteAssetRecord:
        row = NoteAsset(
            asset_id=asset_id,
            note_id=note_id,
            mime_type=mime_type,
            file_ext=file_ext,
            byte_size=byte_size,
            relative_path=relative_path,
            deleted_at=None,
        )
        self._session.add(row)
        self._session.flush()
        return self._to_record(row)

    def get_asset(self, asset_id: str) -> NoteAssetRecord | None:
        row = self._session.get(NoteAsset, asset_id)
        if row is None:
            return None
        return self._to_record(row)

    def list_assets_for_note(self, note_id: str) -> list[NoteAssetRecord]:
        rows = self._session.execute(
            select(NoteAsset)
            .where(NoteAsset.note_id == note_id)
            .order_by(NoteAsset.asset_id.asc())
        ).scalars().all()
        return [self._to_record(row) for row in rows]

    def list_active_assets_for_note(self, note_id: str) -> list[NoteAssetRecord]:
        rows = self._session.execute(
            select(NoteAsset)
            .where(
                NoteAsset.note_id == note_id,
                NoteAsset.deleted_at.is_(None),
            )
            .order_by(NoteAsset.asset_id.asc())
        ).scalars().all()
        return [self._to_record(row) for row in rows]

    def mark_deleted(self, asset_id: str) -> bool:
        row = self._session.get(NoteAsset, asset_id)
        if row is None:
            return False
        if row.deleted_at is None:
            row.deleted_at = datetime.now(UTC)
            self._session.flush()
        return True

    def mark_deleted_many(self, asset_ids: set[str]) -> int:
        if not asset_ids:
            return 0
        updated = 0
        rows = self._session.execute(
            select(NoteAsset).where(NoteAsset.asset_id.in_(asset_ids))
        ).scalars().all()
        for row in rows:
            if row.deleted_at is None:
                row.deleted_at = datetime.now(UTC)
                updated += 1
        self._session.flush()
        return updated

    def list_by_ids(self, asset_ids: set[str]) -> list[NoteAssetRecord]:
        if not asset_ids:
            return []
        rows = self._session.execute(
            select(NoteAsset)
            .where(NoteAsset.asset_id.in_(asset_ids))
            .order_by(NoteAsset.asset_id.asc())
        ).scalars().all()
        return [self._to_record(row) for row in rows]

    def _to_record(self, row: NoteAsset) -> NoteAssetRecord:
        return NoteAssetRecord(
            asset_id=row.asset_id,
            note_id=row.note_id,
            mime_type=row.mime_type,
            file_ext=row.file_ext,
            byte_size=row.byte_size,
            relative_path=row.relative_path,
            deleted_at=row.deleted_at,
        )
