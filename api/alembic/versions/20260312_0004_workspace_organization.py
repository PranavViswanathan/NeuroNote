"""workspace organization metadata

Revision ID: 20260312_0004
Revises: 20260311_0003
Create Date: 2026-03-12 20:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260312_0004"
down_revision = "20260311_0003"
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


def _index_names(bind: sa.Connection, table_name: str) -> set[str]:
    inspector = sa.inspect(bind)
    return {
        str(index.get("name"))
        for index in inspector.get_indexes(table_name)
        if index.get("name") is not None
    }


def upgrade() -> None:
    bind = op.get_bind()

    if _table_exists(bind, "notes"):
        note_columns = _column_names(bind, "notes")
        if "is_pinned" not in note_columns:
            op.add_column(
                "notes",
                sa.Column(
                    "is_pinned",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.false(),
                ),
            )
        if "is_archived" not in note_columns:
            op.add_column(
                "notes",
                sa.Column(
                    "is_archived",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.false(),
                ),
            )

    has_note_tags = _table_exists(bind, "note_tags")
    if not has_note_tags and _table_exists(bind, "notes") and _table_exists(bind, "tags"):
        op.create_table(
            "note_tags",
            sa.Column("note_id", sa.String(length=255), nullable=False),
            sa.Column("tag_id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["note_id"], ["notes.note_id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("note_id", "tag_id"),
        )

    if _table_exists(bind, "note_tags"):
        indexes = _index_names(bind, "note_tags")
        if "ix_note_tags_note_id" not in indexes:
            op.create_index("ix_note_tags_note_id", "note_tags", ["note_id"])
        if "ix_note_tags_tag_id" not in indexes:
            op.create_index("ix_note_tags_tag_id", "note_tags", ["tag_id"])


def downgrade() -> None:
    bind = op.get_bind()

    if _table_exists(bind, "note_tags"):
        indexes = _index_names(bind, "note_tags")
        if "ix_note_tags_note_id" in indexes:
            op.drop_index("ix_note_tags_note_id", table_name="note_tags")
        if "ix_note_tags_tag_id" in indexes:
            op.drop_index("ix_note_tags_tag_id", table_name="note_tags")
        op.drop_table("note_tags")

    if _table_exists(bind, "notes"):
        note_columns = _column_names(bind, "notes")
        if "is_pinned" in note_columns:
            op.drop_column("notes", "is_pinned")
        if "is_archived" in note_columns:
            op.drop_column("notes", "is_archived")
