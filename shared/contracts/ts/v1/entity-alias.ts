export interface ConfirmEntityAliasRequest {
  alias_text: string;
  canonical_entity_id: string;
  canonical_name: string;
  confidence: number;
}

export interface ConfirmEntityAliasResponse {
  alias_text: string;
  canonical_entity_id: string;
  canonical_name: string;
  confidence: number;
  source: string;
}

export interface EntityAliasCalibrationResponse {
  total_aliases: number;
  avg_confidence: number | null;
}

export interface ResolveEntityInput {
  entity_id: string;
  text: string;
  label: string;
  confidence: number;
}

export interface ResolvedEntityOutput {
  source_entity_id: string;
  source_text: string;
  canonical_entity_id: string;
  canonical_name: string;
  confidence: number;
  matched_layer: string;
}

export interface UnresolvedEntityOutput {
  source_entity_id: string;
  source_text: string;
}

export interface ResolveEntitiesRequest {
  entities: ResolveEntityInput[];
}

export interface ResolveEntitiesResponse {
  resolved: ResolvedEntityOutput[];
  unresolved: UnresolvedEntityOutput[];
}
