"""note assets table for media uploads

Revision ID: 20260313_0005
Revises: 20260312_0004
Create Date: 2026-03-13 09:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260313_0005"
down_revision = "20260312_0004"
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

    if not _table_exists(bind, "note_assets") and _table_exists(bind, "notes"):
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
            sa.ForeignKeyConstraint(["note_id"], ["notes.note_id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("asset_id"),
            sa.UniqueConstraint("relative_path"),
        )

    if _table_exists(bind, "note_assets"):
        indexes = _index_names(bind, "note_assets")
        if "ix_note_assets_note_id" not in indexes:
            op.create_index("ix_note_assets_note_id", "note_assets", ["note_id"])


def downgrade() -> None:
    bind = op.get_bind()
    if _table_exists(bind, "note_assets"):
        indexes = _index_names(bind, "note_assets")
        if "ix_note_assets_note_id" in indexes:
            op.drop_index("ix_note_assets_note_id", table_name="note_assets")
        op.drop_table("note_assets")
