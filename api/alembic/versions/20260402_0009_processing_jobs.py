"""Add processing_jobs table for durable job state

In-memory job_store is lost on restart. This table makes job state durable
so the frontend never gets stuck showing "processing" after a container restart.
On startup, any job that was IN_PROGRESS is automatically marked as FAILED.

Revision ID: 20260402_0009
Revises: 20260402_0008
Create Date: 2026-04-02 00:01:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260402_0009"
down_revision = "20260402_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "processing_jobs",
        sa.Column("job_id", sa.String(length=64), nullable=False),
        sa.Column("note_id", sa.String(length=255), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("job_id"),
        schema="public",
    )
    op.create_index(
        "ix_processing_jobs_note_content",
        "processing_jobs",
        ["note_id", "content_hash"],
        schema="public",
    )
    op.create_index(
        "ix_processing_jobs_status",
        "processing_jobs",
        ["status"],
        schema="public",
    )


def downgrade() -> None:
    op.drop_index("ix_processing_jobs_status", table_name="processing_jobs", schema="public")
    op.drop_index("ix_processing_jobs_note_content", table_name="processing_jobs", schema="public")
    op.drop_table("processing_jobs", schema="public")
