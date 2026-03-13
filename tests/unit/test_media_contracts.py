from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from shared.contracts.python.v1.media import DeleteImageResponse, UploadImageResponse

ROOT = Path(__file__).resolve().parents[2]


def test_upload_image_response_accepts_valid_payload() -> None:
    payload = UploadImageResponse(
        asset_id="asset-1",
        note_id="note-1",
        src="/v1/media/asset-1",
        mime_type="image/png",
        byte_size=123,
    )
    assert payload.asset_id == "asset-1"


def test_upload_image_response_rejects_invalid_size() -> None:
    with pytest.raises(ValidationError):
        UploadImageResponse(
            asset_id="asset-1",
            note_id="note-1",
            src="/v1/media/asset-1",
            mime_type="image/png",
            byte_size=0,
        )


def test_delete_image_response_shape() -> None:
    payload = DeleteImageResponse(asset_id="asset-1", deleted=True)
    assert payload.deleted is True


def test_ts_media_contract_contains_required_fields() -> None:
    ts_contract = (ROOT / "shared/contracts/ts/v1/media.ts").read_text()
    for token in [
        "interface UploadImageRequest",
        "filename: string",
        "mime_type: string",
        "content_base64: string",
        "interface UploadImageResponse",
        "asset_id: string",
        "note_id: string",
        "src: string",
        "mime_type: string",
        "byte_size: number",
        "interface DeleteImageResponse",
        "deleted: boolean",
    ]:
        assert token in ts_contract
