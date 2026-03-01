from __future__ import annotations

from datetime import UTC, datetime
from threading import Lock
from uuid import uuid4

from shared.contracts.python.v1.process import ProcessStatusResponse

_JOB_STORE: dict[str, ProcessStatusResponse] = {}
_LOCK = Lock()


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def create_job() -> ProcessStatusResponse:
    now = _utc_now_iso()
    record = ProcessStatusResponse(
        job_id=str(uuid4()),
        status="queued",
        created_at=now,
        updated_at=now,
        error=None,
    )
    with _LOCK:
        _JOB_STORE[record.job_id] = record
    return record


def get_job(job_id: str) -> ProcessStatusResponse | None:
    with _LOCK:
        return _JOB_STORE.get(job_id)
