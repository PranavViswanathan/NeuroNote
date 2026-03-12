# Shared Contracts

Versioned request/response schemas shared across services.

- Python contracts: `shared/contracts/python/v1/`
- TypeScript contracts: `shared/contracts/ts/v1/`

Current `v1` contracts:
- `process`: async note processing queue and status payloads.
- `note`: note save/fetch payloads (`note_title`, JSON content, plain text) used by debounced autosave.
- `entity_alias`: alias confirmation, calibration metrics, and resolve preview payloads.
- `backfill`: startup backfill status payloads.
