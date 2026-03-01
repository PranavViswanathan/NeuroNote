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

## Run Locally (Browser)
1. Start API: `make run-api`
2. Start web (new terminal): `make run-web`
3. Open: `http://localhost:3000/notes/sample-note`

## Postgres Profile (Extensions)
1. Start extension-enabled DB container (builds local image): `make db-up`
2. Bootstrap extension install attempts: `make db-bootstrap-extensions`
3. Run migrations: `make db-migrate`
4. Validate AGE/pgvector support: `make db-check-extensions`
