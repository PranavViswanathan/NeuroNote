"""repair note_assets table when prior revisions were stamped without media schema

Revision ID: 20260314_0007
Revises: 20260314_0006
Create Date: 2026-03-14 19:20:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260314_0007"
down_revision = "20260314_0006"
branch_labels = None
depends_on = None


def _table_exists(bind: sa.Connection, table_name: str, *, schema: str | None = None) -> bool:
    inspector = sa.inspect(bind)
    try:
        table_names = inspector.get_table_names(schema=schema)
    except TypeError:
        table_names = inspector.get_table_names()
    return table_name in set(table_names)


def _index_names(bind: sa.Connection, table_name: str, *, schema: str | None = None) -> set[str]:
    inspector = sa.inspect(bind)
    try:
        indexes = inspector.get_indexes(table_name, schema=schema)
    except sa.exc.NoSuchTableError:
        return set()
    except TypeError:
        indexes = inspector.get_indexes(table_name)
    return {
        str(index.get("name"))
        for index in indexes
        if index.get("name") is not None
    }


def upgrade() -> None:
    bind = op.get_bind()

    has_notes = _table_exists(bind, "notes", schema="public") or _table_exists(bind, "notes")
    if not has_notes:
        return

    has_note_assets = _table_exists(bind, "note_assets", schema="public")
    if not has_note_assets:
        op.create_table(
            "note_assets",
            sa.Column("asset_id", sa.String(length=64), nullable=False),
            sa.Column("note_id", sa.String(length=255), nullable=False),
            sa.Column("mime_type", sa.String(length=128), nullable=False),
            sa.Column("file_ext", sa.String(length=16), nullable=False),
            sa.Column("byte_size", sa.Integer(), nullable=False),
            sa.Column("relative_path", sa.String(length=512), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["note_id"], ["public.notes.note_id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("asset_id"),
            sa.UniqueConstraint("relative_path"),
            schema="public",
        )

    public_indexes = _index_names(bind, "note_assets", schema="public")
    if "ix_note_assets_note_id" not in public_indexes:
        op.create_index(
            "ix_note_assets_note_id",
            "note_assets",
            ["note_id"],
            schema="public",
        )


def downgrade() -> None:
    # Irreversible repair migration: intentionally no-op.
    return None
