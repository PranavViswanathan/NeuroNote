"""Unit tests for BlockRepository."""
from __future__ import annotations

import pytest

from app.db.repositories.block_repository import BlockRepository, _BLOCK_REF_PATTERN
from app.db.repositories.note_repository import NoteRepository

_CONTENT_JSON = {"type": "doc", "content": []}


# ---------------------------------------------------------------------------
# Helper to create a note before testing blocks
# ---------------------------------------------------------------------------

def _create_note(note_repo: NoteRepository, *, note_id: str = "note-1", title: str = "My Note") -> None:
    note_repo.upsert_note(
        note_id=note_id,
        note_title=title,
        subject_id="inbox",
        tags=[],
        is_pinned=False,
        is_archived=False,
        content_json=_CONTENT_JSON,
        content_text="placeholder",
        updated_at="2026-01-01T00:00:00Z",
    )


def _make_paragraph(text: str, block_uid: str | None = None) -> dict:
    node: dict = {
        "type": "paragraph",
        "content": [{"type": "text", "text": text}],
    }
    if block_uid:
        node["attrs"] = {"blockUid": block_uid}
    return node


# ---------------------------------------------------------------------------
# replace_blocks tests
# ---------------------------------------------------------------------------


def test_replace_blocks_creates_blocks_with_uid(note_repo, block_repo, session):
    content_json = {
        "type": "doc",
        "content": [_make_paragraph("Hello world", block_uid="uid-abc")],
    }
    _create_note(note_repo, note_id="note-1")
    session.commit()

    block_repo.replace_blocks(note_id="note-1", content_json=content_json, fallback_text="")
    session.commit()

    blocks = block_repo.list_blocks_for_note("note-1")
    assert len(blocks) == 1
    assert blocks[0].block_uid == "uid-abc"


def test_replace_blocks_auto_generates_uid_when_missing(note_repo, block_repo, session):
    content_json = {
        "type": "doc",
        "content": [_make_paragraph("No explicit uid")],  # no block_uid attr
    }
    _create_note(note_repo, note_id="note-1")
    session.commit()

    block_repo.replace_blocks(note_id="note-1", content_json=content_json, fallback_text="")
    session.commit()

    blocks = block_repo.list_blocks_for_note("note-1")
    assert len(blocks) == 1
    assert blocks[0].block_uid  # should be auto-generated non-empty string


def test_replace_blocks_removes_old_blocks(note_repo, block_repo, session):
    content_json_v1 = {
        "type": "doc",
        "content": [
            _make_paragraph("Block one", "uid-1"),
            _make_paragraph("Block two", "uid-2"),
        ],
    }
    _create_note(note_repo, note_id="note-1")
    session.commit()

    block_repo.replace_blocks(note_id="note-1", content_json=content_json_v1, fallback_text="")
    session.commit()

    assert len(block_repo.list_blocks_for_note("note-1")) == 2

    content_json_v2 = {
        "type": "doc",
        "content": [_make_paragraph("Only one block now", "uid-3")],
    }
    block_repo.replace_blocks(note_id="note-1", content_json=content_json_v2, fallback_text="")
    session.commit()

    blocks = block_repo.list_blocks_for_note("note-1")
    assert len(blocks) == 1
    assert blocks[0].block_uid == "uid-3"


def test_replace_blocks_extracts_content_text(note_repo, block_repo, session):
    content_json = {
        "type": "doc",
        "content": [_make_paragraph("Extracted text", "uid-x")],
    }
    _create_note(note_repo, note_id="note-1")
    session.commit()

    block_repo.replace_blocks(note_id="note-1", content_json=content_json, fallback_text="")
    session.commit()

    blocks = block_repo.list_blocks_for_note("note-1")
    assert blocks[0].content_text == "Extracted text"


def test_replace_blocks_index_reflects_document_order(note_repo, block_repo, session):
    content_json = {
        "type": "doc",
        "content": [
            _make_paragraph("First", "uid-1"),
            _make_paragraph("Second", "uid-2"),
            _make_paragraph("Third", "uid-3"),
        ],
    }
    _create_note(note_repo, note_id="note-1")
    session.commit()

    block_repo.replace_blocks(note_id="note-1", content_json=content_json, fallback_text="")
    session.commit()

    blocks = block_repo.list_blocks_for_note("note-1")
    assert [b.block_index for b in blocks] == [0, 1, 2]


def test_replace_blocks_returns_normalized_content_json(note_repo, block_repo, session):
    content_json = {
        "type": "doc",
        "content": [_make_paragraph("Norm check", "uid-norm")],
    }
    _create_note(note_repo, note_id="note-1")
    session.commit()

    result = block_repo.replace_blocks(note_id="note-1", content_json=content_json, fallback_text="")
    session.commit()

    # Result is a dict (the normalized content json)
    assert isinstance(result, dict)
    assert result.get("type") == "doc"


# ---------------------------------------------------------------------------
# list_blocks_for_note tests
# ---------------------------------------------------------------------------


def test_list_blocks_ordered_by_block_index(note_repo, block_repo, session):
    content_json = {
        "type": "doc",
        "content": [
            _make_paragraph("A", "uid-a"),
            _make_paragraph("B", "uid-b"),
            _make_paragraph("C", "uid-c"),
        ],
    }
    _create_note(note_repo, note_id="note-1")
    session.commit()

    block_repo.replace_blocks(note_id="note-1", content_json=content_json, fallback_text="")
    session.commit()

    blocks = block_repo.list_blocks_for_note("note-1")
    texts = [b.content_text for b in blocks]
    assert texts == ["A", "B", "C"]


def test_list_blocks_empty_for_note_with_no_blocks(block_repo):
    blocks = block_repo.list_blocks_for_note("nonexistent-note")
    assert blocks == []


