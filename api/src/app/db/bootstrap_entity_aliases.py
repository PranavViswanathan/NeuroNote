from __future__ import annotations

import json
from pathlib import Path

from app.db.engine import get_session_factory
from app.db.repositories.entity_alias_repository import EntityAliasRepository


def bootstrap_aliases_from_file(path: str) -> int:
    file_path = Path(path)
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Alias bootstrap file must contain a JSON list")

    inserted = 0
    session_factory = get_session_factory()
    with session_factory() as session:
        repository = EntityAliasRepository(session)
        with session.begin():
            for item in payload:
                if not isinstance(item, dict):
                    continue
                alias_text = str(item.get("alias_text", ""))
                canonical_entity_id = str(item.get("canonical_entity_id", ""))
                canonical_name = str(item.get("canonical_name", ""))
                if not alias_text or not canonical_entity_id or not canonical_name:
                    continue

                repository.upsert_alias(
                    alias_text=alias_text,
                    canonical_entity_id=canonical_entity_id,
                    canonical_name=canonical_name,
                    confidence=float(item.get("confidence", 1.0)),
                    source="bootstrap",
                )
                inserted += 1
    return inserted
