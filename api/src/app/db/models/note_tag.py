from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base

if TYPE_CHECKING:
    from app.db.models.note import Note
    from app.db.models.tag import Tag


class NoteTag(Base):
    __tablename__ = "note_tags"

    note_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("notes.note_id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    tag_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

    note: Mapped["Note"] = relationship(back_populates="note_tags", overlaps="tags,notes")
    tag: Mapped["Tag"] = relationship(back_populates="note_tags", overlaps="tags,notes")
