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

## 2026-03-07 (Epic E4 Delivery Notes)
- Added `entity_aliases` persistence for canonical mapping memory and conflict handling.
- Added resolver preview API endpoint to expose unresolved entities for optional confirmation flow.
- Added alias bootstrap utility (`api/src/app/db/bootstrap_entity_aliases.py`) for seed imports.

## 2026-03-10 (Permanent Migration Safety)
- Set `DB_AUTO_CREATE` default to `false` to favor migration-owned schema lifecycle.
- Added PostgreSQL startup guard so `initialize_database()` does not run `create_all` for Postgres URLs.
- Made Alembic revision `20260307_0002` idempotent when `entity_aliases` and indexes already exist.

## 2026-03-10 (Processing Transaction Safety)
- Fixed `NoteProcessingService` transaction scope so alias index reads and graph writes execute under one explicit transaction.
- Added unit regression test for the `A transaction is already begun on this Session.` failure path.

## 2026-03-11 (Epic E5 + Title Flow Delivery Notes)
- Added `note_title` to note persistence, contracts, API payloads, and editor autosave flow.
- Added idempotent migration `20260311_0003_note_title` for existing databases.
- Added graph sync delete-and-replace by `source_note_id` and typed graph-edge writing.
- Added startup async backfill service and `/v1/backfill-status` API route.
- Added dedicated unit/integration coverage for graph sync relation collapse, backfill status, startup backfill async behavior, and note-title migration.
- Local web test runtime still has an esbuild platform mismatch in `web/node_modules`; validated frontend tests in compose runtime (`docker compose ... run --rm web npm run test`).

## 2026-03-12 (Embedding Schema Safety)
- Fixed graph embedding persistence to always target `public.note_embeddings` instead of relying on session `search_path`.
- Added compatibility copy-forward from `ag_catalog.note_embeddings` to `public.note_embeddings` inside repository table bootstrap.
- Added regression test ensuring note embeddings land in `public` schema.

## 2026-03-12 (Commercial Roadmap Rebaseline Notes)
- Planning rebaseline:
  - Legacy unfinished epics (`E6-E9`) are marked deprecated in `docs/plan.md`.
  - New authoritative commercial-track roadmap is `E6-E12` (`Workspace`, `Editor Commands`, `Math/Images/Export`, `UX Hardening`, `Hybrid Workflows`, `Guided Graph`, `Launch Hardening`).
- Product scope alignment notes:
  - Canonical editor persistence remains TipTap JSON; markdown remains export capability, not canonical storage.
  - v1 editor target is Notion-like core blocks and command UX, not full Notion parity.
  - v1 math target is LaTeX inline + block.
  - v1 image target is upload API + local disk with storage adapter boundary for future object storage.
  - v1 graph target is local-first + guided global on explicit action.

## 2026-03-12 (Epic E6 Delivery Notes)
- Added workspace shell (`web/src/components/workspace/NotesWorkspace.tsx`) and switched root/note routes to workspace-driven navigation.
- Added note list client capabilities (`listNotes`, `deleteNote`) and maintained existing note save/get API boundaries.
- Added `note_tags` association model/migration and organization metadata fields on notes (`subject_id`, `is_pinned`, `is_archived`).
- Added organization-aware list semantics in API with default archive exclusion and explicit query controls.
- Validation/runtime notes:
  - Local `uv run` remains unstable in this environment (panic); Python checks/tests validated through `api/.venv/bin/*`.
  - Local host `vitest` remains blocked by platform-specific `esbuild` mismatch; web tests validated in compose Node 20 runtime.

## 2026-03-12 (Workspace UI Stabilization)
- Reworked workspace layout to a commercial baseline with explicit sidebar/editor panels and app-wide styling in `web/src/app/globals.css`.
- Moved note destructive/edit actions to right-click context menu (`Rename`, `Pin/Unpin`, `Delete`) and removed always-visible rename/delete header controls.
- Split list rendering so pinned notes live in `Pinned` while `All notes` excludes pinned entries, preventing duplicate visual rows.
- Added explicit TipTap shell/editor classes and ProseMirror styles to enforce immediate text visibility and multiline editing ergonomics.
- Added regression coverage for context-menu actions, pinned/all list separation, duplicate-create guard, and TipTap initial content rendering.

## 2026-03-12 (Workspace UX Hardening)
- Changed filter behavior to debounced reactive refresh (search/subject/tag/archive) instead of blur-triggered refresh.
- Added note-row content preview snippets to improve scanability and reduce open-click churn.
- Added keyboard access path for note actions (`Shift+F10` / `ContextMenu` key opens note context menu).
- Added explicit loading message for list fetches and retry panel for fetch errors.
- Added regression tests for debounce refresh, preview rendering, keyboard context menu opening, loading state, and retry success flow.

## 2026-03-12 (Epic E7 Delivery Notes)
- Added editor command registry (`web/src/lib/editor/commands.ts`) and shared command filtering/slash-trigger matching helpers.
- Added wiki-link parsing/normalization helpers (`web/src/lib/editor/wiki-links.ts`) with regression coverage.
- Upgraded TipTap editor UX:
  - command toolbar for core blocks,
  - slash command menu,
  - `Cmd/Ctrl+K` command palette fallback,
  - `[[wiki-link]]` autocomplete with quick-create option for unresolved titles.
