from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db_session

router = APIRouter()


@router.get("/health")
def health_check(response: Response, session: Session = Depends(get_db_session)) -> dict[str, str]:
    try:
        session.execute(text("SELECT 1"))
    except Exception:
        response.status_code = 503
        return {"status": "degraded", "detail": "database unreachable"}
    return {"status": "ok"}
