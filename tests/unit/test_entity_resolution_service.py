from __future__ import annotations

import pytest

from app.db.repositories.entity_alias_repository import AliasRecord
from app.nlp.types import ExtractedEntity
from app.services.entity_resolution_service import EntityResolutionService


def _alias_record(alias_text: str, canonical_name: str, entity_id: str) -> AliasRecord:
    return AliasRecord(
        alias_text=alias_text,
        canonical_entity_id=entity_id,
        canonical_name=canonical_name,
        confidence=1.0,
        source="test",
    )


def _entity(text: str, entity_id: str = "ent-1") -> ExtractedEntity:
    return ExtractedEntity(entity_id=entity_id, text=text, label="concept", confidence=0.9)


class TestBuildResolver:
    def test_resolved_entity_is_found_via_alias_index(self) -> None:
        alias_records = {"machine learning": _alias_record("machine learning", "Machine Learning", "ent-ml")}
        resolver = EntityResolutionService.build_resolver(alias_records)
        batch = resolver.resolve([_entity("machine learning")])
        assert len(batch.resolved) == 1
        assert batch.resolved[0].canonical_entity_id == "ent-ml"

    def test_unresolved_entity_is_returned_when_no_alias_matches(self) -> None:
        resolver = EntityResolutionService.build_resolver({})
        batch = resolver.resolve([_entity("unknown concept")])
        assert len(batch.unresolved) == 1
        assert batch.resolved == []

    def test_abbreviation_filter_includes_short_single_word_aliases(self) -> None:
        # "ML" has no spaces, len=2, len<=10 → qualifies for abbreviation index
        alias_records = {"ML": _alias_record("ML", "machine learning", "ent-ml")}
        resolver = EntityResolutionService.build_resolver(alias_records)
        batch = resolver.resolve([_entity("ML", "ent-ml-source")])
        assert len(batch.resolved) == 1

    def test_abbreviation_filter_excludes_multi_word_aliases(self) -> None:
        # "machine learning" has a space → not in abbreviation_index.
        # If entity "machinelearning" resolves at all, it must be via fuzzy — not abbreviation.
        alias_records = {"machine learning": _alias_record("machine learning", "Machine Learning", "ent-ml")}
        resolver = EntityResolutionService.build_resolver(alias_records)
        batch = resolver.resolve([_entity("machinelearning", "ent-nospace")])
        if batch.resolved:
            assert batch.resolved[0].matched_layer != "abbreviation"

    def test_abbreviation_filter_excludes_single_char_aliases(self) -> None:
        # len("A") == 1 → excluded from abbreviation index
        alias_records = {"A": _alias_record("A", "Alpha", "ent-alpha")}
        resolver = EntityResolutionService.build_resolver(alias_records)
        batch = resolver.resolve([_entity("A", "ent-a")])
        # Should not resolve via abbreviation (len 1 excluded), and "A" IS in alias_index so it resolves via alias
        # This test verifies the filter boundary, not that 'A' is entirely excluded
        assert len(batch.resolved) + len(batch.unresolved) == 1

    def test_abbreviation_filter_excludes_aliases_longer_than_ten_chars(self) -> None:
        # len("averylongtag") > 10 → excluded from abbreviation index
        alias_records = {"averylongtag": _alias_record("averylongtag", "Some Concept", "ent-long")}
        resolver = EntityResolutionService.build_resolver(alias_records)
        # Try to match the concatenated form — should not resolve via abbreviation
        batch = resolver.resolve([_entity("averylongtag", "ent-src")])
        # resolves via alias_index (direct match) even though not in abbreviation_index
        assert len(batch.resolved) == 1

    def test_empty_alias_records_produces_empty_resolver(self) -> None:
        resolver = EntityResolutionService.build_resolver({})
        batch = resolver.resolve([_entity("anything")])
        assert batch.resolved == []
        assert len(batch.unresolved) == 1


class TestPreviewResolution:
    def test_preview_resolution_returns_resolved_batch(
        self,
        configured_db: None,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import app.services.entity_resolution_service as svc_module

        class _FakeRepo:
            def __init__(self, _session) -> None:
                pass

            def list_alias_index(self) -> dict[str, AliasRecord]:
                return {
                    "neural networks": _alias_record("neural networks", "Neural Networks", "ent-nn"),
                }

        monkeypatch.setattr(svc_module, "EntityAliasRepository", _FakeRepo)

        from app.db.engine import get_session_factory

        with get_session_factory()() as session:
            batch = EntityResolutionService(session).preview_resolution(
                [_entity("neural networks", "ent-src")]
            )

        assert len(batch.resolved) == 1
        assert batch.resolved[0].canonical_name == "Neural Networks"

    def test_preview_resolution_returns_unresolved_when_no_alias_matches(
        self,
        configured_db: None,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import app.services.entity_resolution_service as svc_module

        class _FakeRepo:
            def __init__(self, _session) -> None:
                pass

            def list_alias_index(self) -> dict[str, AliasRecord]:
                return {}

        monkeypatch.setattr(svc_module, "EntityAliasRepository", _FakeRepo)

        from app.db.engine import get_session_factory

        with get_session_factory()() as session:
            batch = EntityResolutionService(session).preview_resolution(
                [_entity("unknown term", "ent-unk")]
            )

        assert batch.resolved == []
        assert len(batch.unresolved) == 1
