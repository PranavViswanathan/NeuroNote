"""Process-level LRU cache for compiled graph responses.

Invalidation is keyed on MAX(updated_at) across all notes — a single cheap SQL
aggregate that changes the moment any note is saved. No explicit invalidation calls
needed; callers include notes_version in the cache key.
"""
from __future__ import annotations

from collections import OrderedDict

from sqlalchemy import text
from sqlalchemy.orm import Session

_GRAPH_CACHE: OrderedDict[str, object] = OrderedDict()
_GRAPH_CACHE_MAX = 64  # graph responses can be large; cap memory usage


def get_notes_version(session: Session) -> str:
    """Return a version string that changes whenever any note is saved.

    Uses MAX(updated_at) which is already indexed and computed in O(1) by Postgres.
    Falls back to empty string (safe: causes cache miss) if the query fails or the
    table is empty.
    """
    try:
        row = session.execute(
            text("SELECT COALESCE(MAX(updated_at), '') FROM notes")
        ).first()
        return str(row[0]) if row else ""
    except Exception:
        return ""


def get_note_version(session: Session, note_id: str) -> str:
    """Return a version string that changes only when a specific note is saved.

    Used by LocalGraphService so that editing an unrelated note does not
    invalidate a cached local-graph response for a different seed note.
    Falls back to empty string (safe: causes cache miss) on any error.
    """
    try:
        row = session.execute(
            text("SELECT COALESCE(updated_at, '') FROM notes WHERE note_id = :nid"),
            {"nid": note_id},
        ).first()
        return str(row[0]) if row else ""
    except Exception:
        return ""


def get_cached(key: str) -> object | None:
    """Return a cached graph response or None on miss."""
    if key in _GRAPH_CACHE:
        _GRAPH_CACHE.move_to_end(key)
        return _GRAPH_CACHE[key]
    return None


def set_cached(key: str, value: object) -> None:
    """Store a graph response, evicting the oldest entry when over capacity."""
    _GRAPH_CACHE[key] = value
    _GRAPH_CACHE.move_to_end(key)
    if len(_GRAPH_CACHE) > _GRAPH_CACHE_MAX:
        _GRAPH_CACHE.popitem(last=False)


__all__ = ["get_notes_version", "get_note_version", "get_cached", "set_cached"]
