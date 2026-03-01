from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_DIRS = [
    "api",
    "api/src/app/routes",
    "shared/contracts/python/v1",
    "shared/contracts/ts/v1",
    "web/src/app",
    "web/src/lib",
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
    "api/src/app/routes/process.py",
    "shared/contracts/python/v1/process.py",
    "shared/contracts/ts/v1/process.ts",
    "shared/contracts/README.md",
    "web/package.json",
    "web/src/app/page.tsx",
    "web/src/lib/api-client.ts",
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
