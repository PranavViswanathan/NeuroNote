from __future__ import annotations

from app.nlp.resolution.resolver import CanonicalAlias, EntityResolver
from app.nlp.types import ExtractedEntity


def test_resolver_short_circuits_on_alias_table_match() -> None:
    resolver = EntityResolver(
        alias_index={
            "ml": CanonicalAlias(
                canonical_entity_id="concept-machine-learning",
                canonical_name="Machine Learning",
            )
        }
    )

    batch = resolver.resolve(
        [
            ExtractedEntity(
                entity_id="entity-ml",
                text="ML",
                label="acronym",
                confidence=0.75,
            )
        ]
    )

    assert len(batch.resolved) == 1
    assert not batch.unresolved
    assert batch.resolved[0].canonical_entity_id == "concept-machine-learning"
    assert batch.resolved[0].matched_layer == "alias_table"


def test_resolver_uses_abbreviation_layer_then_alias_lookup() -> None:
    resolver = EntityResolver(
        alias_index={
            "machine learning": CanonicalAlias(
                canonical_entity_id="concept-machine-learning",
                canonical_name="Machine Learning",
            )
        },
        abbreviation_index={"ml": "machine learning"},
    )

    batch = resolver.resolve(
        [
            ExtractedEntity(
                entity_id="entity-ml",
                text="ML",
                label="acronym",
                confidence=0.75,
            )
        ]
    )

    assert len(batch.resolved) == 1
    assert batch.resolved[0].canonical_name == "Machine Learning"
    assert batch.resolved[0].matched_layer == "abbreviation"


def test_resolver_uses_fuzzy_layer_for_near_match() -> None:
    resolver = EntityResolver(
        alias_index={
            "machine learning": CanonicalAlias(
                canonical_entity_id="concept-machine-learning",
                canonical_name="Machine Learning",
            )
        },
        fuzzy_threshold=0.8,
    )

    batch = resolver.resolve(
        [
            ExtractedEntity(
                entity_id="entity-ml-typo",
                text="Machine Learnng",
                label="proper_noun",
                confidence=0.8,
            )
        ]
    )

    assert len(batch.resolved) == 1
    assert batch.resolved[0].canonical_entity_id == "concept-machine-learning"
    assert batch.resolved[0].matched_layer == "fuzzy"


def test_resolver_uses_embedding_layer_when_fuzzy_is_strict() -> None:
    resolver = EntityResolver(
        alias_index={
            "graph databases": CanonicalAlias(
                canonical_entity_id="concept-graph-databases",
                canonical_name="Graph Databases",
            )
        },
        fuzzy_threshold=1.01,
        embedding_threshold=0.0,
    )

    batch = resolver.resolve(
        [
            ExtractedEntity(
                entity_id="entity-graph-db",
                text="Graph Database",
                label="proper_noun",
                confidence=0.8,
            )
        ]
    )

    assert len(batch.resolved) == 1
    assert batch.resolved[0].canonical_entity_id == "concept-graph-databases"
    assert batch.resolved[0].matched_layer == "embedding"


def test_resolver_reports_unresolved_entities() -> None:
    resolver = EntityResolver(alias_index={})

    batch = resolver.resolve(
        [
            ExtractedEntity(
                entity_id="entity-unknown",
                text="xqzv_123",
                label="acronym",
                confidence=0.5,
            )
        ]
    )

    assert not batch.resolved
    assert len(batch.unresolved) == 1
    assert batch.unresolved[0].source_entity_id == "entity-unknown"
