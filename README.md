# NeuroNote

NeuroNote is a monorepo with a web frontend, a Python API service, shared contracts, and infrastructure configuration.

## Services
- `web/`: Next.js frontend with note editor (`note_title` + content), autosave orchestration, and API clients.
- `api/`: FastAPI service for health, note persistence, and note-processing endpoints.
- `shared/`: versioned request/response contracts shared across services.
- `infra/`: local infrastructure orchestration.
- `tests/`: repository-level structure and integration tests.

## Project Docs
- `docs/codex.md`: project working instructions.
- `docs/plan.md`: executable implementation plan and architecture decisions.
- `docs/initial_scoping_doc.md`: original scoping and requirements baseline.
- `docs/decisions.md`: non-plan implementation notes and operational decisions.

## Recommended Workflow (Docker Compose + uv)
This is the default way to run NeuroNote now. API commands still use `uv`, but inside Docker containers.

### Quick Start
1. Ensure Docker Desktop is running.
2. Start full stack:
   - `make compose-up`
   - If default ports are busy:
     - `WEB_PORT=3001 API_PORT=8001 DB_PORT=5433 make compose-up`
3. Apply migrations:
   - `make compose-migrate`
4. Run API checks:
   - `make compose-check`
5. Run API tests:
   - `make compose-test`
6. Open browser:
   - `http://localhost:3000/notes/sample-note`
7. Stop stack:
   - `make compose-down`

Schema ownership is migration-first:
- `DB_AUTO_CREATE=false` in compose API runtime.
- PostgreSQL auto-create is disabled in app startup logic.
- Migration `20260307_0002` is idempotent for pre-existing `entity_aliases` tables.
- Migration `20260311_0003` is idempotent for pre-existing `notes.note_title` columns.

### Common Commands
- API checks: `make compose-check`
- API tests: `make compose-test`
- PostgreSQL extension tests: `make compose-test-db`
- Bootstrap DB extensions manually: `make compose-bootstrap-extensions`
- Stream logs: `make compose-logs`

### Default URLs
- Web: `http://localhost:3000`
- API: `http://localhost:8000`
- Postgres: `localhost:5432`

If you override `WEB_PORT` / `API_PORT` / `DB_PORT`, use those port numbers in URLs and DB clients.

## Local Fallback (Native uv)
Use this only if you explicitly want a non-container local run.

1. `make setup`
2. `make check`
3. `make test`
4. `make run-api-db` and `make run-web`

`make run-api` still enables sqlite auto-create for quick local-only bootstrapping.

## Validate Processing Flow
1. Save a note through API:
   - Use heredoc payload to avoid shell-escaped JSON issues:
```bash
curl -sS -X PUT http://127.0.0.1:8000/v1/notes/demo-note \
  -H 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{"note_id":"demo-note","note_title":"Graph Reasoning Notes","content_json":{"type":"doc","content":[{"type":"paragraph","content":[{"type":"text","text":"Machine Learning improves Graph Reasoning across Notes"}]}]},"content_text":"Machine Learning improves Graph Reasoning across Notes","updated_at":"2026-03-07T12:00:00Z"}
JSON
```
2. Trigger processing:
   - Hash helper: `HASH=$(printf 'Graph Reasoning Notes\n\nMachine Learning improves Graph Reasoning across Notes' | shasum -a 256 | awk '{print $1}')`
```bash
curl -sS -X POST http://127.0.0.1:8000/v1/process-note \
  -H 'Content-Type: application/json' \
  -d "{\"note_id\":\"demo-note\",\"content_text\":\"Graph Reasoning Notes\n\nMachine Learning improves Graph Reasoning across Notes\",\"content_hash\":\"$HASH\",\"updated_at\":\"2026-03-07T12:00:00Z\"}"
```
3. Poll status:
   - `curl http://127.0.0.1:8000/v1/process-status/<job_id>`
4. Expected status flow:
   - `queued -> running -> completed` (or `failed` with `error` populated).

## Validate Startup Backfill Status
After API startup (PostgreSQL mode), check async backfill progress:

```bash
curl -sS http://127.0.0.1:8000/v1/backfill-status
```

Response shape:
- `total_notes`
- `processed_notes`
- `failed_notes`
- `in_progress`

## Validate Entity Resolution Flow
1. Confirm a canonical alias:
```bash
curl -sS -X POST http://127.0.0.1:8000/v1/entity-aliases/confirm \
  -H 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{"alias_text":"ML","canonical_entity_id":"concept-machine-learning","canonical_name":"Machine Learning","confidence":0.95}
JSON
```
2. Preview resolution output (resolved + unresolved):
```bash
curl -sS -X POST http://127.0.0.1:8000/v1/entity-aliases/resolve-preview \
  -H 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{"entities":[{"entity_id":"entity-1","text":"ML","label":"acronym","confidence":0.8},{"entity_id":"entity-2","text":"xqzv_123","label":"acronym","confidence":0.4}]}
JSON
```
3. Check calibration metrics:
   - `curl http://127.0.0.1:8000/v1/entity-aliases/calibration`
