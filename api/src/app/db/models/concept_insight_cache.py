from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base


class ConceptInsightCache(Base):
    __tablename__ = "concept_insight_cache"

    concept_label: Mapped[str] = mapped_column(Text, primary_key=True)
    content_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    insight: Mapped[str] = mapped_column(Text, nullable=False)
    learning_links: Mapped[str] = mapped_column(Text, nullable=False, server_default="[]")
    notes_count: Mapped[int] = mapped_column(Integer, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
