from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.repositories.block_repository import BlockRepository
from app.db.repositories.note_repository import NoteRepository


def _nested_doc() -> dict[str, object]:
    return {
        "type": "doc",
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": "Root paragraph"}]},
            {
                "type": "bulletList",
                "content": [
                    {
                        "type": "listItem",
                        "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Item one"}]}],
                    },
                    {
                        "type": "listItem",
                        "content": [
                            {"type": "paragraph", "content": [{"type": "text", "text": "Item two"}]},
                            {
                                "type": "bulletList",
                                "content": [
                                    {
                                        "type": "listItem",
                                        "content": [
                                            {
                                                "type": "paragraph",
                                                "content": [{"type": "text", "text": "Nested item"}],
                                            }
                                        ],
                                    }
                                ],
                            },
                        ],
                    },
                ],
            },
        ],
    }


def test_replace_blocks_persists_tree_fields(db_session: Session) -> None:
    note_repo = NoteRepository(db_session)
    block_repo = BlockRepository(db_session)

    with db_session.begin():
        note_repo.upsert_note(
            note_id="tree-note-1",
            note_title="Tree note",
            subject_id="inbox",
            tags=[],
            is_pinned=False,
            is_archived=False,
            content_json=_nested_doc(),
            content_text="Root paragraph\nItem one\nItem two\nNested item",
            updated_at="2026-03-14T12:00:00Z",
        )

    rows = block_repo.list_blocks_for_note("tree-note-1")
    assert rows
    assert all(row.block_uid for row in rows)
    assert all(row.sibling_order >= 0 for row in rows)
    assert any(row.parent_block_uid is not None for row in rows)


def test_search_blocks_prefers_note_scope(db_session: Session) -> None:
    note_repo = NoteRepository(db_session)
    block_repo = BlockRepository(db_session)

    with db_session.begin():
        note_repo.upsert_note(
            note_id="scope-a",
            note_title="Scope A",
            subject_id="inbox",
            tags=[],
            is_pinned=False,
            is_archived=False,
            content_json={"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Graph alpha"}]}]},
            content_text="Graph alpha",
            updated_at="2026-03-14T12:00:00Z",
        )
        note_repo.upsert_note(
            note_id="scope-b",
            note_title="Scope B",
            subject_id="inbox",
            tags=[],
            is_pinned=False,
            is_archived=False,
            content_json={"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Graph beta"}]}]},
            content_text="Graph beta",
            updated_at="2026-03-14T12:01:00Z",
        )

    rows = block_repo.search_blocks(query="graph", note_id="scope-a", limit=10)
    assert rows
    assert all(row.note_id == "scope-a" for row in rows)


def test_list_block_backlinks_returns_source_blocks(db_session: Session) -> None:
    note_repo = NoteRepository(db_session)
    block_repo = BlockRepository(db_session)

    with db_session.begin():
        note_repo.upsert_note(
            note_id="target-note",
            note_title="Target",
            subject_id="inbox",
            tags=[],
            is_pinned=False,
            is_archived=False,
            content_json={"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Target block body"}]}]},
            content_text="Target block body",
            updated_at="2026-03-14T12:02:00Z",
        )
        target_block_uid = block_repo.list_blocks_for_note("target-note")[0].block_uid

    with db_session.begin():
        note_repo.upsert_note(
            note_id="source-note",
            note_title="Source",
            subject_id="inbox",
            tags=[],
            is_pinned=False,
            is_archived=False,
            content_json={
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": f"Reference (({target_block_uid})) from source"}],
                    }
                ],
            },
            content_text=f"Reference (({target_block_uid})) from source",
            updated_at="2026-03-14T12:03:00Z",
        )

    backlinks = block_repo.list_block_backlinks(target_block_uid)
    assert backlinks is not None
    assert [item.source_note_id for item in backlinks] == ["source-note"]


