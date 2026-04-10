"""Export service.

Encapsulates TipTap document transformation and ZIP archive assembly
for the markdown export endpoint.
"""
from __future__ import annotations

import io
import zipfile
from copy import deepcopy

from sqlalchemy.orm import Session

from app.db.repositories.note_asset_repository import NoteAssetRecord, NoteAssetRepository
from app.db.repositories.note_repository import NoteRepository
from app.export.markdown import render_note_markdown
from app.media.references import extract_asset_ids_from_doc
from app.services.note_asset_service import get_media_storage, note_assets_table_exists


class NoteNotFoundError(LookupError):
    """Raised when the requested note does not exist."""


def _as_object(value: object) -> dict[str, object] | None:
    if isinstance(value, dict):
        return value
    return None


class ExportService:
    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def hydrate_image_filenames(
        content_json: dict[str, object],
        *,
        assets_by_id: dict[str, NoteAssetRecord],
    ) -> dict[str, object]:
        """Return a deep copy of *content_json* with image node attrs enriched.

        Each ``image`` node whose ``assetId`` matches a known asset gains
        ``filename`` and ``ext`` attributes so the markdown exporter can embed
        the correct file reference.
        """
        cloned = deepcopy(content_json)

        def _walk(node: dict[str, object]) -> None:
            if str(node.get("type", "")) == "image":
                attrs = _as_object(node.get("attrs")) or {}
                asset_id = attrs.get("assetId")
                if isinstance(asset_id, str):
                    asset = assets_by_id.get(asset_id)
                    if asset is not None:
                        attrs["filename"] = f"{asset.asset_id}.{asset.file_ext}"
                        attrs["ext"] = asset.file_ext
                node["attrs"] = attrs

            raw_content = node.get("content")
            if isinstance(raw_content, list):
                for item in raw_content:
                    child = _as_object(item)
                    if child is not None:
                        _walk(child)

        root = _as_object(cloned)
        if root is not None:
            _walk(root)
        return cloned

    def build_markdown_zip(self, note_id: str) -> bytes:
        """Render a note to markdown and bundle it with its assets into a ZIP.

        Raises NoteNotFoundError when the note does not exist.
        """
        note = NoteRepository(self._session).get_note(note_id)
        if note is None:
            raise NoteNotFoundError(f"Note {note_id} was not found")

        assets_by_id: dict[str, NoteAssetRecord] = {}
        if note_assets_table_exists(self._session):
            referenced_ids = extract_asset_ids_from_doc(note.content_json)
            assets = NoteAssetRepository(self._session).list_by_ids(referenced_ids)
            assets_by_id = {a.asset_id: a for a in assets if a.deleted_at is None}

        hydrated = self.hydrate_image_filenames(note.content_json, assets_by_id=assets_by_id)
        markdown = render_note_markdown(hydrated)

        storage = get_media_storage()
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("note.md", markdown)
            for asset in assets_by_id.values():
                if not storage.exists(relative_path=asset.relative_path):
                    continue
                filename = f"{asset.asset_id}.{asset.file_ext}"
                archive.writestr(
                    f"assets/{filename}",
                    storage.read_bytes(relative_path=asset.relative_path),
                )
        return buffer.getvalue()
