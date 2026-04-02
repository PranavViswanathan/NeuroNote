"""Job store with Postgres persistence and in-memory fallback.

When a Postgres DATABASE_URL is configured, all job state is written to the
`processing_jobs` table so it survives container restarts. On startup the API
calls `mark_stale_jobs_as_failed()` to clean up any jobs that were in-progress
when the previous instance died.

For SQLite (tests / local dev without Postgres), the pure in-memory store is
used unchanged.
"""
from __future__ import annotations

from datetime import UTC, datetime
from threading import Lock
from uuid import uuid4

from sqlalchemy import text

from app.db.config import get_database_settings
from shared.contracts.python.v1.process import ProcessStatusResponse

_JOB_STORE: dict[str, ProcessStatusResponse] = {}
_NOTE_VERSION_INDEX: dict[tuple[str, str], str] = {}
_LOCK = Lock()


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _is_postgres() -> bool:
    return get_database_settings().database_url.startswith("postgresql")


def _get_session():  # type: ignore[return]
    from app.db.engine import get_session_factory
    return get_session_factory()()


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
    """Clear in-memory store (used by tests)."""
    with _LOCK:
        _JOB_STORE.clear()
        _NOTE_VERSION_INDEX.clear()


def mark_stale_jobs_as_failed() -> None:
    """Mark any running/queued jobs as failed on startup.

    Call this once during app lifespan startup to clean up jobs that were
    in-progress when the previous worker process died.
    Only runs on Postgres; in-memory store is always clean on startup.
    """
    if not _is_postgres():
        return
    try:
        with _get_session() as session:
            with session.begin():
                session.execute(
                    text(
                        """
                        UPDATE public.processing_jobs
                        SET status = 'failed',
                            error = 'Worker restarted — job was interrupted',
                            updated_at = NOW()
                        WHERE status IN ('queued', 'running')
                        """
                    )
                )
    except Exception:
        pass  # DB may not have the table yet (pre-migration); safe to ignore


# ── Postgres path ─────────────────────────────────────────────────────────────

def _pg_create_or_get_job(*, note_id: str, content_hash: str) -> tuple[ProcessStatusResponse, bool]:
    with _get_session() as session:
        with session.begin():
            existing_row = session.execute(
                text(
                    """
                    SELECT job_id, status, error, created_at, updated_at
                    FROM public.processing_jobs
                    WHERE note_id = :note_id AND content_hash = :content_hash
                      AND status NOT IN ('failed')
                    ORDER BY created_at DESC
                    LIMIT 1
                    """
                ),
                {"note_id": note_id, "content_hash": content_hash},
            ).first()

            if existing_row is not None:
                return ProcessStatusResponse(
                    job_id=str(existing_row[0]),
                    status=str(existing_row[1]),
                    error=str(existing_row[2]) if existing_row[2] else None,
                    created_at=str(existing_row[3]),
                    updated_at=str(existing_row[4]),
                ), False

            job_id = str(uuid4())
            now = _utc_now_iso()
            session.execute(
                text(
                    """
                    INSERT INTO public.processing_jobs
                        (job_id, note_id, content_hash, status, created_at, updated_at)
                    VALUES (:job_id, :note_id, :content_hash, 'queued', NOW(), NOW())
                    """
                ),
                {"job_id": job_id, "note_id": note_id, "content_hash": content_hash},
            )
            return ProcessStatusResponse(
                job_id=job_id,
                status="queued",
                created_at=now,
                updated_at=now,
                error=None,
            ), True


def _pg_transition_job(*, job_id: str, status: str, error: str | None) -> ProcessStatusResponse | None:
    with _get_session() as session:
        with session.begin():
            row = session.execute(
                text(
                    """
                    UPDATE public.processing_jobs
                    SET status = :status, error = :error, updated_at = NOW()
                    WHERE job_id = :job_id
                    RETURNING job_id, status, error, created_at, updated_at
                    """
                ),
                {"job_id": job_id, "status": status, "error": error},
            ).first()
    if row is None:
        return None
    return ProcessStatusResponse(
        job_id=str(row[0]),
        status=str(row[1]),
        error=str(row[2]) if row[2] else None,
        created_at=str(row[3]),
        updated_at=str(row[4]),
    )


def _pg_get_job(job_id: str) -> ProcessStatusResponse | None:
    with _get_session() as session:
        row = session.execute(
            text(
                """
                SELECT job_id, status, error, created_at, updated_at
                FROM public.processing_jobs
                WHERE job_id = :job_id
                """
            ),
            {"job_id": job_id},
        ).first()
    if row is None:
        return None
    return ProcessStatusResponse(
        job_id=str(row[0]),
        status=str(row[1]),
        error=str(row[2]) if row[2] else None,
        created_at=str(row[3]),
        updated_at=str(row[4]),
    )


# ── In-memory path (SQLite / tests) ──────────────────────────────────────────

def _mem_create_or_get_job(*, note_id: str, content_hash: str) -> tuple[ProcessStatusResponse, bool]:
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


def _mem_transition_job(*, job_id: str, status: str, error: str | None) -> ProcessStatusResponse | None:
    with _LOCK:
        record = _JOB_STORE.get(job_id)
        if record is None:
            return None
        updated = record.model_copy(update={"status": status, "updated_at": _utc_now_iso(), "error": error})
        _JOB_STORE[job_id] = updated
        return updated


def _mem_get_job(job_id: str) -> ProcessStatusResponse | None:
    with _LOCK:
        return _JOB_STORE.get(job_id)


# ── Public API ────────────────────────────────────────────────────────────────

def create_or_get_job(*, note_id: str, content_hash: str) -> tuple[ProcessStatusResponse, bool]:
    if _is_postgres():
        return _pg_create_or_get_job(note_id=note_id, content_hash=content_hash)
    return _mem_create_or_get_job(note_id=note_id, content_hash=content_hash)


def _transition_job(*, job_id: str, status: str, error: str | None) -> ProcessStatusResponse | None:
    if _is_postgres():
        return _pg_transition_job(job_id=job_id, status=status, error=error)
    return _mem_transition_job(job_id=job_id, status=status, error=error)


def mark_job_running(job_id: str) -> ProcessStatusResponse | None:
    return _transition_job(job_id=job_id, status="running", error=None)


def mark_job_completed(job_id: str) -> ProcessStatusResponse | None:
    return _transition_job(job_id=job_id, status="completed", error=None)


def mark_job_failed(job_id: str, *, error: str) -> ProcessStatusResponse | None:
    return _transition_job(job_id=job_id, status="failed", error=error)


def get_job(job_id: str) -> ProcessStatusResponse | None:
    if _is_postgres():
        return _pg_get_job(job_id)
    return _mem_get_job(job_id)
