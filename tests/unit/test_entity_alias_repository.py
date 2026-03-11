from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.repositories.entity_alias_repository import EntityAliasRepository


def test_upsert_alias_inserts_new_alias(db_session: Session) -> None:
    repository = EntityAliasRepository(db_session)

    with db_session.begin():
        record = repository.upsert_alias(
            alias_text="ML",
            canonical_entity_id="concept-machine-learning",
            canonical_name="Machine Learning",
            confidence=0.9,
            source="user_confirmed",
        )

    assert record.alias_text == "ml"
    assert record.canonical_entity_id == "concept-machine-learning"
    assert record.confidence == 0.9


def test_alias_lookup_short_circuits_through_repository_index(db_session: Session) -> None:
    repository = EntityAliasRepository(db_session)

    with db_session.begin():
        repository.upsert_alias(
            alias_text="Machine-Learning",
            canonical_entity_id="concept-machine-learning",
            canonical_name="Machine Learning",
            confidence=0.88,
            source="bootstrap",
        )

    alias_index = repository.list_alias_index()
    assert "machine learning" in alias_index
    assert alias_index["machine learning"].canonical_entity_id == "concept-machine-learning"


def test_upsert_alias_conflict_policy_keeps_higher_confidence_mapping(db_session: Session) -> None:
    repository = EntityAliasRepository(db_session)

    with db_session.begin():
        repository.upsert_alias(
            alias_text="AI",
            canonical_entity_id="concept-artificial-intelligence",
            canonical_name="Artificial Intelligence",
            confidence=0.95,
            source="user_confirmed",
        )

    with db_session.begin():
        result = repository.upsert_alias(
            alias_text="AI",
            canonical_entity_id="concept-applied-inference",
            canonical_name="Applied Inference",
            confidence=0.6,
            source="bootstrap",
        )

    assert result.canonical_entity_id == "concept-artificial-intelligence"
    assert result.canonical_name == "Artificial Intelligence"
    assert result.confidence == 0.95


def test_upsert_alias_conflict_policy_replaces_with_higher_confidence_mapping(db_session: Session) -> None:
    repository = EntityAliasRepository(db_session)

    with db_session.begin():
        repository.upsert_alias(
            alias_text="NLP",
            canonical_entity_id="concept-natural-language-processing",
            canonical_name="Natural Language Processing",
            confidence=0.55,
            source="bootstrap",
        )

    with db_session.begin():
        result = repository.upsert_alias(
            alias_text="NLP",
            canonical_entity_id="concept-neural-language-processing",
            canonical_name="Neural Language Processing",
            confidence=0.9,
            source="user_confirmed",
        )

    assert result.canonical_entity_id == "concept-neural-language-processing"
    assert result.canonical_name == "Neural Language Processing"
    assert result.confidence == 0.9


def test_get_calibration_stats_returns_total_and_average(db_session: Session) -> None:
    repository = EntityAliasRepository(db_session)

    with db_session.begin():
        repository.upsert_alias(
            alias_text="ML",
            canonical_entity_id="concept-machine-learning",
            canonical_name="Machine Learning",
            confidence=0.8,
            source="bootstrap",
        )
        repository.upsert_alias(
            alias_text="DL",
            canonical_entity_id="concept-deep-learning",
            canonical_name="Deep Learning",
            confidence=1.0,
            source="user_confirmed",
        )

    stats = repository.get_calibration_stats()
    assert stats.total_aliases == 2
    assert stats.avg_confidence == 0.9
