"""add block tree fields and constraints

Revision ID: 20260314_0006
Revises: 20260313_0005
Create Date: 2026-03-14 11:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from uuid import uuid4


revision = "20260314_0006"
down_revision = "20260313_0005"
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


def _unique_names(bind: sa.Connection, table_name: str) -> set[str]:
    inspector = sa.inspect(bind)
    return {
        str(item.get("name"))
        for item in inspector.get_unique_constraints(table_name)
        if item.get("name") is not None
    }


def upgrade() -> None:
    bind = op.get_bind()
    if not _table_exists(bind, "blocks"):
        return

    columns = _column_names(bind, "blocks")
    if "block_uid" not in columns:
        op.add_column("blocks", sa.Column("block_uid", sa.String(length=64), nullable=True))
    if "parent_block_uid" not in columns:
        op.add_column("blocks", sa.Column("parent_block_uid", sa.String(length=64), nullable=True))
    if "sibling_order" not in columns:
        op.add_column("blocks", sa.Column("sibling_order", sa.Integer(), nullable=True))

    rows = bind.execute(sa.text("SELECT id, block_uid, block_index, sibling_order FROM blocks")).all()
    for row in rows:
        row_id = int(row[0])
        row_uid = row[1]
        row_block_index = int(row[2]) if row[2] is not None else 0
        row_sibling_order = row[3]

        updates: dict[str, object] = {"block_uid": None, "sibling_order": None}
        if row_uid is None or (isinstance(row_uid, str) and not row_uid.strip()):
            updates["block_uid"] = uuid4().hex
        if row_sibling_order is None:
            updates["sibling_order"] = row_block_index
        if updates["block_uid"] is not None or updates["sibling_order"] is not None:
            updates["id"] = row_id
            bind.execute(
                sa.text(
                    """
                    UPDATE blocks
                    SET
                        block_uid = COALESCE(:block_uid, block_uid),
                        sibling_order = COALESCE(:sibling_order, sibling_order)
                    WHERE id = :id
                    """
                ),
                updates,
            )

    op.alter_column("blocks", "block_uid", nullable=False)
    op.alter_column("blocks", "sibling_order", nullable=False)

    indexes = _index_names(bind, "blocks")
    if "ix_blocks_block_uid" not in indexes:
        op.create_index("ix_blocks_block_uid", "blocks", ["block_uid"])
    if "ix_blocks_parent_block_uid" not in indexes:
        op.create_index("ix_blocks_parent_block_uid", "blocks", ["parent_block_uid"])

    uniques = _unique_names(bind, "blocks")
    if "uq_blocks_note_id_block_index" in uniques:
        op.drop_constraint("uq_blocks_note_id_block_index", "blocks", type_="unique")
    uniques = _unique_names(bind, "blocks")
    if "uq_blocks_note_id_block_uid" not in uniques:
        op.create_unique_constraint("uq_blocks_note_id_block_uid", "blocks", ["note_id", "block_uid"])
    if "uq_blocks_note_id_parent_sibling_order" not in uniques:
        op.create_unique_constraint(
            "uq_blocks_note_id_parent_sibling_order",
            "blocks",
            ["note_id", "parent_block_uid", "sibling_order"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    if not _table_exists(bind, "blocks"):
        return

    uniques = _unique_names(bind, "blocks")
    if "uq_blocks_note_id_parent_sibling_order" in uniques:
        op.drop_constraint("uq_blocks_note_id_parent_sibling_order", "blocks", type_="unique")
    if "uq_blocks_note_id_block_uid" in uniques:
        op.drop_constraint("uq_blocks_note_id_block_uid", "blocks", type_="unique")
    if "uq_blocks_note_id_block_index" not in uniques:
        op.create_unique_constraint("uq_blocks_note_id_block_index", "blocks", ["note_id", "block_index"])

    indexes = _index_names(bind, "blocks")
    if "ix_blocks_parent_block_uid" in indexes:
        op.drop_index("ix_blocks_parent_block_uid", table_name="blocks")
    if "ix_blocks_block_uid" in indexes:
        op.drop_index("ix_blocks_block_uid", table_name="blocks")

    columns = _column_names(bind, "blocks")
    if "sibling_order" in columns:
        op.drop_column("blocks", "sibling_order")
    if "parent_block_uid" in columns:
        op.drop_column("blocks", "parent_block_uid")
    if "block_uid" in columns:
        op.drop_column("blocks", "block_uid")
