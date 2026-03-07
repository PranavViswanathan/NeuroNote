# Decisions Log (Non-Plan Additions)

This file captures implementation notes and additions that are useful context but do not change the executable project plan.

Architectural decisions are tracked in `docs/plan.md` under `Architecture Decisions`.

## 2026-03-07
- Documentation policy alignment:
  - `docs/decisions.md` stores non-plan additions and operational notes.
  - `docs/plan.md` remains the source of truth for architecture and implementation sequencing.
- Hardening follow-through notes:
  - Removed unused placeholder package file `api/src/app/models/__init__.py`.
  - Removed unused web note state helper in `web/src/lib/state/note-store.ts` after TipTap path consolidation.
- Tooling/runtime note:
  - In this environment, `uv run` intermittently panics with a system configuration error.
  - Validation fallback used `api/.venv/bin/ruff`, `api/.venv/bin/mypy`, and `api/.venv/bin/pytest` with equivalent scope.

## 2026-03-07 (Containerized Workflow)
- Containerized orchestration addition:
  - Added a Docker Compose workflow where API execution remains `uv`-based but runs inside containers.
  - Added `infra/api/Dockerfile` and `infra/scripts/api-entrypoint.sh` to run `uv sync` before API commands.
  - Added compose-focused Make targets (`compose-up`, `compose-check`, `compose-test`, `compose-migrate`, etc.).
  - Added `web` service to compose stack for browser-level local validation from one command.
  - Added configurable port bindings (`DB_PORT`, `API_PORT`, `WEB_PORT`) to avoid host port conflicts.
  - Updated documentation to make compose-first workflow the default run/check/test path.
