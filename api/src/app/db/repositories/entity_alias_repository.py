from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.entity_alias import EntityAlias
from app.nlp.resolution.normalization import normalize_entity_text


@dataclass(frozen=True, slots=True)
class AliasRecord:
    alias_text: str
    canonical_entity_id: str
    canonical_name: str
    confidence: float
    source: str


@dataclass(frozen=True, slots=True)
class AliasCalibrationStats:
    total_aliases: int
    avg_confidence: float | None


class EntityAliasRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def _to_record(self, row: EntityAlias) -> AliasRecord:
        return AliasRecord(
            alias_text=row.alias_text,
            canonical_entity_id=row.canonical_entity_id,
            canonical_name=row.canonical_name,
            confidence=row.confidence,
            source=row.source,
        )

    def _get_row(self, alias_text: str) -> EntityAlias | None:
        normalized_alias = normalize_entity_text(alias_text)
        if not normalized_alias:
            return None
        return self._session.execute(
            select(EntityAlias).where(EntityAlias.alias_text == normalized_alias),
        ).scalar_one_or_none()

    def get_by_alias(self, alias_text: str) -> AliasRecord | None:
        row = self._get_row(alias_text)
        if row is None:
            return None
        return self._to_record(row)

    def upsert_alias(
        self,
        *,
        alias_text: str,
        canonical_entity_id: str,
        canonical_name: str,
        confidence: float,
        source: str,
    ) -> AliasRecord:
        normalized_alias = normalize_entity_text(alias_text)
        if not normalized_alias:
            raise ValueError("alias_text must contain at least one alphanumeric character")

        normalized_name = normalize_entity_text(canonical_name)
        if not normalized_name:
            raise ValueError("canonical_name must contain at least one alphanumeric character")
        if not canonical_entity_id.strip():
            raise ValueError("canonical_entity_id must not be empty")

        bounded_confidence = min(1.0, max(0.0, confidence))
        existing = self._get_row(normalized_alias)
        if existing is None:
            row = EntityAlias(
                alias_text=normalized_alias,
                canonical_entity_id=canonical_entity_id.strip(),
                canonical_name=normalized_name.title(),
                confidence=bounded_confidence,
                source=source,
            )
            self._session.add(row)
            self._session.flush()
            return self._to_record(row)

        if existing.canonical_entity_id == canonical_entity_id.strip():
            existing.canonical_name = normalized_name.title()
            existing.confidence = max(existing.confidence, bounded_confidence)
            if source == "user_confirmed":
                existing.source = source
            self._session.flush()
            return self._to_record(existing)

        should_replace = bounded_confidence > existing.confidence
        same_confidence = bounded_confidence == existing.confidence
        if same_confidence and source == "user_confirmed" and existing.source != "user_confirmed":
            should_replace = True

        if should_replace:
            existing.canonical_entity_id = canonical_entity_id.strip()
            existing.canonical_name = normalized_name.title()
            existing.confidence = bounded_confidence
            existing.source = source

        self._session.flush()
        return self._to_record(existing)

    def list_alias_index(self) -> dict[str, AliasRecord]:
        rows = self._session.execute(
            select(EntityAlias).order_by(EntityAlias.alias_text.asc()),
        ).scalars()
        return {row.alias_text: self._to_record(row) for row in rows}

    def get_calibration_stats(self) -> AliasCalibrationStats:
        total_aliases = self._session.execute(
            select(func.count()).select_from(EntityAlias),
        ).scalar_one()
        avg_confidence = self._session.execute(
            select(func.avg(EntityAlias.confidence)),
        ).scalar_one()
        rounded_avg = None
        if avg_confidence is not None:
            rounded_avg = round(float(avg_confidence), 6)
        return AliasCalibrationStats(
            total_aliases=int(total_aliases),
            avg_confidence=rounded_avg,
        )
