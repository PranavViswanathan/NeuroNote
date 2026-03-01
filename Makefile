.PHONY: setup setup-web check check-web test test-api test-structure test-web

UV_CACHE_DIR ?= .uv-cache

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
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run --project api --group dev pytest tests/integration tests/unit -q

test-structure:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run --project api --group dev pytest tests/unit/test_structure.py -q

test-web:
	npm --prefix web run test
