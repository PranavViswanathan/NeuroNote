"""create core tables

Revision ID: 20260301_0001
Revises:
Create Date: 2026-03-01 11:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260301_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subjects",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "notes",
        sa.Column("note_id", sa.String(length=255), nullable=False),
        sa.Column("subject_id", sa.String(length=64), nullable=False),
        sa.Column("content_json", sa.JSON(), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("saved_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("note_id"),
    )
    op.create_index("ix_notes_subject_id", "notes", ["subject_id"])
    op.create_index("ix_notes_content_hash", "notes", ["content_hash"])

    op.create_table(
        "blocks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("note_id", sa.String(length=255), nullable=False),
        sa.Column("block_index", sa.Integer(), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("rich_content", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["note_id"], ["notes.note_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("note_id", "block_index", name="uq_blocks_note_id_block_index"),
    )
    op.create_index("ix_blocks_note_id", "blocks", ["note_id"])
    op.create_index("ix_blocks_content_hash", "blocks", ["content_hash"])

    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_tags_name", "tags", ["name"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_tags_name", table_name="tags")
    op.drop_table("tags")

    op.drop_index("ix_blocks_content_hash", table_name="blocks")
    op.drop_index("ix_blocks_note_id", table_name="blocks")
    op.drop_table("blocks")

    op.drop_index("ix_notes_content_hash", table_name="notes")
    op.drop_index("ix_notes_subject_id", table_name="notes")
    op.drop_table("notes")

    op.drop_table("subjects")
