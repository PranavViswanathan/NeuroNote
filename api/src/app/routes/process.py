from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.job_store import (
    create_or_get_job,
    get_job,
    mark_job_completed,
    mark_job_failed,
    mark_job_running,
)
from app.db.repositories.note_repository import NoteRepository
from app.db.session import get_db_session
from app.services.note_processing_service import NoteNotFoundError, NoteProcessingService
from shared.contracts.python.v1.process import (
    ProcessNoteRequest,
    ProcessNoteResponse,
    ProcessStatusResponse,
)

router = APIRouter()


def _run_processing_job(*, job_id: str, payload: ProcessNoteRequest) -> None:
    mark_job_running(job_id)
    try:
        NoteProcessingService().process_note(payload)
    except NoteNotFoundError as exc:
        mark_job_failed(job_id, error=str(exc))
        return
    except Exception as exc:  # pragma: no cover - defensive runtime guard
        mark_job_failed(job_id, error=str(exc))
        return

    mark_job_completed(job_id)


@router.post(
    "/process-note",
    response_model=ProcessNoteResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def process_note(
    payload: ProcessNoteRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db_session),
) -> ProcessNoteResponse:
    note = NoteRepository(session).get_note(payload.note_id)
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note {payload.note_id} was not found",
        )

    record, created = create_or_get_job(
        note_id=payload.note_id,
        content_hash=payload.content_hash,
    )
    if created:
        background_tasks.add_task(_run_processing_job, job_id=record.job_id, payload=payload)

    return ProcessNoteResponse(job_id=record.job_id, status="queued")


@router.get("/process-status/{job_id}", response_model=ProcessStatusResponse)
def process_status(job_id: str) -> ProcessStatusResponse:
    record = get_job(job_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} was not found",
        )
    return record
