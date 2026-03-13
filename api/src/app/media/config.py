from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


def _as_int(raw: str | None, *, default: int) -> int:
    if raw is None:
        return default
    value = raw.strip()
    if not value:
        return default
    try:
        parsed = int(value)
    except ValueError:
        return default
    if parsed <= 0:
        return default
    return parsed


@dataclass(frozen=True, slots=True)
class MediaSettings:
    root_dir: Path
    max_upload_bytes: int


def get_media_settings() -> MediaSettings:
    root = Path(os.getenv("MEDIA_ROOT_DIR", "api/media")).resolve()
    max_bytes = _as_int(os.getenv("MEDIA_MAX_UPLOAD_BYTES"), default=10 * 1024 * 1024)
    return MediaSettings(root_dir=root, max_upload_bytes=max_bytes)
