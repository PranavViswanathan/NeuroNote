from __future__ import annotations

from pathlib import Path

from app.media.storage import MediaStorage


class LocalDiskMediaStorage(MediaStorage):
    def __init__(self, root_dir: Path) -> None:
        self._root_dir = root_dir
        self._root_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, relative_path: str) -> Path:
        candidate = (self._root_dir / relative_path).resolve()
        root = self._root_dir.resolve()
        if root != candidate and root not in candidate.parents:
            raise ValueError("Invalid media path")
        return candidate

    def save_bytes(self, *, relative_path: str, content: bytes) -> None:
        destination = self._resolve_path(relative_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)

    def read_bytes(self, *, relative_path: str) -> bytes:
        return self._resolve_path(relative_path).read_bytes()

    def delete(self, *, relative_path: str) -> None:
        path = self._resolve_path(relative_path)
        if path.exists():
            path.unlink()

    def exists(self, *, relative_path: str) -> bool:
        return self._resolve_path(relative_path).exists()

    def absolute_path(self, *, relative_path: str) -> Path:
        return self._resolve_path(relative_path)
