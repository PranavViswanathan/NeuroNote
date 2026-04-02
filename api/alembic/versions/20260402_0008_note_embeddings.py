"""Add note_embeddings table with pgvector HNSW index

The table was previously created at runtime by GraphRepository.ensure_embedding_table().
This migration makes it part of the official schema so fresh deployments get it via
`alembic upgrade head` instead of waiting for the first NLP sync.

The HNSW index on the embedding column turns the O(n) cosine-distance sequential scan
used by nearest_neighbors() into an approximate ANN search — orders of magnitude faster
beyond a few hundred rows.

Revision ID: 20260402_0008
Revises: 20260314_0007
Create Date: 2026-04-02 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260402_0008"
down_revision = "20260314_0007"
branch_labels = None
depends_on = None


def _table_exists(bind: sa.Connection, table_name: str, *, schema: str | None = None) -> bool:
    inspector = sa.inspect(bind)
    try:
        table_names = inspector.get_table_names(schema=schema)
    except TypeError:
        table_names = inspector.get_table_names()
    return table_name in set(table_names)


def _index_exists(bind: sa.Connection, table_name: str, index_name: str, *, schema: str | None = None) -> bool:
    inspector = sa.inspect(bind)
    try:
        indexes = inspector.get_indexes(table_name, schema=schema)
    except (sa.exc.NoSuchTableError, TypeError):
        return False
    return any(str(idx.get("name")) == index_name for idx in indexes)


def upgrade() -> None:
    bind = op.get_bind()

    # Enable pgvector extension — idempotent.
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))

    # Create table only if it does not already exist (may have been created at runtime).
    if not _table_exists(bind, "note_embeddings", schema="public"):
        op.create_table(
            "note_embeddings",
            sa.Column("embedding_id", sa.BigInteger(), nullable=False, autoincrement=True),
            sa.Column("item_id", sa.Text(), nullable=False),
            sa.Column("item_type", sa.Text(), nullable=False),
            # vector(384) is a pgvector type — expressed as raw DDL below.
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
            sa.PrimaryKeyConstraint("embedding_id"),
            sa.UniqueConstraint("item_id", "item_type", name="uq_note_embeddings_item"),
            schema="public",
        )
        # Add the vector column separately (SQLAlchemy has no native Vector type yet).
        op.execute(sa.text(
            "ALTER TABLE public.note_embeddings ADD COLUMN IF NOT EXISTS embedding vector(384) NOT NULL"
        ))

    # Add HNSW index — approximate nearest-neighbour, far faster than sequential scan.
    if not _index_exists(bind, "note_embeddings", "ix_note_embeddings_hnsw", schema="public"):
        op.execute(sa.text(
            "CREATE INDEX ix_note_embeddings_hnsw "
            "ON public.note_embeddings "
            "USING hnsw (embedding vector_cosine_ops)"
        ))


def downgrade() -> None:
    bind = op.get_bind()
    if _index_exists(bind, "note_embeddings", "ix_note_embeddings_hnsw", schema="public"):
        op.execute(sa.text("DROP INDEX IF EXISTS public.ix_note_embeddings_hnsw"))
    if _table_exists(bind, "note_embeddings", schema="public"):
        op.drop_table("note_embeddings", schema="public")