- Added NoteEditor wiring for wiki-link suggestion lookup and unresolved linked-note creation through existing note APIs.
- Validation/runtime notes:
  - local host vitest remains blocked by platform-specific `esbuild` mismatch;
  - canonical validation executed in compose runtime (`docker compose -f infra/docker-compose.yml run --rm web npm run test`);
  - web typecheck passed and compose web tests passed (`45` tests).

## 2026-03-12 (Slash Enter Command Fix)
- Fixed slash-command Enter behavior to use TipTap `editorProps.handleKeyDown` instead of relying only on wrapper `onKeyDown`.
- Added deterministic key-action resolver (`web/src/lib/editor/key-handlers.ts`) with regression tests.
- Result: pressing Enter on slash command now executes selected command transform instead of inserting a newline.

## 2026-03-13 (Epic E8 Delivery Notes)
- Added media and export API surface:
  - `POST /v1/media/uploads` (JSON base64 image payload),
  - `GET /v1/media/{asset_id}`,
  - `DELETE /v1/media/{asset_id}`,
  - `GET /v1/notes/{note_id}/export/markdown` (zip download).
- Added `note_assets` migration/model/repository with note-save reconciliation that marks unreferenced assets deleted and removes local files.
- Added markdown renderer for deterministic math/image export output.
- Added TipTap math/image command entries and custom node extensions for persisted math/image content.
- Validation/runtime notes:
  - local `uv run` panic persists in this environment; validation used `api/.venv/bin/{pytest,ruff,mypy}`.
  - local vitest/esbuild mismatch persists; canonical web validation executed in compose runtime.
  - Added compatibility guard for pre-migration DBs: note-save reconciliation no-ops when `note_assets` is absent, while media endpoints return explicit migration-required (`503`) responses.

## 2026-03-13 (Math Rendering Hardening)
- Math input normalization now strips optional `$...$` / `$$...$$` delimiters before persistence and rendering.
- Inline authoring now supports direct typing of `$...$` which auto-converts to a `mathInline` node.
- This closes the UX gap where wrapped expressions stayed visible as raw delimiter text in the editor.

## 2026-03-13 (Roadmap Renumber + E9 Reliability Kickoff)
- Roadmap sequencing update:
  - Prior planned `E9 Guided Graph` is now `E11`.
  - Prior planned `E10 Launch Hardening` is now `E12`.
  - New `E9` and `E10` focus on UX debt burn-down and hybrid workflows.
- Runtime compatibility hardening:
  - `note_assets` existence checks now use PostgreSQL `to_regclass('public.note_assets')` probing when on Postgres.
  - Note asset reconciliation now no-ops when backend hits an undefined-table error for `note_assets`, preventing note-save failures on partially migrated environments.

## 2026-03-13 (Epic E9 Workspace/Editor UX Delivery)
- Applied major visual refresh in workspace/editor surfaces via updated CSS variable system and panel/card hierarchy polish.
- Added optimistic UI + rollback semantics for note rename, pin/unpin, and delete actions in workspace state management.
- Added regression tests that enforce optimistic behavior followed by rollback on failed persistence (`pin` and `delete` paths).
- Validation/runtime notes:
  - local host web runtime still unstable due `esbuild` platform mismatch;
  - canonical validation used compose runtime (`docker compose -f infra/docker-compose.yml run --rm web npm run test`);
  - API regression suite revalidated in compose (`111 passed, 5 skipped`).

## 2026-03-13 (Epic E10 Quick-Switch Foundation)
- Added a workspace-global quick switcher (`Cmd/Ctrl+K`) with a single searchable result model for actions and notes.
- Added keyboard-first interaction contract (`Arrow` navigation, `Enter` execution, `Escape` close) with dialog/listbox semantics.
- Added quick actions for create/open/pin/archive and aligned context menu parity by adding archive/unarchive action.
- Validation/runtime notes:
  - web host runtime still depends on local platform-correct `node_modules`; compose remains the canonical verification path;
  - compose validation passed: targeted quick-switch tests (`22 passed`) and full web suite (`67 passed`).

## 2026-03-13 (Epic E10 Backlinks + Title Guardrail Delivery)
- Added backlinks API route and shared contracts:
  - `GET /v1/notes/{note_id}/backlinks`
  - `shared/contracts/python/v1/backlink.py`
  - `shared/contracts/ts/v1/backlink.ts`
- Implemented deterministic backlinks from explicit wiki-link references (`[[Title]]`) with ordering:
  - `updated_at` descending
  - `source_note_id` ascending
- Added title uniqueness write guardrail in note persistence:
  - duplicate title saves now return `409` with `note_title_conflict` payload.
- Added workspace linked-mentions modal:
  - loading/error/empty/data states
  - retry action
  - keyboard close (`Escape`)
  - focus restore to trigger
  - source-note jump behavior
- Validation/runtime notes:
  - compose API checks and full API tests passed (`116 passed, 5 skipped`);
  - compose web typecheck and full web tests passed (`71 passed`);
  - local host `uv run` panic and host `esbuild` mismatch remain known environment constraints; compose remains canonical verification path.
