FROM postgres:16

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       postgresql-16-age \
       postgresql-16-pgvector \
    && rm -rf /var/lib/apt/lists/*

# Bake the extension-enable script in so it runs on first DB init.
# In Docker Compose the sql/ dir is volume-mounted; this COPY makes it
# self-contained for Railway and other non-compose deployments.
COPY sql/001-enable-extensions.sql /docker-entrypoint-initdb.d/001-enable-extensions.sql
