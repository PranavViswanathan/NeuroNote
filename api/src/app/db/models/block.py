from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base

if TYPE_CHECKING:
    from app.db.models.note import Note


class Block(Base):
    __tablename__ = "blocks"
    __table_args__ = (
        UniqueConstraint("note_id", "block_uid", name="uq_blocks_note_id_block_uid"),
        UniqueConstraint(
            "note_id",
            "parent_block_uid",
            "sibling_order",
            name="uq_blocks_note_id_parent_sibling_order",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    note_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("notes.note_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    block_uid: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    parent_block_uid: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    sibling_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    block_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    rich_content: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
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

    note: Mapped["Note"] = relationship(back_populates="blocks")
