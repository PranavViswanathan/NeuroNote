"""Concept registry with Postgres persistence and in-process TTL cache.

When running on Postgres, concept registrations are stored in the
`concept_registry` table so they survive restarts and are shared across
multiple uvicorn workers. The in-process cache avoids a DB hit on every
extraction call; it refreshes automatically after _CACHE_TTL_SECONDS.

For SQLite (tests / local dev without Postgres), the pure in-memory dict
is used unchanged — no DB dependency.

The first-write-wins invariant is preserved: once "machine learning" is
registered, later registrations of the same normalised key are ignored
(ON CONFLICT DO NOTHING in Postgres; early-return in memory).
"""
from __future__ import annotations

import time
from threading import Lock

_REGISTRY: dict[str, str] = {}   # canonical_text → concept_entity_id
_LOCK = Lock()

# Postgres cache — rebuilt from DB at most once every 30 seconds.
_CACHE_TTL_SECONDS = 30.0
_CACHE_LOADED_AT: float = 0.0
_CACHE_VALID = False


def _is_postgres() -> bool:
    try:
        from app.db.config import get_database_settings
        return get_database_settings().database_url.startswith("postgresql")
    except Exception:
        return False


def _get_session():  # type: ignore[return]
    from app.db.engine import get_session_factory
    return get_session_factory()()


def _pg_register(items: list[tuple[str, str]]) -> None:
    if not items:
        return
    try:
        from sqlalchemy import text
        with _get_session() as session:
            with session.begin():
                for concept_text, entity_id in items:
                    session.execute(
                        text(
                            """
                            INSERT INTO public.concept_registry (concept_text, entity_id)
                            VALUES (:concept_text, :entity_id)
                            ON CONFLICT (concept_text) DO NOTHING
                            """
                        ),
                        {"concept_text": concept_text, "entity_id": entity_id},
                    )
    except Exception:
        pass  # Registry is best-effort; never fail NLP processing


def _pg_load_all() -> dict[str, str]:
    try:
        from sqlalchemy import text
        with _get_session() as session:
            rows = session.execute(
                text("SELECT concept_text, entity_id FROM public.concept_registry")
            ).all()
        return {str(row[0]): str(row[1]) for row in rows}
    except Exception:
        return {}


def _ensure_cache_fresh() -> None:
    """Refresh the in-process cache from Postgres if TTL has expired."""
    global _CACHE_LOADED_AT, _CACHE_VALID
    now = time.monotonic()
    if _CACHE_VALID and (now - _CACHE_LOADED_AT) < _CACHE_TTL_SECONDS:
        return
    db_data = _pg_load_all()
    with _LOCK:
        _REGISTRY.update(db_data)
        _CACHE_LOADED_AT = now
        _CACHE_VALID = True


def register_concepts(items: list[tuple[str, str]]) -> None:
    """Register (concept_text, concept_entity_id) pairs.

    Already-known concepts are not overwritten so the first extracted form
    of a concept wins (later extractions reuse it via the SLM prompt).
    """
    normalised = [
        (text.strip().lower(), entity_id)
        for text, entity_id in items
        if text.strip()
    ]
    if not normalised:
        return

    with _LOCK:
        new_items = [
            (concept_text, entity_id)
            for concept_text, entity_id in normalised
            if concept_text not in _REGISTRY
        ]
        for concept_text, entity_id in new_items:
            _REGISTRY[concept_text] = entity_id

    if new_items and _is_postgres():
        _pg_register(new_items)


def get_known_concepts() -> list[str]:
    """Return all registered concept texts, sorted for deterministic prompts."""
    if _is_postgres():
        _ensure_cache_fresh()
    with _LOCK:
        return sorted(_REGISTRY.keys())


def registry_size() -> int:
    if _is_postgres():
        _ensure_cache_fresh()
    with _LOCK:
        return len(_REGISTRY)


__all__ = ["register_concepts", "get_known_concepts", "registry_size"]
