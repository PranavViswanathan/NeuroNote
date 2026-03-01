from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.tag import Tag


class TagRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_name(self, name: str) -> Tag | None:
        return self._session.execute(
            select(Tag).where(Tag.name == name),
        ).scalar_one_or_none()

    def create(self, *, name: str) -> Tag:
        tag = Tag(name=name)
        self._session.add(tag)
        self._session.flush()
        return tag
