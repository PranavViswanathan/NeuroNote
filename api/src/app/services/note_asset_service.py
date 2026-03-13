from __future__ import annotations

from functools import lru_cache
import uuid

from sqlalchemy import inspect, text
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.repositories.note_asset_repository import NoteAssetRepository, NoteAssetRecord
from app.media.config import get_media_settings
from app.media.local_storage import LocalDiskMediaStorage
from app.media.references import extract_asset_ids_from_doc
from app.media.storage import MediaStorage

_ALLOWED_MIME_TO_EXT: dict[str, str] = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
    "image/gif": "gif",
}


@lru_cache(maxsize=1)
def get_media_storage() -> MediaStorage:
    settings = get_media_settings()
    return LocalDiskMediaStorage(settings.root_dir)


def reset_media_storage() -> None:
    get_media_storage.cache_clear()


def note_assets_table_exists(session: Session) -> bool:
    bind = session.get_bind()
    try:
        if bind.dialect.name == "postgresql":
            # Use an explicit schema-qualified probe to avoid search_path ambiguity.
            regclass = session.execute(
                text("SELECT to_regclass('public.note_assets')"),
            ).scalar_one_or_none()
            return bool(regclass)
        return bool(inspect(bind).has_table("note_assets"))
    except SQLAlchemyError:
        return False


def allowed_image_mime_types() -> set[str]:
    return set(_ALLOWED_MIME_TO_EXT.keys())


def extension_for_mime(mime_type: str) -> str | None:
    return _ALLOWED_MIME_TO_EXT.get(mime_type)


def create_asset_identity(note_id: str, mime_type: str) -> tuple[str, str, str]:
    asset_id = uuid.uuid4().hex
    extension = extension_for_mime(mime_type)
    if extension is None:
        raise ValueError("Unsupported mime type")
    relative_path = f"{note_id}/{asset_id}.{extension}"
    return asset_id, extension, relative_path


def _is_missing_note_assets_error(exc: ProgrammingError) -> bool:
    error_text = str(getattr(exc, "orig", exc)).lower()
    return "note_assets" in error_text and (
        "does not exist" in error_text
        or "undefinedtable" in error_text
        or "no such table" in error_text
    )


def reconcile_note_assets_for_note(
    *,
    note_id: str,
    content_json: dict[str, object],
    session: Session,
) -> list[NoteAssetRecord]:
    if not note_assets_table_exists(session):
        return []

    repository = NoteAssetRepository(session)
    referenced_asset_ids = extract_asset_ids_from_doc(content_json)
    try:
        active_assets = repository.list_active_assets_for_note(note_id)
    except ProgrammingError as exc:
        if _is_missing_note_assets_error(exc):
            return []
        raise

    active_ids = {asset.asset_id for asset in active_assets}
    to_delete_ids = active_ids - referenced_asset_ids
    if not to_delete_ids:
        return []

    to_delete = [asset for asset in active_assets if asset.asset_id in to_delete_ids]
    repository.mark_deleted_many(to_delete_ids)

    storage = get_media_storage()
    for asset in to_delete:
        storage.delete(relative_path=asset.relative_path)

    return to_delete