def test_list_block_backlinks_supports_reference_link_marks(db_session: Session) -> None:
    note_repo = NoteRepository(db_session)
    block_repo = BlockRepository(db_session)

    with db_session.begin():
        note_repo.upsert_note(
            note_id="target-note-mark",
            note_title="Target mark",
            subject_id="inbox",
            tags=[],
            is_pinned=False,
            is_archived=False,
            content_json={
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "attrs": {"blockUid": "target-mark-uid"},
                        "content": [{"type": "text", "text": "Target block body"}],
                    }
                ],
            },
            content_text="Target block body",
            updated_at="2026-03-14T12:04:00Z",
        )

        note_repo.upsert_note(
            note_id="source-note-mark",
            note_title="Source mark",
            subject_id="inbox",
            tags=[],
            is_pinned=False,
            is_archived=False,
            content_json={
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": "Readable block link",
                                "marks": [
                                    {
                                        "type": "referenceLink",
                                        "attrs": {
                                            "href": "/notes/target-note-mark#block=target-mark-uid",
                                            "dataRefType": "block",
                                            "dataBlockUid": "target-mark-uid",
                                            "dataNoteId": "target-note-mark",
                                        },
                                    }
                                ],
                            }
                        ],
                    }
                ],
            },
            content_text="Readable block link",
            updated_at="2026-03-14T12:05:00Z",
        )

    backlinks = block_repo.list_block_backlinks("target-mark-uid")
    assert backlinks is not None
    assert [item.source_note_id for item in backlinks] == ["source-note-mark"]


def test_replace_blocks_rewrites_duplicate_block_uids_and_parent_refs(db_session: Session) -> None:
    note_repo = NoteRepository(db_session)
    block_repo = BlockRepository(db_session)

    with db_session.begin():
        note_repo.upsert_note(
            note_id="dup-uid-note",
            note_title="Duplicate uid note",
            subject_id="inbox",
            tags=[],
            is_pinned=False,
            is_archived=False,
            content_json={
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "attrs": {"blockUid": "dup-uid"},
                        "content": [{"type": "text", "text": "First"}],
                    },
                    {
                        "type": "paragraph",
                        "attrs": {"blockUid": "dup-uid"},
                        "content": [{"type": "text", "text": "Second"}],
                    },
                    {
                        "type": "paragraph",
                        "attrs": {
                            "blockUid": "child-uid",
                            "parentBlockUid": "dup-uid",
                        },
                        "content": [{"type": "text", "text": "Child"}],
                    },
                ],
            },
            content_text="First\nSecond\nChild",
            updated_at="2026-03-14T20:00:00Z",
        )

    rows = block_repo.list_blocks_for_note("dup-uid-note")
    assert len(rows) == 3
    assert len({row.block_uid for row in rows}) == 3

    persisted_note = note_repo.get_note("dup-uid-note")
    assert persisted_note is not None
    persisted_content = persisted_note.content_json.get("content")
    assert isinstance(persisted_content, list)
    first_node = persisted_content[0]
    second_node = persisted_content[1]
    child_node = persisted_content[2]
    assert isinstance(first_node, dict)
    assert isinstance(second_node, dict)
    assert isinstance(child_node, dict)
    first_attrs = first_node.get("attrs")
    second_attrs = second_node.get("attrs")
    child_attrs = child_node.get("attrs")
    assert isinstance(first_attrs, dict)
    assert isinstance(second_attrs, dict)
    assert isinstance(child_attrs, dict)
    first_uid = first_attrs.get("blockUid")
    second_uid = second_attrs.get("blockUid")
    child_parent_uid = child_attrs.get("parentBlockUid")
    assert isinstance(first_uid, str)
    assert isinstance(second_uid, str)
    assert isinstance(child_parent_uid, str)

    assert first_uid == "dup-uid"
    assert second_uid != "dup-uid"
    assert second_uid != first_uid
    assert child_parent_uid == second_uid
