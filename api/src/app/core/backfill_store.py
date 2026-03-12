from __future__ import annotations

from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True, slots=True)
class BackfillStatusSnapshot:
    total_notes: int
    processed_notes: int
    failed_notes: int
    in_progress: bool


_STATUS = BackfillStatusSnapshot(
    total_notes=0,
    processed_notes=0,
    failed_notes=0,
    in_progress=False,
)
_LOCK = Lock()


def reset_backfill_status() -> None:
    global _STATUS
    with _LOCK:
        _STATUS = BackfillStatusSnapshot(
            total_notes=0,
            processed_notes=0,
            failed_notes=0,
            in_progress=False,
        )


def get_backfill_status() -> BackfillStatusSnapshot:
    with _LOCK:
        return _STATUS


def set_backfill_status(snapshot: BackfillStatusSnapshot) -> None:
    global _STATUS
    with _LOCK:
        _STATUS = snapshot

