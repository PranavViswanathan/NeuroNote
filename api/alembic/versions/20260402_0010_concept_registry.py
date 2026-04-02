"""Add concept_registry table for durable, cross-worker concept normalisation

The in-memory concept_registry is per-process and lost on restart. Multiple
uvicorn workers each build their own independent registry, causing the same
concept to be normalised differently across workers.

This table makes concept registration durable and shared: all workers and all
restarts see the same known-concept list fed to the SLM extraction prompt.

Revision ID: 20260402_0010
Revises: 20260402_0009
Create Date: 2026-04-02 00:02:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260402_0010"
down_revision = "20260402_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "concept_registry",
        sa.Column("concept_text", sa.Text(), nullable=False),
        sa.Column("entity_id", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("concept_text"),
        schema="public",
    )


def downgrade() -> None:
    op.drop_table("concept_registry", schema="public")
