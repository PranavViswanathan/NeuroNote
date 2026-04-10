"""File import endpoint — accepts markdown or plain text content and creates a note."""
from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.job_store import create_or_get_job, mark_job_completed, mark_job_failed, mark_job_running
from app.db.session import get_db_session
from app.services.note_import_service import NoteImportService, UnsupportedFileTypeError
from app.services.note_processing_service import NoteNotFoundError, NoteProcessingService
from shared.contracts.python.v1.import_ import ImportNoteRequest, ImportNoteResponse
from shared.contracts.python.v1.process import ProcessNoteRequest

router = APIRouter()
_LOG = logging.getLogger(__name__)


def _run_import_processing_job(*, job_id: str, payload: ProcessNoteRequest) -> None:
    mark_job_running(job_id)
    try:
        summary = NoteProcessingService().process_note(payload)
    except NoteNotFoundError as exc:
        mark_job_failed(job_id, error=str(exc))
        return
    except Exception as exc:  # pragma: no cover - defensive runtime guard
        _LOG.exception("Import processing job %s failed: %s", job_id, exc)
        mark_job_failed(job_id, error=str(exc))
        return
    mark_job_completed(job_id, extraction_summary=summary.model_dump() if summary else None)


@router.post(
    "/notes/import",
    response_model=ImportNoteResponse,
    status_code=status.HTTP_201_CREATED,
)
def import_note(
    payload: ImportNoteRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db_session),
) -> ImportNoteResponse:
    try:
        with session.begin():
            imported = NoteImportService(session).import_note(
                filename=payload.filename.strip(),
                content=payload.content,
                subject_id=payload.subject_id,
            )
    except UnsupportedFileTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    record, created = create_or_get_job(
        note_id=imported.note_id,
        content_hash=imported.content_hash,
    )
    if created:
        process_payload = ProcessNoteRequest(
            note_id=imported.note_id,
            content_text="",
            content_hash=imported.content_hash,
            updated_at=imported.updated_at,
        )
        background_tasks.add_task(
            _run_import_processing_job,
            job_id=record.job_id,
            payload=process_payload,
        )

    return ImportNoteResponse(
        note_id=imported.note_id,
        note_title=imported.note_title,
        saved_at=imported.updated_at,
    )
