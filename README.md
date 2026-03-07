# NeuroNote

NeuroNote is a monorepo with a web frontend, a Python API service, shared contracts, and infrastructure configuration.

## Services
- `web/`: Next.js frontend with note editor, autosave orchestration, and API clients.
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

## Validate Processing Flow
1. Save a note through API:
   - `curl -X PUT http://127.0.0.1:8000/v1/notes/demo-note -H 'Content-Type: application/json' -d '{"note_id":"demo-note","content_json":{"type":"doc","content":[{"type":"paragraph","content":[{"type":"text","text":"Machine Learning improves Graph Reasoning across Notes"}]}]},"content_text":"Machine Learning improves Graph Reasoning across Notes","updated_at":"2026-03-07T12:00:00Z"}'`
2. Trigger processing:
   - `curl -X POST http://127.0.0.1:8000/v1/process-note -H 'Content-Type: application/json' -d '{"note_id":"demo-note","content_text":"Machine Learning improves Graph Reasoning across Notes","content_hash":"<sha256_of_content_text>","updated_at":"2026-03-07T12:00:00Z"}'`
   - Hash helper: `printf 'Machine Learning improves Graph Reasoning across Notes' | shasum -a 256`
3. Poll status:
   - `curl http://127.0.0.1:8000/v1/process-status/<job_id>`
4. Expected status flow:
   - `queued -> running -> completed` (or `failed` with `error` populated).
