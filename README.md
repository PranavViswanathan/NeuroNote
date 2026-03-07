# NeuroNote

NeuroNote is a monorepo with a web frontend, a Python API service, shared contracts, and infrastructure configuration.

## Services
- `web/`: Next.js frontend with note editor, autosave orchestration, and API clients.
- `api/`: FastAPI service for health, note persistence, and note-processing endpoints.
- `shared/`: versioned request/response contracts shared across services.
- `infra/`: local infrastructure orchestration.
- `tests/`: repository-level structure and integration tests.

## Quick Start
1. Create/activate `.venv`.
2. Bootstrap base tooling via `make setup`.
3. Run checks with `make check`.
4. Run tests with `make test`.
5. For web tests, install JS deps with `npm --prefix web install` then run `npm --prefix web run test`.
6. For DB migrations, run `make db-migrate`.
7. For NLP perf guardrails, run `make test-perf`.

## Run Locally (Browser)
1. Start Postgres with extensions: `make db-up`
2. Bootstrap extensions: `make db-bootstrap-extensions`
3. Apply migrations: `make db-migrate`
4. Start API against Postgres: `make run-api-db`
5. Start web (new terminal): `make run-web`
6. Open: `http://localhost:3000/notes/sample-note`

If you want to run API without Postgres (SQLite dev mode), use `make run-api`.

## Postgres Profile (Extensions)
1. Start extension-enabled DB container (builds local image): `make db-up`
2. Bootstrap extension install attempts: `make db-bootstrap-extensions`
3. Run migrations: `make db-migrate`
4. Validate AGE/pgvector support: `make db-check-extensions`

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
