from __future__ import annotations

from pathlib import Path
from typing import Protocol


class MediaStorage(Protocol):
    def save_bytes(self, *, relative_path: str, content: bytes) -> None:
        ...

    def read_bytes(self, *, relative_path: str) -> bytes:
        ...

    def delete(self, *, relative_path: str) -> None:
        ...

    def exists(self, *, relative_path: str) -> bool:
        ...

    def absolute_path(self, *, relative_path: str) -> Path:
        ...
