from __future__ import annotations

from datetime import UTC, datetime
from threading import Lock
from uuid import uuid4

from shared.contracts.python.v1.process import ProcessStatusResponse

_JOB_STORE: dict[str, ProcessStatusResponse] = {}
_NOTE_VERSION_INDEX: dict[tuple[str, str], str] = {}
_LOCK = Lock()


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _create_job_record() -> ProcessStatusResponse:
    now = _utc_now_iso()
    return ProcessStatusResponse(
        job_id=str(uuid4()),
        status="queued",
        created_at=now,
        updated_at=now,
        error=None,
    )


def reset_job_store() -> None:
    with _LOCK:
        _JOB_STORE.clear()
        _NOTE_VERSION_INDEX.clear()


def create_or_get_job(*, note_id: str, content_hash: str) -> tuple[ProcessStatusResponse, bool]:
    key = (note_id, content_hash)
    with _LOCK:
        existing_job_id = _NOTE_VERSION_INDEX.get(key)
        if existing_job_id is not None:
            existing = _JOB_STORE.get(existing_job_id)
            if existing is not None and existing.status != "failed":
                return existing, False

        record = _create_job_record()
        _JOB_STORE[record.job_id] = record
        _NOTE_VERSION_INDEX[key] = record.job_id
        return record, True


def _transition_job(
    *,
    job_id: str,
    status: str,
    error: str | None,
) -> ProcessStatusResponse | None:
    with _LOCK:
        record = _JOB_STORE.get(job_id)
        if record is None:
            return None

        updated = record.model_copy(
            update={
                "status": status,
                "updated_at": _utc_now_iso(),
                "error": error,
            }
        )
        _JOB_STORE[job_id] = updated
        return updated


def mark_job_running(job_id: str) -> ProcessStatusResponse | None:
    return _transition_job(job_id=job_id, status="running", error=None)


def mark_job_completed(job_id: str) -> ProcessStatusResponse | None:
    return _transition_job(job_id=job_id, status="completed", error=None)


def mark_job_failed(job_id: str, *, error: str) -> ProcessStatusResponse | None:
    return _transition_job(job_id=job_id, status="failed", error=error)


def get_job(job_id: str) -> ProcessStatusResponse | None:
    with _LOCK:
        return _JOB_STORE.get(job_id)
