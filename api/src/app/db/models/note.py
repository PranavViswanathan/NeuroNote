from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base

if TYPE_CHECKING:
    from app.db.models.block import Block
    from app.db.models.note_asset import NoteAsset
    from app.db.models.note_tag import NoteTag
    from app.db.models.subject import Subject
    from app.db.models.tag import Tag


class Note(Base):
    __tablename__ = "notes"

    note_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    subject_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("subjects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    note_title: Mapped[str] = mapped_column(String(255), nullable=False, default="Untitled")
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    content_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    updated_at: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    saved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    subject: Mapped["Subject"] = relationship(back_populates="notes")
    blocks: Mapped[list["Block"]] = relationship(
        back_populates="note",
        cascade="all, delete-orphan",
    )
    note_tags: Mapped[list["NoteTag"]] = relationship(
        back_populates="note",
        cascade="all, delete-orphan",
    )
    note_assets: Mapped[list["NoteAsset"]] = relationship(
        back_populates="note",
        cascade="all, delete-orphan",
    )
    tags: Mapped[list["Tag"]] = relationship(
        secondary="note_tags",
        back_populates="notes",
        overlaps="note_tags,tag,note",
    )
