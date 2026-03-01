from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_DIRS = [
    "api",
    "api/src/app/core",
    "api/src/app/routes",
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
    "tests/unit",
    "tests/integration",
    "tests/e2e",
    "tests/perf",
]

REQUIRED_FILES = [
    ".gitignore",
    "Makefile",
    "api/pyproject.toml",
    "api/.env.example",
    "api/src/app/main.py",
    "api/src/app/routes/health.py",
    "api/src/app/routes/notes.py",
    "api/src/app/routes/process.py",
    "api/src/app/core/note_store.py",
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
