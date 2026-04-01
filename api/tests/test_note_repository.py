"""Unit tests for NoteRepository."""
from __future__ import annotations

import hashlib

import pytest

from app.db.repositories.note_repository import (
    NoteRecord,
    NoteRepository,
    NoteTitleConflictError,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CONTENT_JSON = {"type": "doc", "content": []}


def _upsert(repo: NoteRepository, **kwargs) -> NoteRecord:
    defaults = dict(
        note_id="note-1",
        note_title="My Note",
        subject_id="inbox",
        tags=[],
        is_pinned=False,
        is_archived=False,
        content_json=_CONTENT_JSON,
        content_text="hello world",
        updated_at="2026-01-01T00:00:00Z",
    )
    defaults.update(kwargs)
    return repo.upsert_note(**defaults)


# ---------------------------------------------------------------------------
# upsert_note tests
# ---------------------------------------------------------------------------


def test_upsert_creates_new_note(note_repo, session):
    record = _upsert(note_repo)
    session.commit()

    assert record.note_id == "note-1"
    assert record.note_title == "My Note"
    assert record.subject_id == "inbox"
    assert record.version == 1
    assert isinstance(record.content_hash, str)
    assert len(record.content_hash) == 64  # sha256 hex


def test_upsert_increments_version_on_update(note_repo, session):
    _upsert(note_repo)
    session.commit()

    record2 = _upsert(note_repo, note_title="My Note")
    session.commit()

    assert record2.version == 2


def test_upsert_whitespace_normalized_title(note_repo, session):
    record = _upsert(note_repo, note_id="note-ws", note_title="  My   Note  ")
    session.commit()

    assert record.note_title == "My Note"


def test_upsert_tags_lowercase_and_deduplicated(note_repo, session):
    record = _upsert(note_repo, note_id="note-tags", tags=["ML", "ml", "Python", "python"])
    session.commit()

    assert sorted(record.tags) == ["ml", "python"]


def test_upsert_empty_subject_id_falls_back_to_inbox(note_repo, session):
    record = _upsert(note_repo, note_id="note-subj", subject_id="")
    session.commit()

    assert record.subject_id == "inbox"


def test_upsert_whitespace_only_subject_id_falls_back_to_inbox(note_repo, session):
    record = _upsert(note_repo, note_id="note-subj2", subject_id="   ")
    session.commit()

    assert record.subject_id == "inbox"


def test_upsert_raises_conflict_for_same_title_different_note(note_repo, session):
    _upsert(note_repo, note_id="note-a", note_title="Shared Title")
    session.commit()

    with pytest.raises(NoteTitleConflictError):
        _upsert(note_repo, note_id="note-b", note_title="shared title")


def test_upsert_does_not_raise_for_same_note_id_same_title(note_repo, session):
    _upsert(note_repo, note_id="note-same", note_title="Unique Title")
    session.commit()

    # Should succeed — same note_id updating its own title
    record2 = _upsert(note_repo, note_id="note-same", note_title="Unique Title")
    session.commit()

    assert record2.version == 2


def test_upsert_content_hash_is_deterministic(note_repo, session):
    record1 = _upsert(note_repo, note_id="note-h1", note_title="Hash Test", content_text="body")
    session.commit()

    # Compute expected hash manually
    combined = "Hash Test\n\nbody"
    expected_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()

    assert record1.content_hash == expected_hash


def test_upsert_replaces_tags_on_update(note_repo, session):
    _upsert(note_repo, note_id="note-tagr", tags=["old-tag"])
    session.commit()

    record2 = _upsert(note_repo, note_id="note-tagr", tags=["new-tag"])
    session.commit()

    assert record2.tags == ["new-tag"]
    assert "old-tag" not in record2.tags


# ---------------------------------------------------------------------------
# get_note tests
# ---------------------------------------------------------------------------


def test_get_note_returns_record_for_existing(note_repo, session):
    _upsert(note_repo, note_id="note-get", note_title="Get Me")
    session.commit()

    result = note_repo.get_note("note-get")

    assert result is not None
    assert result.note_id == "note-get"
    assert result.note_title == "Get Me"


def test_get_note_returns_none_for_missing(note_repo):
    result = note_repo.get_note("does-not-exist")
    assert result is None


# ---------------------------------------------------------------------------
# list_notes tests
# ---------------------------------------------------------------------------


def _list(repo: NoteRepository, **kwargs):
    defaults = dict(limit=50, offset=0)
    defaults.update(kwargs)
    items, total = repo.list_notes(**defaults)
    return items, total


def test_list_notes_returns_all_active(note_repo, session):
    _upsert(note_repo, note_id="n1", note_title="Alpha")
    _upsert(note_repo, note_id="n2", note_title="Beta")
    session.commit()

    items, total = _list(note_repo)

    assert total == 2
    assert len(items) == 2


def test_list_notes_filters_by_search_title(note_repo, session):
    _upsert(note_repo, note_id="n1", note_title="Machine Learning")
    _upsert(note_repo, note_id="n2", note_title="Unrelated")
    session.commit()

    items, total = _list(note_repo, search="machine")

    assert total == 1
    assert items[0].note_id == "n1"


def test_list_notes_filters_by_search_content(note_repo, session):
    _upsert(note_repo, note_id="n1", note_title="Alpha", content_text="deep learning concepts")
    _upsert(note_repo, note_id="n2", note_title="Beta", content_text="nothing relevant")
    session.commit()

    items, total = _list(note_repo, search="deep learning")

    assert total == 1
    assert items[0].note_id == "n1"


def test_list_notes_search_is_case_insensitive(note_repo, session):
    _upsert(note_repo, note_id="n1", note_title="Neural Networks")
    session.commit()

    items, _ = _list(note_repo, search="NEURAL")

    assert len(items) == 1


def test_list_notes_filters_by_subject_id(note_repo, session):
    _upsert(note_repo, note_id="n1", note_title="Work Note", subject_id="work")
    _upsert(note_repo, note_id="n2", note_title="Personal Note", subject_id="inbox")
    session.commit()

    items, total = _list(note_repo, subject_id="work")

    assert total == 1
    assert items[0].note_id == "n1"


def test_list_notes_filters_by_tag(note_repo, session):
    _upsert(note_repo, note_id="n1", note_title="Tagged", tags=["ml"])
    _upsert(note_repo, note_id="n2", note_title="Untagged", tags=[])
    session.commit()

    items, total = _list(note_repo, tag="ML")  # case-insensitive

    assert total == 1
    assert items[0].note_id == "n1"


def test_list_notes_filters_by_is_archived_true(note_repo, session):
    _upsert(note_repo, note_id="n1", note_title="Active", is_archived=False)
    _upsert(note_repo, note_id="n2", note_title="Archived", is_archived=True)
    session.commit()

    items, total = _list(note_repo, is_archived=True)

    assert total == 1
    assert items[0].note_id == "n2"


def test_list_notes_filters_by_is_pinned_true(note_repo, session):
    _upsert(note_repo, note_id="n1", note_title="Pinned", is_pinned=True)
    _upsert(note_repo, note_id="n2", note_title="Not Pinned", is_pinned=False)
    session.commit()

    items, total = _list(note_repo, is_archived=None, is_pinned=True)

    assert total == 1
    assert items[0].note_id == "n1"


def test_list_notes_pagination(note_repo, session):
    for i in range(5):
        _upsert(note_repo, note_id=f"n{i}", note_title=f"Note {i}")
    session.commit()

    items, total = _list(note_repo, limit=2, offset=0)

    assert total == 5
    assert len(items) == 2


def test_list_notes_returns_empty_when_no_match(note_repo, session):
    _upsert(note_repo, note_id="n1", note_title="Something")
    session.commit()

    items, total = _list(note_repo, search="zzz-no-match")

    assert total == 0
    assert items == []


# ---------------------------------------------------------------------------
# delete_note tests
# ---------------------------------------------------------------------------


def test_delete_note_returns_true_and_removes(note_repo, session):
    _upsert(note_repo, note_id="note-del")
    session.commit()

    deleted = note_repo.delete_note("note-del")
    session.commit()

    assert deleted is True
    assert note_repo.get_note("note-del") is None


def test_delete_note_returns_false_for_missing(note_repo):
    result = note_repo.delete_note("ghost-note")
    assert result is False


# ---------------------------------------------------------------------------
# list_backlinks_for_note tests
# ---------------------------------------------------------------------------


def test_backlinks_empty_when_no_links(note_repo, session):
    _upsert(note_repo, note_id="target", note_title="Target Note")
    session.commit()

    backlinks = note_repo.list_backlinks_for_note("target")

    assert backlinks == []


def test_backlinks_returned_when_source_links_to_target(note_repo, session):
    _upsert(note_repo, note_id="target", note_title="Target Note")
    _upsert(
        note_repo,
        note_id="source",
        note_title="Source Note",
        content_text="See [[Target Note]] for details",
    )
    session.commit()

    backlinks = note_repo.list_backlinks_for_note("target")

    assert len(backlinks) == 1
    assert backlinks[0].source_note_id == "source"
    assert backlinks[0].matched_title == "Target Note"


def test_backlinks_wiki_link_matching_is_case_insensitive(note_repo, session):
    _upsert(note_repo, note_id="target", note_title="Target Note")
    _upsert(
        note_repo,
        note_id="source",
        note_title="Source Note",
        content_text="Read [[target note]] here",
    )
    session.commit()

    backlinks = note_repo.list_backlinks_for_note("target")

    assert len(backlinks) == 1


def test_backlinks_returns_empty_for_missing_note(note_repo):
    backlinks = note_repo.list_backlinks_for_note("ghost-note")
    assert backlinks == []


def test_backlinks_snippet_contains_surrounding_text(note_repo, session):
    _upsert(note_repo, note_id="target", note_title="Important Note")
    _upsert(
        note_repo,
        note_id="source",
        note_title="Source",
        content_text="Please read [[Important Note]] carefully",
    )
    session.commit()

    backlinks = note_repo.list_backlinks_for_note("target")

    assert len(backlinks) == 1
    snippet = backlinks[0].snippet
    assert "Important Note" in snippet


def test_backlinks_does_not_include_self_reference(note_repo, session):
    _upsert(
        note_repo,
        note_id="self-ref",
        note_title="Self Ref Note",
        content_text="See [[Self Ref Note]] for more",
    )
    session.commit()

    backlinks = note_repo.list_backlinks_for_note("self-ref")

    # self-referential links are excluded because list_backlinks_for_note
    # only scans notes where note_id != target note_id
    assert backlinks == []


# ---------------------------------------------------------------------------
# _iter_wiki_link_titles (tested indirectly via backlinks, plus directly)
# ---------------------------------------------------------------------------


def test_iter_wiki_link_extracts_single_title(note_repo):
    titles = note_repo._iter_wiki_link_titles("See [[My Note]] here")
    assert titles == ["My Note"]


def test_iter_wiki_link_extracts_multiple_titles(note_repo):
    titles = note_repo._iter_wiki_link_titles("See [[Alpha]] and [[Beta]] here")
    assert titles == ["Alpha", "Beta"]


def test_iter_wiki_link_ignores_single_bracket(note_repo):
    titles = note_repo._iter_wiki_link_titles("[Not a link] and [another]")
    assert titles == []
