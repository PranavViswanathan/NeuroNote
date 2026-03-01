from fastapi import APIRouter, HTTPException, status

from app.core.job_store import create_job, get_job
from shared.contracts.python.v1.process import (
    ProcessNoteRequest,
    ProcessNoteResponse,
    ProcessStatusResponse,
)

router = APIRouter()


@router.post(
    "/process-note",
    response_model=ProcessNoteResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def process_note(payload: ProcessNoteRequest) -> ProcessNoteResponse:
    _ = payload
    record = create_job()
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
