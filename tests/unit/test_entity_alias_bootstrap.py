from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.db.bootstrap_entity_aliases import bootstrap_aliases_from_file
from app.db.engine import get_session_factory
from app.db.repositories.entity_alias_repository import EntityAliasRepository


@pytest.mark.usefixtures("configured_db")
def test_bootstrap_aliases_from_file_imports_valid_records(tmp_path: Path) -> None:
    payload = [
        {
            "alias_text": "ML",
            "canonical_entity_id": "concept-machine-learning",
            "canonical_name": "Machine Learning",
            "confidence": 0.9,
        },
        {
            "alias_text": "AI",
            "canonical_entity_id": "concept-artificial-intelligence",
            "canonical_name": "Artificial Intelligence",
            "confidence": 0.8,
        },
    ]
    file_path = tmp_path / "aliases.json"
    file_path.write_text(json.dumps(payload), encoding="utf-8")

    inserted = bootstrap_aliases_from_file(str(file_path))
    assert inserted == 2

    session_factory = get_session_factory()
    with session_factory() as session:
        repository = EntityAliasRepository(session)
        ml = repository.get_by_alias("ml")
        ai = repository.get_by_alias("ai")

    assert ml is not None
    assert ml.canonical_entity_id == "concept-machine-learning"
    assert ai is not None
    assert ai.canonical_entity_id == "concept-artificial-intelligence"
