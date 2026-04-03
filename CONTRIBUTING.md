# Contributing to NeuroNote

## Development setup

```bash
# Start the full stack (Docker required)
make compose-up

# Apply DB migrations after pulling
make compose-migrate

# Run the test suite
make compose-test

# Stop the stack
make compose-down
```

Web: `http://localhost:3000` · API: `http://localhost:8000`

## Running checks locally

```bash
# Python: lint + type check + tests
uv run --project api --group dev ruff check api/src shared tests
uv run --project api --group dev mypy api/src shared
uv run --project api --group dev pytest tests/integration tests/unit -q

# TypeScript: type check + tests
cd web && npm run typecheck && npm run test
```

## Adding a database migration

```bash
docker compose -f infra/docker-compose.yml exec api \
  uv run alembic revision --autogenerate -m "describe your change"
make compose-migrate
```

Migration files go in `api/alembic/versions/`. Write them idempotently — they run in production.

## Shared contracts

`shared/contracts/python/v1/` and `shared/contracts/ts/v1/` must stay in sync. When you change a Python Pydantic model, update the matching TypeScript interface in the same commit.

## Pull request guidelines

- One concern per PR — keep diffs focused and reviewable
- All CI checks must pass before merge (ruff, mypy, pytest, tsc)
- New API endpoints need a matching test in `tests/integration/`
- Follow existing patterns — see `CLAUDE.md` for architectural decisions
