"""add note_title to notes

Revision ID: 20260311_0003
Revises: 20260307_0002
Create Date: 2026-03-11 10:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260311_0003"
down_revision = "20260307_0002"
branch_labels = None
depends_on = None


def _table_exists(bind: sa.Connection, table_name: str) -> bool:
    inspector = sa.inspect(bind)
    return table_name in set(inspector.get_table_names())


def _column_names(bind: sa.Connection, table_name: str) -> set[str]:
    inspector = sa.inspect(bind)
    return {
        str(column.get("name"))
        for column in inspector.get_columns(table_name)
        if column.get("name") is not None
    }


def upgrade() -> None:
    bind = op.get_bind()
    if not _table_exists(bind, "notes"):
        return

    columns = _column_names(bind, "notes")
    if "note_title" in columns:
        return

    op.add_column(
        "notes",
        sa.Column("note_title", sa.String(length=255), nullable=True),
    )
    op.execute(sa.text("UPDATE notes SET note_title = 'Untitled' WHERE note_title IS NULL"))
    op.alter_column("notes", "note_title", existing_type=sa.String(length=255), nullable=False)


def downgrade() -> None:
    bind = op.get_bind()
    if not _table_exists(bind, "notes"):
        return

    columns = _column_names(bind, "notes")
    if "note_title" not in columns:
        return

    op.drop_column("notes", "note_title")
