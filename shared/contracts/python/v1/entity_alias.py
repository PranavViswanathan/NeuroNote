from __future__ import annotations

from pydantic import BaseModel, Field


class ConfirmEntityAliasRequest(BaseModel):
    alias_text: str = Field(min_length=1)
    canonical_entity_id: str = Field(min_length=1)
    canonical_name: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)


class ConfirmEntityAliasResponse(BaseModel):
    alias_text: str
    canonical_entity_id: str
    canonical_name: str
    confidence: float
    source: str


class EntityAliasCalibrationResponse(BaseModel):
    total_aliases: int = Field(ge=0)
    avg_confidence: float | None = None


class ResolveEntityInput(BaseModel):
    entity_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    label: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)


class ResolvedEntityOutput(BaseModel):
    source_entity_id: str
    source_text: str
    canonical_entity_id: str
    canonical_name: str
    confidence: float
    matched_layer: str


class UnresolvedEntityOutput(BaseModel):
    source_entity_id: str
    source_text: str


class ResolveEntitiesRequest(BaseModel):
    entities: list[ResolveEntityInput]


class ResolveEntitiesResponse(BaseModel):
    resolved: list[ResolvedEntityOutput]
    unresolved: list[UnresolvedEntityOutput]
