#!/bin/sh
set -eu

cd /app

export UV_CACHE_DIR="${UV_CACHE_DIR:-/tmp/uv-cache}"
export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-/tmp/neuronote-api-venv}"
export PYTHONPATH="${PYTHONPATH:-api/src:.}"

uv sync --project api --group dev

exec "$@"
