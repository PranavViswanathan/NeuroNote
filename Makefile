.PHONY: setup setup-web check check-web test test-api test-structure test-web test-db run run-api run-web db-up db-down db-bootstrap-extensions db-migrate db-check-extensions

UV_CACHE_DIR ?= .uv-cache
DB_URL ?= postgresql+psycopg://neuronote:neuronote@127.0.0.1:5432/neuronote

setup:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv sync --project api --group dev

setup-web:
	npm --prefix web install

check:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run --project api --group dev ruff check api/src shared tests
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run --project api --group dev mypy api/src shared

check-web:
	npm --prefix web run lint
	npm --prefix web run typecheck

test: test-api test-structure

test-api:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run --project api --group dev pytest -c api/pyproject.toml tests/integration tests/unit -q

test-structure:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run --project api --group dev pytest -c api/pyproject.toml tests/unit/test_structure.py -q

test-web:
	npm --prefix web run test

test-db:
	TEST_DATABASE_URL=$(DB_URL) UV_CACHE_DIR=$(UV_CACHE_DIR) uv run --project api --group dev pytest -c api/pyproject.toml tests/integration/test_db_extensions.py tests/integration/test_graph_vector_repository.py -q

run: run-api

run-api:
	PYTHONPATH=api/src:. UV_CACHE_DIR=$(UV_CACHE_DIR) uv run --project api --group dev uvicorn app.main:app --app-dir api/src --reload --host 127.0.0.1 --port 8000

run-web:
	npm --prefix web run dev

db-up:
	docker compose -f infra/docker-compose.yml up -d --build db

db-down:
	docker compose -f infra/docker-compose.yml down

db-bootstrap-extensions:
	docker compose -f infra/docker-compose.yml exec -T db psql -U neuronote -d neuronote -f /docker-entrypoint-initdb.d/001-enable-extensions.sql

db-migrate:
	DATABASE_URL=$(DB_URL) PYTHONPATH=api/src:. UV_CACHE_DIR=$(UV_CACHE_DIR) uv run --project api --group dev alembic -c api/alembic.ini upgrade head

db-check-extensions:
	DATABASE_URL=$(DB_URL) REQUIRE_DB_EXTENSIONS=true PYTHONPATH=api/src:. UV_CACHE_DIR=$(UV_CACHE_DIR) uv run --project api --group dev python -c "from app.db.engine import get_session_factory; from app.db.extensions import check_age_capability, check_pgvector_capability, validate_required_extensions; f=get_session_factory(); s=f(); validate_required_extensions(s); check_pgvector_capability(s); check_age_capability(s); s.close(); print('AGE and pgvector checks passed')"
