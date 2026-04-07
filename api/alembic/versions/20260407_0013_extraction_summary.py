"""Add extraction_summary JSONB column to processing_jobs

Stores entity/relation/keyphrase counts and top entity names so the
frontend can display what was extracted after processing completes.

Revision ID: 20260407_0013
Revises: 20260403_0012
Create Date: 2026-04-07 00:01:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "20260407_0013"
down_revision = "20260403_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "processing_jobs",
        sa.Column("extraction_summary", JSONB, nullable=True),
        schema="public",
    )


def downgrade() -> None:
    op.drop_column("processing_jobs", "extraction_summary", schema="public")
