# NeuroNote

NeuroNote is a monorepo with a web frontend, a Python API service, shared contracts, and infrastructure configuration.

## Services
- `web/`: frontend shell and client-side API helpers.
- `api/`: FastAPI service for health and note-processing endpoints.
- `shared/`: versioned request/response contracts shared across services.
- `infra/`: local infrastructure orchestration.
- `tests/`: repository-level structure and integration tests.

## Quick Start
1. Create/activate `.venv`.
2. Bootstrap base tooling via `make setup`.
3. Run checks with `make check`.
4. Run tests with `make test`.
