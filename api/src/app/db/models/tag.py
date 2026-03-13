from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship

from app.db.models.base import Base

if TYPE_CHECKING:
    from app.db.models.note import Note
    from app.db.models.note_tag import NoteTag


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    note_tags: Mapped[list["NoteTag"]] = relationship(
        back_populates="tag",
        cascade="all, delete-orphan",
    )
    notes: Mapped[list["Note"]] = relationship(
        secondary="note_tags",
        back_populates="tags",
        overlaps="note_tags,note,tag",
    )
