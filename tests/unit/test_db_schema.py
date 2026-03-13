from __future__ import annotations

from sqlalchemy import inspect

from app.db.engine import get_engine


def test_core_tables_exist(configured_db: None) -> None:
    inspector = inspect(get_engine())
    table_names = set(inspector.get_table_names())

    assert {
        "subjects",
        "notes",
        "blocks",
        "tags",
        "note_tags",
        "entity_aliases",
        "note_assets",
    }.issubset(table_names)


def test_foreign_keys_and_indexes_exist(configured_db: None) -> None:
    inspector = inspect(get_engine())
    note_columns = {column["name"] for column in inspector.get_columns("notes")}
    assert "note_title" in note_columns
    assert "is_pinned" in note_columns
    assert "is_archived" in note_columns

    note_fks = inspector.get_foreign_keys("notes")
    assert any(
        fk.get("referred_table") == "subjects" and fk.get("constrained_columns") == ["subject_id"]
        for fk in note_fks
    )

    block_fks = inspector.get_foreign_keys("blocks")
    assert any(
        fk.get("referred_table") == "notes" and fk.get("constrained_columns") == ["note_id"]
        for fk in block_fks
    )

    block_indexes = {index["name"] for index in inspector.get_indexes("blocks")}
    assert "ix_blocks_note_id" in block_indexes
    assert "ix_blocks_content_hash" in block_indexes

    block_uniques = inspector.get_unique_constraints("blocks")
    assert any(
        constraint.get("name") == "uq_blocks_note_id_block_index"
        or constraint.get("column_names") == ["note_id", "block_index"]
        for constraint in block_uniques
    )

    alias_indexes = {index["name"] for index in inspector.get_indexes("entity_aliases")}
    assert "ix_entity_aliases_alias_text" in alias_indexes
    assert "ix_entity_aliases_canonical_entity_id" in alias_indexes

    note_tag_fks = inspector.get_foreign_keys("note_tags")
    assert any(
        fk.get("referred_table") == "notes" and fk.get("constrained_columns") == ["note_id"]
        for fk in note_tag_fks
    )
    assert any(
        fk.get("referred_table") == "tags" and fk.get("constrained_columns") == ["tag_id"]
        for fk in note_tag_fks
    )

    note_asset_fks = inspector.get_foreign_keys("note_assets")
    assert any(
        fk.get("referred_table") == "notes" and fk.get("constrained_columns") == ["note_id"]
        for fk in note_asset_fks
    )

    note_asset_indexes = {index["name"] for index in inspector.get_indexes("note_assets")}
    assert "ix_note_assets_note_id" in note_asset_indexes