# ---------------------------------------------------------------------------
# search_blocks tests
# ---------------------------------------------------------------------------


def test_search_blocks_finds_by_content_text(note_repo, block_repo, session):
    content_json = {
        "type": "doc",
        "content": [_make_paragraph("neural network architectures", "uid-nn")],
    }
    _create_note(note_repo, note_id="note-1")
    session.commit()

    block_repo.replace_blocks(note_id="note-1", content_json=content_json, fallback_text="")
    session.commit()

    results = block_repo.search_blocks(query="neural", note_id=None, limit=10)
    assert len(results) == 1
    assert results[0].block_uid == "uid-nn"


def test_search_blocks_returns_empty_for_empty_db(block_repo):
    results = block_repo.search_blocks(query="anything", note_id=None, limit=10)
    assert results == []


def test_search_blocks_empty_query_returns_all(note_repo, block_repo, session):
    content_json = {
        "type": "doc",
        "content": [
            _make_paragraph("First block", "uid-1"),
            _make_paragraph("Second block", "uid-2"),
        ],
    }
    _create_note(note_repo, note_id="note-1")
    session.commit()

    block_repo.replace_blocks(note_id="note-1", content_json=content_json, fallback_text="")
    session.commit()

    results = block_repo.search_blocks(query="", note_id=None, limit=100)
    assert len(results) == 2


def test_search_blocks_respects_limit(note_repo, block_repo, session):
    content_json = {
        "type": "doc",
        "content": [_make_paragraph(f"Block {i}", f"uid-{i}") for i in range(10)],
    }
    _create_note(note_repo, note_id="note-1")
    session.commit()

    block_repo.replace_blocks(note_id="note-1", content_json=content_json, fallback_text="")
    session.commit()

    results = block_repo.search_blocks(query="", note_id=None, limit=3)
    assert len(results) == 3


def test_search_blocks_case_insensitive(note_repo, block_repo, session):
    content_json = {
        "type": "doc",
        "content": [_make_paragraph("Transformer Models", "uid-t")],
    }
    _create_note(note_repo, note_id="note-1")
    session.commit()

    block_repo.replace_blocks(note_id="note-1", content_json=content_json, fallback_text="")
    session.commit()

    results = block_repo.search_blocks(query="TRANSFORMER", note_id=None, limit=10)
    assert len(results) == 1


# ---------------------------------------------------------------------------
# list_block_backlinks tests
# ---------------------------------------------------------------------------


def test_list_block_backlinks_returns_none_for_unknown_uid(block_repo):
    result = block_repo.list_block_backlinks("no-such-uid")
    assert result is None


def test_list_block_backlinks_returns_empty_when_no_references(note_repo, block_repo, session):
    content_json = {
        "type": "doc",
        "content": [_make_paragraph("standalone block", "uid-stand")],
    }
    _create_note(note_repo, note_id="note-1")
    session.commit()

    block_repo.replace_blocks(note_id="note-1", content_json=content_json, fallback_text="")
    session.commit()

    result = block_repo.list_block_backlinks("uid-stand")
    assert result == []


def test_list_block_backlinks_detects_double_paren_pattern(note_repo, block_repo, session):
    target_uid = "uid-target123"

    # Create note with target block
    content_target = {
        "type": "doc",
        "content": [_make_paragraph("I am the target", target_uid)],
    }
    _create_note(note_repo, note_id="note-target", title="Target Note")
    session.commit()
    block_repo.replace_blocks(note_id="note-target", content_json=content_target, fallback_text="")
    session.commit()

    # Create note with block referencing target via ((uid)) pattern in content_text
    ref_text = f"Refer to ((uid-target123)) for info"
    content_ref = {
        "type": "doc",
        "content": [_make_paragraph(ref_text, "uid-source")],
    }
    _create_note(note_repo, note_id="note-source", title="Source Note")
    session.commit()
    block_repo.replace_blocks(note_id="note-source", content_json=content_ref, fallback_text="")
    session.commit()

    result = block_repo.list_block_backlinks(target_uid)
    # There should be at least one backlink (uid-source references uid-target123)
    assert result is not None
    assert len(result) >= 1
    uids = [r.source_block_uid for r in result]
    assert "uid-source" in uids


def test_list_block_backlinks_snippet_has_context(note_repo, block_repo, session):
    target_uid = "uid-tgt456"

    content_target = {
        "type": "doc",
        "content": [_make_paragraph("Target block content", target_uid)],
    }
    _create_note(note_repo, note_id="note-t", title="T Note")
    session.commit()
    block_repo.replace_blocks(note_id="note-t", content_json=content_target, fallback_text="")
    session.commit()

    ref_text = f"Before context ((uid-tgt456)) after context"
    content_ref = {
        "type": "doc",
        "content": [_make_paragraph(ref_text, "uid-src2")],
    }
    _create_note(note_repo, note_id="note-s", title="S Note")
    session.commit()
    block_repo.replace_blocks(note_id="note-s", content_json=content_ref, fallback_text="")
    session.commit()

    result = block_repo.list_block_backlinks(target_uid)
    assert result is not None and len(result) >= 1
    snippet = result[0].snippet
    # The snippet should contain surrounding text
    assert "context" in snippet.lower() or "uid-tgt456" in snippet


# ---------------------------------------------------------------------------
# extract_block_refs tests
# ---------------------------------------------------------------------------


def test_extract_block_refs_finds_uid_patterns(block_repo):
    text = "See ((abc-def-123)) for more"
    refs = block_repo.extract_block_refs(text)
    assert "abc-def-123" in refs


def test_extract_block_refs_returns_empty_for_no_refs(block_repo):
    refs = block_repo.extract_block_refs("No refs here at all")
    assert refs == []
