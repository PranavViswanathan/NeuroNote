from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_DIRS = [
    "api",
    "api/alembic",
    "api/alembic/versions",
    "api/src/app/db",
    "api/src/app/db/models",
    "api/src/app/db/repositories",
    "api/src/app/core",
    "api/src/app/nlp",
    "api/src/app/routes",
    "api/src/app/services",
    "shared/contracts/python/v1",
    "shared/contracts/ts/v1",
    "web/src/app",
    "web/src/app/notes/[noteId]",
    "web/src/components/editor",
    "web/src/lib/editor",
    "web/src/lib",
    "web/src/lib/orchestration",
    "web/src/lib/state",
    "web/src/lib/timing",
    "infra",
    "infra/db",
    "infra/sql",
    "tests/unit",
    "tests/integration",
    "tests/e2e",
    "tests/perf",
]

REQUIRED_FILES = [
    ".gitignore",
    "Makefile",
    "api/alembic.ini",
    "api/alembic/env.py",
    "api/alembic/script.py.mako",
    "api/alembic/versions/20260301_0001_core_tables.py",
    "api/pyproject.toml",
    "api/.env.example",
    "api/src/app/main.py",
    "api/src/app/routes/health.py",
    "api/src/app/routes/notes.py",
    "api/src/app/routes/process.py",
    "api/src/app/nlp/config.py",
    "api/src/app/nlp/entities.py",
    "api/src/app/nlp/keyphrases.py",
    "api/src/app/nlp/relations.py",
    "api/src/app/nlp/embeddings.py",
    "api/src/app/nlp/pipeline.py",
    "api/src/app/nlp/types.py",
    "api/src/app/nlp/metrics.py",
    "api/src/app/services/note_processing_service.py",
    "api/src/app/db/config.py",
    "api/src/app/db/engine.py",
    "api/src/app/db/session.py",
    "api/src/app/db/extensions.py",
    "api/src/app/db/models/base.py",
    "api/src/app/db/models/subject.py",
    "api/src/app/db/models/note.py",
    "api/src/app/db/models/block.py",
    "api/src/app/db/models/tag.py",
    "api/src/app/db/repositories/note_repository.py",
    "api/src/app/db/repositories/graph_repository.py",
    "api/src/app/db/repositories/block_repository.py",
    "api/src/app/db/repositories/subject_repository.py",
    "api/src/app/db/repositories/tag_repository.py",
    "shared/contracts/python/v1/note.py",
    "shared/contracts/python/v1/process.py",
    "shared/contracts/ts/v1/note.ts",
    "shared/contracts/ts/v1/process.ts",
    "shared/contracts/README.md",
    "web/package.json",
    "web/next-env.d.ts",
    "web/vitest.config.ts",
    "web/src/app/layout.tsx",
    "web/src/app/notes/[noteId]/page.tsx",
    "web/src/app/page.tsx",
    "web/src/components/editor/EditorToolbar.tsx",
    "web/src/components/editor/NoteEditor.tsx",
    "web/src/components/editor/TipTapEditor.tsx",
    "web/src/lib/api-client.ts",
    "web/src/lib/editor/serialize.ts",
    "web/src/lib/editor/text-extract.ts",
    "web/src/lib/orchestration/note-lifecycle.ts",
    "web/src/lib/orchestration/process-polling.ts",
    "web/src/lib/state/note-store.ts",
    "web/src/lib/timing/debounce.ts",
    "infra/docker-compose.yml",
    "infra/db/Dockerfile",
    "infra/sql/001-enable-extensions.sql",
    "tests/integration/test_graph_vector_repository.py",
    "tests/integration/test_process_api.py",
    "tests/perf/test_nlp_latency.py",
    "tests/perf/fixtures/short_200w.txt",
    "tests/perf/fixtures/medium_800w.txt",
    "tests/perf/fixtures/long_2000w.txt",
    "tests/unit/test_nlp_pipeline.py",
    "tests/unit/test_note_processing_service.py",
    "tests/unit/test_job_store.py",
    ".github/workflows/ci.yml",
]


def test_required_directories_exist() -> None:
    for rel in REQUIRED_DIRS:
        path = ROOT / rel
        assert path.is_dir(), f"Missing required directory: {rel}"


def test_required_files_exist() -> None:
    for rel in REQUIRED_FILES:
        path = ROOT / rel
        assert path.is_file(), f"Missing required file: {rel}"
