# Shared Contracts

Versioned request/response schemas shared across API and web.

- Python (Pydantic): `shared/contracts/python/v1/`
- TypeScript interfaces: `shared/contracts/ts/v1/`

Both sides must stay in sync — update them in the same commit.

## v1 contracts

| Contract | Description |
|---|---|
| `note` | Note save/fetch/list payloads |
| `process` | Async processing queue and status |
| `block` | Block search response |
| `backlink` | Backlinks response |
| `graph` | Local/global graph and concept insight responses |
| `media` | Image upload/delete |
| `export` | Markdown export |
| `entity_alias` | Alias management and resolve preview |
| `connections` | Note connections |
| `backfill` | Startup backfill status |
