FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/tmp/neuronote-api-venv \
    UV_CACHE_DIR=/tmp/uv-cache

RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy only the files needed to resolve and install dependencies.
# The full source tree is mounted at runtime via docker-compose volumes,
# but the venv lives at /tmp/neuronote-api-venv (outside /app) so it
# persists across volume mounts and is not reinstalled on every start.
COPY api/pyproject.toml api/pyproject.toml
COPY api/uv.lock api/uv.lock
RUN uv sync --project api --group dev --frozen

COPY infra/scripts/api-entrypoint.sh /usr/local/bin/api-entrypoint.sh
RUN chmod +x /usr/local/bin/api-entrypoint.sh

ENTRYPOINT ["api-entrypoint.sh"]
