from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.subject import Subject


class SubjectRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, subject_id: str) -> Subject | None:
        return self._session.execute(
            select(Subject).where(Subject.id == subject_id),
        ).scalar_one_or_none()

    def create(self, *, subject_id: str, name: str) -> Subject:
        subject = Subject(id=subject_id, name=name)
        self._session.add(subject)
        self._session.flush()
        return subject
