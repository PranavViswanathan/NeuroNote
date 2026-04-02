# NeuroNote — Claude Code Context

## What this project is

NeuroNote is a local-first AI-powered knowledge base. Users write notes in a rich TipTap editor; the system automatically extracts concepts and relations with an NLP pipeline (rule-based, spaCy, or Claude-enhanced), stores them in an Apache AGE property graph, and lets users explore the knowledge graph interactively. Clicking any concept node opens an AI-generated insight panel grounded in the user's own notes.

## Monorepo layout

```
api/          FastAPI backend (Python 3.12, uv)
web/          Next.js 14 frontend (TypeScript)
shared/       Versioned contracts (Python Pydantic + TypeScript interfaces, mirrored)
infra/        Docker Compose stack
tests/        Python test suite (pytest)
docs/         Architecture decisions, implementation plan, UX research
```

## Running the project

```bash
make compose-up       # start full stack (Docker required)
make compose-migrate  # apply DB migrations after pulling
make compose-check    # API health checks
make compose-test     # API test suite
make compose-down     # stop
```

Web: `http://localhost:3000` · API: `http://localhost:8000`

## Key architectural decisions

### API
- **FastAPI** with async route handlers; `Depends(get_db_session)` for DB injection
- **SQLAlchemy** ORM (sync sessions, not async) — the DB layer is synchronous even though route handlers are `async def`
- **Apache AGE** (typed property graph in PostgreSQL) — Cypher queries via raw SQL with `LOAD 'age'` + `ag_catalog` search path
- **Schema is migration-first** — `DB_AUTO_CREATE=false`; always run `make compose-migrate` after pulling new migrations
- **Alembic** for migrations — 10 migrations in `api/alembic/versions/`
- **pgvector** for semantic embeddings — stored on entity nodes
- **Shared contracts** — Pydantic models in `shared/contracts/python/v1/`; always update the matching TypeScript file in `shared/contracts/ts/v1/` when changing Python contracts, and vice versa

### NLP pipeline (`api/src/app/nlp/`)
- `NoteNlpPipeline` in `pipeline.py` — entry point; reads `NLP_EXTRACTION_PROFILE` env var
- Three profiles: `rule-only` (default), `hybrid-spacy`, `llm-enhanced`
- LRU extraction cache keyed by `content_hash` — notes with identical text share one result
- `SLMExtractor` (`slm_extractor.py`) wraps Claude API for `llm-enhanced` profile — uses sync `anthropic.Anthropic`
- `ConceptInsightService` (`services/concept_insight_service.py`) wraps Claude for on-demand insight generation — uses async `anthropic.AsyncAnthropic`

### Graph sync (`api/src/app/services/graph_sync_service.py`)
- Delete-and-replace semantics: on each note save, all AGE nodes/edges sourced from that note are deleted then re-created
- `GraphSyncPayload` carries entities, keyphrases, relations, resolved_entities, embedding, entity_mentions
- Block-scoped `MENTIONS` edges: each edge carries `source_note_id`, `mention_text`, `start_offset`, `end_offset`

### Frontend
- **Next.js App Router** — all client components use `"use client"`
- **TipTap** editor with custom extensions: `mathInline`, `mathBlock`, `wikiLink`, `blockRef`, `image`
- **D3.js** for graph rendering (`D3GraphCanvas.tsx`) — force-directed simulation
- **Autosave orchestration** (`web/src/lib/orchestration/`) — 800ms debounce for save, 3s for processing queue trigger
- **API client** (`web/src/lib/api-client.ts`) — typed fetch wrappers using shared TS contracts
- **Design tokens** — all colors, font sizes, z-indices, spacing use CSS custom properties from `globals.css`; never use hardcoded hex colors or bare `rem` values in new CSS

### Logging
- Root logger format uses `%(request_id)s` — injected by `_RequestIdFilter` in `main.py`
- `httpx` logger is set to `WARNING` to suppress HTTP request INFO noise from background threads
- Background threads (startup backfill, NLP processing) do not carry `request_id` — the filter provides `-` as default

## Important patterns to follow

### Adding a new API route
1. Create `api/src/app/routes/<name>.py` with `router = APIRouter()`
2. Add Pydantic response model to `shared/contracts/python/v1/`
3. Add matching TypeScript interface to `shared/contracts/ts/v1/`
4. Register in `api/src/app/main.py`: `app.include_router(router, prefix="/v1")`
5. Add `fetchXxx()` wrapper to `web/src/lib/api-client.ts`

### Adding a DB migration
```bash
docker compose -f infra/docker-compose.yml exec api uv run alembic revision --autogenerate -m "describe change"
make compose-migrate
```
Migration files go in `api/alembic/versions/` — naming convention: `YYYYMMDD_NNNN_<description>.py`

### Shared contracts
Both sides must stay in sync. When you change `shared/contracts/python/v1/graph.py`, update `shared/contracts/ts/v1/graph.ts` in the same commit.

### CSS design tokens
All new CSS must use tokens, not hardcoded values:
- Colors: `var(--text-strong)`, `var(--accent)`, `var(--panel-bg)`, `var(--danger)`, etc.
- Font sizes: `var(--text-xs)` (0.75rem), `var(--text-sm)` (0.8rem), `var(--text-base)` (0.875rem)
- Z-indices: `var(--z-dropdown)`, `var(--z-modal)`, `var(--z-toast)`

## Test suite

```bash
make compose-test          # full Python test suite
make compose-test-db       # PostgreSQL extension tests only
cd web && npx vitest run   # frontend tests
```

Test files: `tests/unit/`, `tests/integration/`, `tests/perf/`, `tests/e2e/`
Frontend tests: `web/src/**/*.test.tsx`

## Environment variables

| Variable | Where set | Purpose |
|---|---|---|
| `DATABASE_URL` | `api/.env` | PostgreSQL connection string |
| `NLP_EXTRACTION_PROFILE` | `api/.env` or compose | `rule-only` / `hybrid-spacy` / `llm-enhanced` |
| `NLP_MODEL_NAME` | `api/.env` or compose | spaCy model (e.g. `spacy:en_core_web_sm`) |
| `NLP_ENTITY_SEED_TERMS` | `api/.env` or compose | Comma-separated terms for deterministic seeding |
| `ANTHROPIC_API_KEY` | `api/.env` or compose | Enables LLM extraction + concept insights |
| `NEXT_PUBLIC_API_BASE_URL` | `web/.env` | API URL for the browser (`http://localhost:8000`) |

## Files to be careful with

- `api/src/app/main.py` — app bootstrap, logging config, lifespan hooks, router registration
- `api/alembic/versions/` — migrations are irreversible in production; write idempotently
- `shared/contracts/python/v1/graph.py` + `shared/contracts/ts/v1/graph.ts` — must stay in sync
- `web/src/app/globals.css` — all design tokens live here; circular variable references will silently break styling
- `infra/docker-compose.yml` — service definitions, port mappings, env var injection
