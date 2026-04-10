from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.services.export_service import ExportService, NoteNotFoundError

router = APIRouter()


@router.get("/notes/{note_id}/export/markdown")
def export_note_markdown(
    note_id: str,
    session: Session = Depends(get_db_session),
) -> Response:
    try:
        payload = ExportService(session).build_markdown_zip(note_id)
    except NoteNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    headers = {"Content-Disposition": f'attachment; filename="{note_id}.zip"'}
    return Response(content=payload, media_type="application/zip", headers=headers)
