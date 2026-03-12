from __future__ import annotations

from fastapi import APIRouter

from app.core.backfill_store import get_backfill_status
from shared.contracts.python.v1.backfill import BackfillStatusResponse

router = APIRouter()


@router.get("/backfill-status", response_model=BackfillStatusResponse)
def backfill_status() -> BackfillStatusResponse:
    snapshot = get_backfill_status()
    return BackfillStatusResponse(
        total_notes=snapshot.total_notes,
        processed_notes=snapshot.processed_notes,
        failed_notes=snapshot.failed_notes,
        in_progress=snapshot.in_progress,
    )

