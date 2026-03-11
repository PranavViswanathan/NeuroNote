"""create entity_aliases table

Revision ID: 20260307_0002
Revises: 20260301_0001
Create Date: 2026-03-07 14:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260307_0002"
down_revision = "20260301_0001"
branch_labels = None
depends_on = None


def _table_exists(bind: sa.Connection, table_name: str) -> bool:
    inspector = sa.inspect(bind)
    return table_name in set(inspector.get_table_names())


def _index_names(bind: sa.Connection, table_name: str) -> set[str]:
    inspector = sa.inspect(bind)
    return {
        str(index.get("name"))
        for index in inspector.get_indexes(table_name)
        if index.get("name") is not None
    }


def upgrade() -> None:
    bind = op.get_bind()
    if not _table_exists(bind, "entity_aliases"):
        op.create_table(
            "entity_aliases",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("alias_text", sa.String(length=255), nullable=False),
            sa.Column("canonical_entity_id", sa.String(length=255), nullable=False),
            sa.Column("canonical_name", sa.String(length=255), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=False),
            sa.Column("source", sa.String(length=64), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    indexes = _index_names(bind, "entity_aliases")
    if "ix_entity_aliases_alias_text" not in indexes:
        op.create_index(
            "ix_entity_aliases_alias_text",
            "entity_aliases",
            ["alias_text"],
            unique=True,
        )
    if "ix_entity_aliases_canonical_entity_id" not in indexes:
        op.create_index(
            "ix_entity_aliases_canonical_entity_id",
            "entity_aliases",
            ["canonical_entity_id"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    if not _table_exists(bind, "entity_aliases"):
        return

    indexes = _index_names(bind, "entity_aliases")
    if "ix_entity_aliases_canonical_entity_id" in indexes:
        op.drop_index("ix_entity_aliases_canonical_entity_id", table_name="entity_aliases")
    if "ix_entity_aliases_alias_text" in indexes:
        op.drop_index("ix_entity_aliases_alias_text", table_name="entity_aliases")
    op.drop_table("entity_aliases")
