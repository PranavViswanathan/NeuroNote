"""Add meta_classified_at to concept_registry

Tracks whether a concept has had its synonym/subtopic relationships
classified by the ConceptMetaClassifier. NULL = not yet classified;
set to NOW() after a successful SLM classification so the same concept
is never re-classified unless a new note introduces it fresh.

Revision ID: 20260403_0012
Revises: 20260403_0011
Create Date: 2026-04-03 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260403_0012"
down_revision = "20260403_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "concept_registry",
        sa.Column("meta_classified_at", sa.DateTime(timezone=True), nullable=True),
        schema="public",
    )


def downgrade() -> None:
    op.drop_column("concept_registry", "meta_classified_at", schema="public")
