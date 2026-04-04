"""Add AI output cache tables

Two tables to persist AI-generated content across server restarts:

- concept_insight_cache: Claude-generated concept insights, keyed by
  concept_label + content_digest (hash of the relevant notes). Auto-stale
  when the underlying notes change.

- nlp_extraction_cache: NLP/SLM extraction results (entities, relations,
  summary), keyed by content_hash + extraction_profile. Eliminates redundant
  LLM calls after a container restart for notes whose content has not changed.

Revision ID: 20260403_0011
Revises: 20260402_0010
Create Date: 2026-04-03 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260403_0011"
down_revision = "20260402_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "concept_insight_cache",
        sa.Column("concept_label", sa.Text(), nullable=False),
        sa.Column("content_digest", sa.String(length=64), nullable=False),
        sa.Column("insight", sa.Text(), nullable=False),
        sa.Column("learning_links", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("notes_count", sa.Integer(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("concept_label"),
        schema="public",
    )

    op.create_table(
        "nlp_extraction_cache",
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("extraction_profile", sa.String(length=32), nullable=False),
        sa.Column("result_json", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.PrimaryKeyConstraint("content_hash"),
        schema="public",
    )


def downgrade() -> None:
    op.drop_table("nlp_extraction_cache", schema="public")
    op.drop_table("concept_insight_cache", schema="public")
