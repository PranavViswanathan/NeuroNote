from __future__ import annotations

from app.db.repositories.note_asset_repository import NoteAssetRecord
from app.services.export_service import ExportService


def _asset(asset_id: str, file_ext: str) -> NoteAssetRecord:
    return NoteAssetRecord(
        asset_id=asset_id,
        note_id="note-1",
        mime_type="image/png",
        file_ext=file_ext,
        byte_size=100,
        relative_path=f"assets/{asset_id}.{file_ext}",
        deleted_at=None,
    )


class TestHydrateImageFilenames:
    def test_sets_filename_and_ext_for_known_asset(self) -> None:
        content = {
            "type": "doc",
            "content": [
                {
                    "type": "image",
                    "attrs": {"assetId": "abc123", "src": "/media/abc123"},
                }
            ],
        }
        assets_by_id = {"abc123": _asset("abc123", "png")}

        result = ExportService.hydrate_image_filenames(content, assets_by_id=assets_by_id)

        image_node = result["content"][0]  # type: ignore[index]
        assert image_node["attrs"]["filename"] == "abc123.png"  # type: ignore[index]
        assert image_node["attrs"]["ext"] == "png"  # type: ignore[index]

    def test_skips_image_node_with_unknown_asset_id(self) -> None:
        content = {
            "type": "doc",
            "content": [
                {"type": "image", "attrs": {"assetId": "unknown-id"}},
            ],
        }
        result = ExportService.hydrate_image_filenames(content, assets_by_id={})
        image_node = result["content"][0]  # type: ignore[index]
        assert "filename" not in image_node["attrs"]  # type: ignore[index]

    def test_does_not_mutate_original_document(self) -> None:
        content: dict[str, object] = {
            "type": "doc",
            "content": [
                {"type": "image", "attrs": {"assetId": "abc123"}},
            ],
        }
        original_attrs = dict(content["content"][0]["attrs"])  # type: ignore[index]
        assets_by_id = {"abc123": _asset("abc123", "jpg")}

        ExportService.hydrate_image_filenames(content, assets_by_id=assets_by_id)

        assert content["content"][0]["attrs"] == original_attrs  # type: ignore[index]

    def test_walks_nested_content_nodes(self) -> None:
        content = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "image", "attrs": {"assetId": "nested-img"}},
                    ],
                }
            ],
        }
        assets_by_id = {"nested-img": _asset("nested-img", "gif")}
        result = ExportService.hydrate_image_filenames(content, assets_by_id=assets_by_id)

        nested_image = result["content"][0]["content"][0]  # type: ignore[index]
        assert nested_image["attrs"]["filename"] == "nested-img.gif"  # type: ignore[index]

    def test_ignores_non_image_nodes(self) -> None:
        content = {
            "type": "doc",
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": "hello"}]},
            ],
        }
        result = ExportService.hydrate_image_filenames(content, assets_by_id={})
        assert result["content"][0]["type"] == "paragraph"  # type: ignore[index]
