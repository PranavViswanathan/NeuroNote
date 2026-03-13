# NeuroNote Implementation Plan

## Purpose
This document translates `docs/initial_scoping_doc.md` into executable action items with full context, organized as:

- Epic
- Story
- Task
- Subtask

Each story follows the working rule from `docs/codex.md`:

1. Build structure first.
2. Write test cases for viable scenarios.
3. Implement logic.
4. Run tests against written test cases.

## Scope Anchors from Scoping Research
- Editor architecture: TipTap + debounced autosave
- Unified data layer: PostgreSQL + Apache AGE + pgvector
- NLP fast path: spaCy + keyphrase extraction + relation extraction
- Entity resolution funnel: normalize -> abbreviations -> fuzzy -> embeddings -> alias table
- Global typed graph: cross-subject relationships with confidence
- Visualization: Sigma.js + graphology local/global views
- Background jobs: FastAPI BackgroundTasks first, Huey later
- Product differentiation: passive, explainable semantic connections

## Progress Snapshot (2026-03-13)
- Overall status: `Epic E0 complete`; `Epic E1 complete`; `Epic E2 complete`; `Epic E3 complete`; `Epic E4 complete`; `Epic E5 complete`; `Epic E6 complete`; `Epic E7 complete`; `Epic E8 complete`; `legacy Epics E6-E9 deprecated`; `commercial-track Epics E9-E10 planned`.
- Completed stories: `S0.1 Repository and service skeleton`, `S0.2 Quality bar and test harnesses`.
- Completed stories: `S1.1 TipTap editor baseline`, `S1.2 Debounced autosave and processing triggers`.
- Completed stories: `S2.1 Core relational schema for notes and blocks`, `S2.2 Graph and vector extension activation`.
- Completed stories: `S3.1 spaCy + keyphrase + relation extraction pipeline`, `S3.2 NLP latency budget and performance regression control`.
- Completed stories: `S4.1 Five-layer resolution funnel`, `S4.2 Alias table persistence and feedback loop`.
- Completed stories: `S5.1 Typed node and relationship model`, `S5.2 Idempotent delete-and-replace synchronization`.
- Completed stories: `S6.1 Note workspace shell and navigation`, `S6.2 Organization primitives`.
- Completed stories: `S7.1 Common block and formatting feature set`, `S7.2 Slash commands and wiki-links`.
- Completed stories: `S8.1 Math authoring and rendering`, `S8.2 Image upload and markdown export`.
- Validation evidence:
  - `make setup` completed with `uv` and created `api/.venv`.
  - `make check` passed (`ruff`, `mypy`).
  - `make test` passed and `tests/unit/test_structure.py` passed with E3 additions.
  - Added E1 API and contract tests now pass.
  - `npm --prefix web run typecheck` passed.
  - `npm --prefix web run test` passed (`17` tests) in compose runtime.
  - Added E2 DB structure (`app/db`), Alembic scaffold, and migrations with `subjects/notes/blocks/tags`.
  - Added DB-focused tests for schema integrity, repository behavior, extension checks, and graph/vector repository operations.
  - `make test-db` passes against extension-enabled local Postgres (`4` tests).
  - `make db-check-extensions` passes (`AGE and pgvector checks passed`).
  - Added E3 NLP package (`app/nlp`), note processing service, background job lifecycle transitions, note-version job coalescing, and processing API integration tests.
  - Added E3 perf fixtures (`200/800/2000` words) and latency guardrail tests under `tests/perf`.
  - Current Python validation set: `87 passed, 5 skipped` (`integration + unit`).
  - Added E4 resolver package (`app/nlp/resolution`) with normalization, abbreviation, fuzzy, embedding, and layered resolver orchestration.
  - Added E4 alias persistence (`entity_aliases`) model/repository, alias bootstrap import entrypoint, and API routes (`confirm`, `calibration`, `resolve-preview`).
  - Added E4 tests across unit/integration/schema/structure.
  - Added permanent migration/runtime hardening (2026-03-10): `DB_AUTO_CREATE` defaults to `false`, PostgreSQL startup auto-create is disabled, and migration `20260307_0002` is idempotent.
  - Added processing transaction-scope hardening (2026-03-10): fixed `A transaction is already begun on this Session.` by using one explicit transaction scope.
- Noted environment behavior: shell `VIRTUAL_ENV=.venv` differs from project `api/.venv`; `uv` ignores the shell env and uses project env correctly.
  - Local extension profile now builds via `infra/db/Dockerfile` and exposes both `age` and `vector`.
  - Current hardening validation after editor/process alignment: `48 passed, 4 skipped` (Python `integration + unit`) and `16 passed` (web tests).
  - Added containerized fallback workflow for unstable local `uv`: compose-managed `api` service uses `uv` inside container (`infra/api/Dockerfile` + entrypoint sync script) with compose-based run/check/test/migrate targets.
  - Documentation now standardized to compose-first operation (`compose-up/check/test/migrate/down`) with native local `uv` as optional fallback.
- Hardening pass completed (2026-03-07):
  - `NoteEditor` now uses TipTap as the single runtime editor path (textarea path removed).
  - `/v1/process-note` dedupe now keys on persisted `note.content_hash` (server-authoritative), not client payload hash.
  - Dead code cleanup completed for removed editor state helper and unused placeholder package.
- E5 implementation pass completed (2026-03-11):
  - Added typed graph sync service with source-note delete-and-replace behavior (`source_note_id` provenance).
  - Added startup async backfill workflow and `/v1/backfill-status` status endpoint.
  - Added explicit `note_title` support across DB/API/contracts/web and included title in persisted hash identity.
- E6 implementation pass completed (2026-03-12):
  - Added workspace shell in `web` with note list sidebar, create/rename/delete actions, recent notes, empty state, and keyboard list navigation.
  - Added note organization metadata (`subject_id`, `tags`, `is_pinned`, `is_archived`) across shared contracts, API persistence, and editor autosave payloads.
  - Added list query semantics for search/subject/tag/archive/pinned filters and default archive exclusion in `/v1/notes`.
  - Added migration `20260312_0004` for organization schema (`notes` flags + `note_tags` association table) with idempotent guards.
  - Validation results: Python `93 passed, 5 skipped`; web tests `22 passed` (Node 20 compose runtime); web typecheck passed.
- E7 implementation pass completed (2026-03-12):
  - Added data-driven command registry for common editing transforms (paragraph/headings/lists/checklist/quote/code/divider).
  - Added slash-command menu and `Cmd/Ctrl+K` command palette fallback with keyboard navigation support.
  - Added `[[wiki-link]]` autocomplete with existing-note suggestions and unresolved-link quick-create flow.
  - Validation results: web typecheck passed; compose web suite `45 passed`.
- E8 implementation pass completed (2026-03-13):
  - Added `note_assets` schema/migration, media storage boundary, upload/get/delete media APIs, and note-save reconciliation of unreferenced assets.
  - Added markdown export endpoint returning zip payload (`note.md` + `assets/*`) with deterministic image/math markdown representation.
  - Added editor support for math/image command surface and math/image plain-text fallback extraction.
  - Validation results: Python `106 passed, 5 skipped`; web typecheck passed; compose web suite `53 passed`.
- Roadmap rebaseline completed (2026-03-12):
  - Legacy unfinished `E6-E9` are deprecated for planning purposes.
  - New commercial-track roadmap is now defined as `E6 Workspace`, `E7 Editor Commands`, `E8 Math/Images/Export`, `E9 Guided Graph`, and `E10 Launch Hardening`.

## Architecture Decisions (Track In docs/plan.md)
- 2026-03-07: TipTap is the canonical editor runtime path.
  - Rationale: avoid dual editor behavior drift and keep one document lifecycle.
  - Impacted areas: `web/src/components/editor/NoteEditor.tsx`, `web/src/components/editor/TipTapEditor.tsx`.
- 2026-03-07: Processing job coalescing uses persisted note hash as source of truth.
  - Rationale: processing already executes on DB snapshot; dedupe key must match persisted snapshot identity.
  - Impacted areas: `api/src/app/routes/process.py`, `tests/integration/test_process_api.py`.
- 2026-03-07: Entity resolution uses deterministic-first layered matching before semantic fallback.
  - Rationale: prioritize low-cost/high-precision matching and only use expensive similarity when needed.
  - Impacted areas: `api/src/app/nlp/resolution/*`, `tests/unit/test_entity_resolver.py`.
- 2026-03-07: Alias conflict policy is confidence-first with `user_confirmed` tie-breaker.
  - Rationale: preserve stable canonical mappings while allowing higher-confidence corrections.
  - Impacted areas: `api/src/app/db/repositories/entity_alias_repository.py`, `tests/unit/test_entity_alias_repository.py`.
- 2026-03-10: Database schema ownership is migration-first in PostgreSQL environments.
  - Rationale: prevent runtime `create_all` from racing with Alembic and causing duplicate-table failures.
  - Impacted areas: `api/src/app/db/config.py`, `api/src/app/db/engine.py`, `api/alembic/versions/20260307_0002_entity_aliases.py`.
- 2026-03-10: Note processing uses a single explicit transaction for alias reads + graph writes.
  - Rationale: avoid nested/implicit transaction collisions in SQLAlchemy session lifecycle.
  - Impacted areas: `api/src/app/services/note_processing_service.py`, `tests/unit/test_note_processing_service.py`.
- 2026-03-11: Note identity and processing hash include `note_title` + body text.
  - Rationale: title-only edits must trigger new processing snapshots and avoid stale coalescing.
  - Impacted areas: `api/src/app/db/repositories/note_repository.py`, `web/src/components/editor/NoteEditor.tsx`, `shared/contracts/python/v1/note.py`.
- 2026-03-11: Graph synchronization uses typed edges with relation collapse to `RELATED_TO`.
  - Rationale: keep graph schema predictable while preserving original predicate as edge metadata.
  - Impacted areas: `api/src/app/services/graph_sync_service.py`, `api/src/app/db/repositories/graph_repository.py`, `tests/unit/test_graph_sync_service.py`.
- 2026-03-11: Startup graph backfill is async and non-blocking in PostgreSQL mode.
  - Rationale: keep API startup responsive while converging existing notes to the new graph model.
  - Impacted areas: `api/src/app/main.py`, `api/src/app/services/startup_backfill_service.py`, `api/src/app/routes/backfill.py`.
- 2026-03-12: Embedding table writes are schema-pinned to `public.note_embeddings`.
  - Rationale: AGE sets session `search_path` to `ag_catalog`; unqualified writes can drift schemas and break operational checks.
  - Impacted areas: `api/src/app/db/repositories/graph_repository.py`, `tests/integration/test_graph_vector_repository.py`.
- 2026-03-12: Editor canonical model remains TipTap JSON with markdown export-only capability.
  - Rationale: preserve rich editor fidelity while enabling portability; avoid dual-canonical content drift.
  - Impacted areas: `web/src/components/editor/*`, `shared/contracts/*`, future export endpoint.
- 2026-03-12: v1 authoring target is Notion-like basic blocks plus command surface, not full Notion parity.
  - Rationale: prioritize high-frequency writing workflows and ship speed over exhaustive block feature parity.
  - Impacted areas: `web/src/components/editor/*`, `web/src/lib/editor/*`.
- 2026-03-12: Editor command behavior is driven by a central command registry consumed by toolbar, slash menu, and command palette.
  - Rationale: keep command behavior consistent across interaction surfaces and simplify extension of future commands.
  - Impacted areas: `web/src/lib/editor/commands.ts`, `web/src/components/editor/TipTapEditor.tsx`, `web/src/components/editor/TipTapEditor.test.tsx`.
- 2026-03-12: Wiki links are represented as canonical inline `[[Title]]` text inside TipTap JSON and resolved via async note-title lookup.
  - Rationale: preserve editor storage simplicity while enabling Obsidian-style linking and unresolved-link quick-create.
  - Impacted areas: `web/src/lib/editor/wiki-links.ts`, `web/src/components/editor/TipTapEditor.tsx`, `web/src/components/editor/NoteEditor.tsx`.
- 2026-03-12: Math support is LaTeX inline/block, and image support is upload API + local disk with storage adapter boundary.
  - Rationale: robust v1 functionality now with a clear path to S3/object storage later.
  - Impacted areas: future `api/src/app/routes/*`, `api/src/app/db/*`, editor media/math modules.
- 2026-03-12: Graph UX target is local-first plus guided global graph behind explicit user action.
  - Rationale: keep graph usable and performant while avoiding early global hairball complexity.
  - Impacted areas: future graph API and `web` graph view modules.
- 2026-03-12: Legacy unfinished `E6-E9` are superseded by commercial-track `E6-E10`.
  - Rationale: align execution order with commercial usability priorities (workspace/editor/media first).
  - Impacted areas: `docs/plan.md` epic sequencing and milestones.
- 2026-03-12: Notes list defaults to non-archived records and supports explicit archive/search/subject/tag/pinned filters.
  - Rationale: preserve focused day-to-day workspace while keeping archived content queryable on demand.
  - Impacted areas: `api/src/app/routes/notes.py`, `api/src/app/db/repositories/note_repository.py`, `tests/integration/test_notes_api.py`.
- 2026-03-12: Workspace note actions are context-menu driven and pinned notes render in a dedicated section.
  - Rationale: reduce destructive-action clutter and prevent duplicate note rows while keeping pinned navigation explicit.
  - Impacted areas: `web/src/components/workspace/NotesWorkspace.tsx`, `web/src/components/workspace/NotesWorkspace.test.tsx`, `web/src/app/globals.css`.
- 2026-03-12: Workspace filters refresh via debounce and support explicit loading/retry feedback states.
  - Rationale: improve responsiveness and operational clarity without requiring blur-based user actions.
  - Impacted areas: `web/src/components/workspace/NotesWorkspace.tsx`, `web/src/components/workspace/NotesWorkspace.test.tsx`, `web/src/app/globals.css`.
- 2026-03-12: Note tags are normalized to trimmed lowercase and persisted via a dedicated `note_tags` association table.
  - Rationale: avoid duplicate semantic tags and keep filtering deterministic across UI and API.
  - Impacted areas: `api/src/app/db/models/note_tag.py`, `api/alembic/versions/20260312_0004_workspace_organization.py`, `api/src/app/db/repositories/note_repository.py`.
- 2026-03-13: Note asset lifecycle is persisted in `note_assets` and reconciled on each note save.
  - Rationale: prevent unreferenced media accumulation and keep note content/image state consistent.
  - Impacted areas: `api/src/app/routes/notes.py`, `api/src/app/db/repositories/note_asset_repository.py`, `api/src/app/services/note_asset_service.py`.
- 2026-03-13: Markdown export is a zip contract with deterministic `note.md` and relative `assets/*` links.
  - Rationale: preserve portability while keeping exported links self-contained.
  - Impacted areas: `api/src/app/routes/export.py`, `api/src/app/export/markdown.py`.
- 2026-03-13: Image upload transport uses JSON + base64 payload instead of multipart form.
  - Rationale: remove multipart runtime dependency and keep API path stable across constrained runtimes.
  - Impacted areas: `api/src/app/routes/media.py`, `shared/contracts/python/v1/media.py`, `shared/contracts/ts/v1/media.ts`, `web/src/lib/api-client.ts`.
- 2026-03-13: Media reconciliation is backward-compatible with pre-E8 schemas.
  - Rationale: prevent note-save failures when runtime DB has not yet applied `note_assets` migration.
  - Impacted areas: `api/src/app/services/note_asset_service.py`, `api/src/app/routes/media.py`, `api/src/app/routes/export.py`.

## Epic E0: Project Foundations and Delivery Guardrails [Completed 2026-03-01]
Context: The scoping doc assumes a multi-service system. Without shared conventions, implementation speed will collapse under integration drift. This epic creates the base structure, contract boundaries, and CI quality gates so all later epics are reliable.

### Story S0.1: Repository and service skeleton [Completed]
Context: Clear boundaries between web app, NLP API, and shared contracts prevent coupling and reduce rework.

#### Task T0.1.1: Create service and package structure
Subtask ST0.1.1.a: Create top-level directories for `web/`, `api/`, `shared/`, `infra/`, and `tests/`.
Subtask ST0.1.1.b: Add base package metadata for web and api services.
Subtask ST0.1.1.c: Add environment templates (`.env.example`) per service.

#### Task T0.1.2: Define initial contract structure
Subtask ST0.1.2.a: Create shared schema module for note processing requests and responses.
Subtask ST0.1.2.b: Define versioning strategy for contracts (`v1` namespace).
Subtask ST0.1.2.c: Document API boundaries in root README.

#### Task T0.1.3: Validate skeleton health
Subtask ST0.1.3.a: Run import/build sanity checks for each service.
Subtask ST0.1.3.b: Confirm all service entrypoints boot with placeholder handlers.
Subtask ST0.1.3.c: Add CI check that fails on missing service bootstrap files.

### Story S0.2: Quality bar and test harnesses [Completed]
Context: The scoping doc targets performance and quality-sensitive NLP behavior. Strong test scaffolding is mandatory before business logic.

#### Task T0.2.1: Create test suite structure
Subtask ST0.2.1.a: Create `tests/unit`, `tests/integration`, `tests/e2e`, and `tests/perf`.
Subtask ST0.2.1.b: Define naming conventions and fixtures layout.
Subtask ST0.2.1.c: Add smoke tests to ensure runner and fixtures execute.

#### Task T0.2.2: Add static quality checks
Subtask ST0.2.2.a: Configure formatting and lint checks for Python and TypeScript.
Subtask ST0.2.2.b: Configure import-order and type-check rules.
Subtask ST0.2.2.c: Add CI step to run all quality checks before tests.

#### Task T0.2.3: Add baseline test gate pipeline
Subtask ST0.2.3.a: Add local command aliases for full test runs.
Subtask ST0.2.3.b: Add CI matrix for web/api/shared test execution.
Subtask ST0.2.3.c: Set merge-blocking policy for failing tests.

## Epic E1: Editor and Frontend Architecture [Completed 2026-03-01]
Context: The editor is the capture point for all graph intelligence. TipTap is recommended for flexibility with custom knowledge graph interactions.

### Story S1.1: TipTap editor baseline
Context: Need a robust editor foundation that preserves rich document structure as ProseMirror JSON.

#### Task T1.1.1: Build editor feature structure
Subtask ST1.1.1.a: Create note editor route and page shell.
Subtask ST1.1.1.b: Create headless TipTap editor component wrapper.
Subtask ST1.1.1.c: Add state container for document JSON and plain-text projection.

#### Task T1.1.2: Write editor behavior tests
Subtask ST1.1.2.a: Test load existing note JSON into editor.
Subtask ST1.1.2.b: Test editing updates local state and dirty flags.
Subtask ST1.1.2.c: Test serialization and deserialization round-trip consistency.

#### Task T1.1.3: Implement editor logic
Subtask ST1.1.3.a: Wire TipTap state updates to note store.
Subtask ST1.1.3.b: Implement save payload shaping (`content_json`, `content_text`).
Subtask ST1.1.3.c: Add UI failure and retry states for save errors.

### Story S1.2: Debounced autosave and processing triggers
Context: Scoping recommends 500-1000ms autosave debounce and 3-5s NLP trigger debounce to avoid partial edit churn.

#### Task T1.2.1: Build autosave/trigger orchestration structure
Subtask ST1.2.1.a: Create debouncer module with configurable intervals.
Subtask ST1.2.1.b: Create note lifecycle event dispatcher.
Subtask ST1.2.1.c: Create API client wrappers for save and process endpoints.

#### Task T1.2.2: Write trigger and debounce tests
Subtask ST1.2.2.a: Test autosave only fires after no keystrokes in debounce window.
Subtask ST1.2.2.b: Test NLP trigger respects longer debounce or note blur.
Subtask ST1.2.2.c: Test rapid edits coalesce into one processing request per note version.

#### Task T1.2.3: Implement autosave and processing trigger logic
Subtask ST1.2.3.a: Wire editor events to autosave.
Subtask ST1.2.3.b: Wire processing trigger after stable note content.
Subtask ST1.2.3.c: Expose processing state in UI.

## Epic E2: Unified Database (PostgreSQL + Apache AGE + pgvector) [Completed 2026-03-01]
Context: The scoping doc identifies one-database architecture as the biggest complexity reducer. This epic establishes that foundation.

### Story S2.1: Core relational schema for notes and blocks
Context: Block-level processing depends on explicit `Note` and `Block` models with provenance and change detection fields.

#### Task T2.1.1: Build migration and schema structure
Subtask ST2.1.1.a: Create migration framework and versioned migration folders.
Subtask ST2.1.1.b: Define `subjects`, `notes`, `blocks`, and `tags` tables.
Subtask ST2.1.1.c: Add required fields: timestamps, `content_hash`, and text columns.

#### Task T2.1.2: Write schema integrity tests
Subtask ST2.1.2.a: Test FK constraints (`notes.subject_id`, `blocks.note_id`).
Subtask ST2.1.2.b: Test uniqueness and indexing assumptions.
Subtask ST2.1.2.c: Test update timestamp behavior on row modifications.

#### Task T2.1.3: Implement repositories for note and block data
Subtask ST2.1.3.a: Add CRUD operations for notes.
Subtask ST2.1.3.b: Add block extraction and update operations.
Subtask ST2.1.3.c: Add transaction wrapper for note+block writes.

### Story S2.2: Graph and vector extension activation
Context: AGE and pgvector are mandatory to keep graph traversal and semantic similarity in one DB.

#### Task T2.2.1: Build extension bootstrap structure
Subtask ST2.2.1.a: Add startup scripts enabling AGE and pgvector.
Subtask ST2.2.1.b: Add checks that fail startup if extensions are unavailable.
Subtask ST2.2.1.c: Add local Docker DB profile with required extensions.

#### Task T2.2.2: Write extension capability tests
Subtask ST2.2.2.a: Test basic Cypher query execution through AGE.
Subtask ST2.2.2.b: Test vector insert and cosine similarity query.
Subtask ST2.2.2.c: Test combined SQL and Cypher access patterns.

#### Task T2.2.3: Implement graph/vector repository operations
Subtask ST2.2.3.a: Add graph node and edge upsert methods.
Subtask ST2.2.3.b: Add embedding write and nearest-neighbor retrieval methods.
Subtask ST2.2.3.c: Add query wrappers used by visualization and recommendations.

## Epic E3: NLP Pipeline (Fast Path) [Completed 2026-03-07]
Context: Product value depends on near-real-time extraction. The scoping doc targets ~60-130ms for common notes.

### Story S3.1: spaCy + keyphrase + relation extraction pipeline [Completed]
Context: Need a deterministic baseline pipeline before adding advanced enrichment.

#### Task T3.1.1: Build NLP package structure
Subtask ST3.1.1.a: Create modules for entity extraction, keyphrases, relations, and embeddings.
Subtask ST3.1.1.b: Add centralized pipeline config with model names and thresholds.
Subtask ST3.1.1.c: Add fixture loader for representative note samples.

#### Task T3.1.2: Write NLP behavior tests
Subtask ST3.1.2.a: Test NER extraction on structured and fragmented notes.
Subtask ST3.1.2.b: Test keyphrase extraction outputs ranked phrases.
Subtask ST3.1.2.c: Test relation extraction emits SVO triples with confidence.

#### Task T3.1.3: Implement baseline extraction logic
Subtask ST3.1.3.a: Integrate spaCy `en_core_web_lg`.
Subtask ST3.1.3.b: Integrate PyTextRank stage.
Subtask ST3.1.3.c: Implement dependency-based SVO extraction.

### Story S3.2: NLP latency budget and performance regression control [Completed]
Context: Without measurable performance guardrails, the UX can degrade silently.

#### Task T3.2.1: Build performance test structure
Subtask ST3.2.1.a: Create benchmark fixtures for 200-word, 800-word, and 2000-word notes.
Subtask ST3.2.1.b: Define target latency thresholds for each fixture class.
Subtask ST3.2.1.c: Add perf result logging artifact in CI.

#### Task T3.2.2: Write latency and throughput tests
Subtask ST3.2.2.a: Test mean and p95 latency for each fixture class.
Subtask ST3.2.2.b: Test pipeline memory ceiling behavior.
Subtask ST3.2.2.c: Test failure behavior when model resources are missing.

#### Task T3.2.3: Implement performance tuning controls
Subtask ST3.2.3.a: Add selective pipeline disabling for low-resource environments.
Subtask ST3.2.3.b: Add reusable loaded-model singleton lifecycle.
Subtask ST3.2.3.c: Add metrics counters and timers around each stage.

## Epic E4: Entity Resolution and Canonicalization [Completed 2026-03-07]
Context: Graph usefulness depends on deduplicating aliases and near-duplicates into canonical entities.

### Story S4.1: Five-layer resolution funnel [Completed]
Context: The scoping doc recommends escalating from cheap deterministic checks to expensive semantic checks.

#### Task T4.1.1: Build resolver layer structure
Subtask ST4.1.1.a: Create normalization layer module.
Subtask ST4.1.1.b: Create abbreviation expansion layer module.
Subtask ST4.1.1.c: Create fuzzy and embedding candidate layers.

#### Task T4.1.2: Write resolution quality tests
Subtask ST4.1.2.a: Test normalization collapse (`Machine-Learning` -> `machine learning`).
Subtask ST4.1.2.b: Test abbreviation expansion (`ML` -> `machine learning`) when alias exists.
Subtask ST4.1.2.c: Test fuzzy threshold behavior near boundary values.
Subtask ST4.1.2.d: Test embedding threshold candidate generation behavior.

#### Task T4.1.3: Implement layered resolution logic
Subtask ST4.1.3.a: Chain layers with short-circuiting on high-confidence matches.
Subtask ST4.1.3.b: Emit confidence, matched layer, and canonical target metadata.
Subtask ST4.1.3.c: Expose unresolved entities for optional user confirmation flow.

### Story S4.2: Alias table persistence and feedback loop [Completed]
Context: Persistent alias memory turns one-time decisions into future instant matches.

#### Task T4.2.1: Build alias persistence structure
Subtask ST4.2.1.a: Create `entity_aliases` schema with provenance fields.
Subtask ST4.2.1.b: Add repository methods for alias read/write/upsert.
Subtask ST4.2.1.c: Add alias bootstrap import entrypoint.

#### Task T4.2.2: Write alias lifecycle tests
Subtask ST4.2.2.a: Test new alias insertion on confirmed matches.
Subtask ST4.2.2.b: Test alias lookup short-circuits resolver layers.
Subtask ST4.2.2.c: Test alias conflict resolution policy.

#### Task T4.2.3: Implement feedback-assisted alias updates
Subtask ST4.2.3.a: Add API endpoint for user confirmation on low-confidence matches.
Subtask ST4.2.3.b: Persist approved alias mappings.
Subtask ST4.2.3.c: Track confidence calibration stats.

## Epic E5: Global Knowledge Graph Schema and Sync [Completed 2026-03-11]
Context: NeuroNote differentiation depends on a typed, cross-subject, confidence-aware graph that stays in sync with note edits.

### Story S5.1: Typed node and relationship model [Completed]
Context: Need strict schema so extraction output remains queryable and explainable.

#### Task T5.1.1: Build graph model structure
Subtask ST5.1.1.a: Define node types (`Subject`, `Note`, `Block`, `Concept`, `Entity`, `Tag`).
Subtask ST5.1.1.b: Define edge types and mandatory properties.
Subtask ST5.1.1.c: Add source provenance fields on extracted edges.

#### Task T5.1.2: Write graph model tests
Subtask ST5.1.2.a: Test node upsert idempotency.
Subtask ST5.1.2.b: Test edge confidence range validation.
Subtask ST5.1.2.c: Test relationship direction correctness for each type.

#### Task T5.1.3: Implement graph mapping logic
Subtask ST5.1.3.a: Map NLP entities/keyphrases to `Concept`/`Entity`.
Subtask ST5.1.3.b: Map note blocks to `MENTIONS` edges with spans/confidence.
Subtask ST5.1.3.c: Compute `APPEARS_IN` edges from note-subject relationships.

### Story S5.2: Idempotent delete-and-replace synchronization [Completed]
Context: Full-note reprocessing with source tagging is simpler and safer than incremental diff sync.

#### Task T5.2.1: Build synchronization transaction structure
Subtask ST5.2.1.a: Create transactional sync entrypoint by `source_note_id`.
Subtask ST5.2.1.b: Add delete-by-source strategy for previous extracted artifacts.
Subtask ST5.2.1.c: Add insert path for fresh extraction results.

#### Task T5.2.2: Write sync reliability tests
Subtask ST5.2.2.a: Test reprocessing unchanged note produces stable graph state.
Subtask ST5.2.2.b: Test removed concepts disappear after reprocessing.
Subtask ST5.2.2.c: Test partial failure rolls back to consistent prior state.

#### Task T5.2.3: Implement sync logic and recovery behavior
Subtask ST5.2.3.a: Execute delete-and-replace in one transaction.
Subtask ST5.2.3.b: Emit sync audit log entries.
Subtask ST5.2.3.c: Add retry-safe idempotency keys.

## Epic E6: Workspace Organization and Multi-Note UX [Completed 2026-03-12]
Context: Commercial usability requires multi-note workflow quality before deeper graph/AI surface expansion.

### Story S6.1: Note workspace shell and navigation [Completed]
Context: Users need fast create/open/search workflows and stable note switching.

#### Task T6.1.1: Build workspace structure
Subtask ST6.1.1.a: Add persistent note list/sidebar shell.
Subtask ST6.1.1.b: Add create, rename, delete, and open-note actions.
Subtask ST6.1.1.c: Add recent-note and empty-state UX.

#### Task T6.1.2: Write workspace behavior tests
Subtask ST6.1.2.a: Test note CRUD from UI.
Subtask ST6.1.2.b: Test note selection persistence and list refresh.
Subtask ST6.1.2.c: Test keyboard-first navigation baseline.

#### Task T6.1.3: Implement workspace logic
Subtask ST6.1.3.a: Extend note list API client behavior.
Subtask ST6.1.3.b: Add optimistic updates and retry handling.
Subtask ST6.1.3.c: Preserve existing autosave/process interaction guarantees.

### Story S6.2: Organization primitives [Completed]
Context: Users need practical organization controls: notebook/subject, tags, pin, and archive.

#### Task T6.2.1: Build organization data structure
Subtask ST6.2.1.a: Add subject assignment support in API and UI.
Subtask ST6.2.1.b: Add tag assignment and filtering support.
Subtask ST6.2.1.c: Add pin/archive metadata and query support.

#### Task T6.2.2: Write organization tests
Subtask ST6.2.2.a: Test filter/sort/pagination behavior.
Subtask ST6.2.2.b: Test persistence of subject/tag/pin/archive fields.
Subtask ST6.2.2.c: Test list endpoint query semantics for search and filters.

#### Task T6.2.3: Implement API and persistence updates
Subtask ST6.2.3.a: Extend notes listing contract/query params.
Subtask ST6.2.3.b: Add required schema and repository updates.
Subtask ST6.2.3.c: Add integration coverage for organization flows.

## Epic E7: Notion-Like Core Editing and Command Surface [Completed 2026-03-12]
Context: TipTap baseline exists; v1 needs common block ergonomics and command-driven editing.

### Story S7.1: Common block and formatting feature set [Completed]
Context: Focus on high-frequency writing blocks, not full Notion parity.

#### Task T7.1.1: Build block feature structure
Subtask ST7.1.1.a: Add H1/H2/H3, list, checklist, quote, code block, divider, paragraph/body behavior.
Subtask ST7.1.1.b: Add toolbar hooks and shortcuts for common block transforms.
Subtask ST7.1.1.c: Keep TipTap JSON as canonical persisted format.

#### Task T7.1.2: Write block behavior tests
Subtask ST7.1.2.a: Test block transforms and serialization stability.
Subtask ST7.1.2.b: Test shortcut behavior and command consistency.
Subtask ST7.1.2.c: Test autosave/process compatibility across new blocks.

#### Task T7.1.3: Implement block logic
Subtask ST7.1.3.a: Wire editor extensions and command handlers.
Subtask ST7.1.3.b: Keep plain-text projection reliable for pipeline input.
Subtask ST7.1.3.c: Preserve existing error/retry UX behavior.

### Story S7.2: Slash commands and wiki-links [Completed]
Context: Users need fast insertion commands and Obsidian-style link ergonomics.

#### Task T7.2.1: Build command and wiki-link structure
Subtask ST7.2.1.a: Add slash command menu for core actions.
Subtask ST7.2.1.b: Add command palette fallback entrypoint.
Subtask ST7.2.1.c: Add `[[wiki-link]]` autocomplete and unresolved-link quick-create flow.

#### Task T7.2.2: Write command/wiki-link tests
Subtask ST7.2.2.a: Test slash command insert/transform behavior.
Subtask ST7.2.2.b: Test wiki-link completion and selection.
Subtask ST7.2.2.c: Test unresolved-link note creation behavior.

#### Task T7.2.3: Implement command/wiki-link logic
Subtask ST7.2.3.a: Add editor command registry wiring.
Subtask ST7.2.3.b: Add note title lookup path for link completion.
Subtask ST7.2.3.c: Keep link representation in canonical JSON model.

## Epic E8: Math, Images, and Export [Completed 2026-03-13]
Context: Commercial note quality requires robust equations/media plus portable export.

### Story S8.1: Math authoring and rendering
Context: v1 math model is LaTeX inline + block.

#### Task T8.1.1: Build math feature structure
Subtask ST8.1.1.a: Add inline and block math nodes.
Subtask ST8.1.1.b: Add deterministic math rendering path.
Subtask ST8.1.1.c: Add toolbar/command entrypoints for math insertion.

#### Task T8.1.2: Write math tests
Subtask ST8.1.2.a: Test save/load round-trip for math nodes.
Subtask ST8.1.2.b: Test invalid expression handling UX.
Subtask ST8.1.2.c: Test plain-text fallback behavior for NLP pipeline compatibility.

#### Task T8.1.3: Implement math logic
Subtask ST8.1.3.a: Wire editor math extensions and rendering.
Subtask ST8.1.3.b: Preserve autosave/process compatibility.
Subtask ST8.1.3.c: Add deterministic export representation for math blocks.

### Story S8.2: Image upload and markdown export
Context: v1 image strategy is upload API + local disk; export strategy is markdown + bundled assets.

#### Task T8.2.1: Build image/export structure
Subtask ST8.2.1.a: Add upload and retrieval API endpoints.
Subtask ST8.2.1.b: Add persisted image metadata and storage adapter boundary.
Subtask ST8.2.1.c: Add markdown export endpoint (`.md` + `assets/` relative links).

#### Task T8.2.2: Write image/export tests
Subtask ST8.2.2.a: Test file validation and path safety behavior.
Subtask ST8.2.2.b: Test editor image lifecycle (insert/render/delete).
Subtask ST8.2.2.c: Test export output structure and link correctness.

#### Task T8.2.3: Implement image/export logic
Subtask ST8.2.3.a: Add local disk storage implementation.
Subtask ST8.2.3.b: Add orphan cleanup behavior.
Subtask ST8.2.3.c: Add export packaging and integration tests.

## Epic E9: Guided Graph Experience (Local First + Global On Demand)
Context: Graph differentiation remains important, but with strict scope and performance boundaries.

### Story S9.1: Local graph in note context
Context: Local graph must be default, fast, and explainable.

#### Task T9.1.1: Build local graph structure
Subtask ST9.1.1.a: Add local graph panel route/shell.
Subtask ST9.1.1.b: Add local neighborhood API endpoint.
Subtask ST9.1.1.c: Add confidence/type/depth filters.

#### Task T9.1.2: Write local graph tests
Subtask ST9.1.2.a: Test empty/non-empty rendering.
Subtask ST9.1.2.b: Test node selection behavior.
Subtask ST9.1.2.c: Test deterministic filter updates.

#### Task T9.1.3: Implement local graph logic
Subtask ST9.1.3.a: Add frontend graph adapter wiring.
Subtask ST9.1.3.b: Add local payload limits.
Subtask ST9.1.3.c: Add loading/error UX states.

### Story S9.2: Guided global graph
Context: Global graph should be explicit-action only with strict query bounds.

#### Task T9.2.1: Build guided global graph structure
Subtask ST9.2.1.a: Add explicit global graph action.
Subtask ST9.2.1.b: Add server-side limits/guards.
Subtask ST9.2.1.c: Add snapshot/layout caching.

#### Task T9.2.2: Write guided global tests
Subtask ST9.2.2.a: Test global graph is not loaded by default.
Subtask ST9.2.2.b: Test filters and limits are enforced.
Subtask ST9.2.2.c: Test cache hit/miss and invalidation behavior.

#### Task T9.2.3: Implement guided global logic
Subtask ST9.2.3.a: Add global graph API query path.
Subtask ST9.2.3.b: Add cache invalidation on note reprocessing.
Subtask ST9.2.3.c: Add safe uncached fallback behavior.

## Epic E10: Commercial Boundaries and Launch Hardening (Single-User Runtime)
Context: Collaboration is deferred, but launch needs clean SaaS-ready boundaries and operational hardening.

### Story S10.1: SaaS-ready boundaries without collaboration features
Context: Keep current single-user behavior while preventing future refactor traps.

#### Task T10.1.1: Build boundary structure
Subtask ST10.1.1.a: Add actor/workspace context abstraction hooks.
Subtask ST10.1.1.b: Add entitlement/billing hook boundaries.
Subtask ST10.1.1.c: Keep default runtime behavior unchanged.

#### Task T10.1.2: Write boundary tests
Subtask ST10.1.2.a: Test backward compatibility when hooks are disabled.
Subtask ST10.1.2.b: Test context injection safety for existing endpoints.
Subtask ST10.1.2.c: Test no regressions in current single-user flows.

#### Task T10.1.3: Implement hardening and telemetry
Subtask ST10.1.3.a: Add launch-critical telemetry events.
Subtask ST10.1.3.b: Add reliability checks for core workflows.
Subtask ST10.1.3.c: Update operational documentation.

## Cross-Epic Test Case Matrix (Minimum Viable Scenarios)
Context: These are mandatory scenarios that validate the full architecture promised in the scoping doc.

1. Workspace and organization
- User can create/open/rename/delete notes from the workspace shell.
- Search/filter/sort/pagination are deterministic with notebook/tag/pin/archive metadata.

2. Note editing and autosave
- User edits rapidly for 30 seconds; only debounced saves are persisted.
- Last stable content is preserved after refresh and note-switch navigation.

3. Command surface and linking
- Slash commands insert/transform supported block types correctly.
- `[[wiki-link]]` completion resolves existing notes and can create unresolved targets.

4. Math and images
- Inline/block LaTeX persists and renders consistently.
- Image upload/insert/render/delete behavior is stable with validation and safe paths.

5. Export portability
- Markdown export emits `.md` plus `assets/` relative links for embedded images.
- Export includes deterministic math representation.

6. Processing trigger and status
- Note save triggers async processing and returns immediately.
- Job status transitions are visible and terminal state is reachable.

7. Graph synchronization and exploration
- Reprocessing the same note is idempotent and stale artifacts are removed.
- Local graph loads by default; guided global graph only loads on explicit user action.

8. Reliability and launch hardening
- Service restart does not corrupt note/graph state.
- Launch-critical telemetry and diagnostics are emitted for core capture/process/discover flows.

## Milestone Sequence
M1: Complete (`E0 complete`, `E1 complete`).
M2: E2 data layer and E3 baseline NLP complete.
M3: Complete (`E4 resolution complete`, `E5 graph sync complete`).
M4: Complete (`E6 workspace complete`, `E7 editor command surface complete`).
M5: E8 math/images/export complete.
M6: E9 guided graph experience complete.
M7: E10 commercial boundaries and launch hardening complete.

## Definition of Done for Any Story
1. Structure artifacts created first.
2. Test cases written and reviewed before logic implementation.
3. Logic implemented with minimal, clear, slop-free comments and docs.
4. Test suite executed and passing for the written scenarios.
5. Acceptance criteria and operational notes documented.


## Epic E6 (Legacy, Deprecated 2026-03-12): Graph Visualization (Sigma.js + Graphology)
Context: The graph must remain explorable at scale. The scoping doc emphasizes local graph first and global graph on demand.

### Story S6.1: Local graph visualization experience
Context: Local graph around current note is the default experience and must be fast and readable.

#### Task T6.1.1: Build graph UI structure
Subtask ST6.1.1.a: Create graph panel route and shell layout.
Subtask ST6.1.1.b: Create graph data adapter from API format to graphology format.
Subtask ST6.1.1.c: Add filter controls scaffold (hop depth, concept types, confidence).

#### Task T6.1.2: Write graph UI behavior tests
Subtask ST6.1.2.a: Test rendering with empty and non-empty graph payloads.
Subtask ST6.1.2.b: Test node click selects related note/block context.
Subtask ST6.1.2.c: Test filters update visible nodes/edges deterministically.

#### Task T6.1.3: Implement Sigma renderer and interactions
Subtask ST6.1.3.a: Integrate `@react-sigma/core`.
Subtask ST6.1.3.b: Implement event handlers for hover, click, and selection.
Subtask ST6.1.3.c: Map node size to degree and color to category.

### Story S6.2: Global graph and scale strategy
Context: Global graph can become a hairball. Need on-demand loading with server-side layout caching.

#### Task T6.2.1: Build global graph query and cache structure
Subtask ST6.2.1.a: Define threshold for switching from local to global strategy.
Subtask ST6.2.1.b: Create server endpoint for pre-computed global graph views.
Subtask ST6.2.1.c: Add position cache model for layout reuse.

#### Task T6.2.2: Write graph scale tests
Subtask ST6.2.2.a: Test local graph response time at typical note neighborhood sizes.
Subtask ST6.2.2.b: Test global graph rendering behavior for large payloads.
Subtask ST6.2.2.c: Test layout cache hit/miss behavior.

#### Task T6.2.3: Implement global graph delivery logic
Subtask ST6.2.3.a: Add backend layout precompute worker path.
Subtask ST6.2.3.b: Send pre-positioned nodes for render-only client mode.
Subtask ST6.2.3.c: Add fallback for uncached graph requests.

## Epic E7 (Legacy, Deprecated 2026-03-12): Background Processing and Queue Evolution
Context: The scoping doc recommends starting very simple with FastAPI BackgroundTasks, then evolving to Huey only when reliability needs increase.

### Story S7.1: Phase 1 async processing with FastAPI BackgroundTasks
Context: Immediate response with deferred processing keeps typing responsive while minimizing infrastructure.

#### Task T7.1.1: Build async job tracking structure
Subtask ST7.1.1.a: Create in-app job registry model.
Subtask ST7.1.1.b: Add status endpoint contract (`queued`, `running`, `completed`, `failed`).
Subtask ST7.1.1.c: Add note-level job coalescing key strategy.

#### Task T7.1.2: Write async processing tests
Subtask ST7.1.2.a: Test `202 Accepted` immediate response behavior.
Subtask ST7.1.2.b: Test single active pending job per note on rapid edits.
Subtask ST7.1.2.c: Test failure states and error surface in status endpoint.

#### Task T7.1.3: Implement BackgroundTasks processing flow
Subtask ST7.1.3.a: Wire note save trigger to async processing pipeline.
Subtask ST7.1.3.b: Update job registry through lifecycle states.
Subtask ST7.1.3.c: Expose polling path to frontend.

### Story S7.2: Phase 2 migration path to Huey
Context: Future reliability requirements need retries and durability without redesigning all call sites.

#### Task T7.2.1: Build queue abstraction boundary
Subtask ST7.2.1.a: Define queue interface used by process dispatcher.
Subtask ST7.2.1.b: Add adapter for BackgroundTasks implementation.
Subtask ST7.2.1.c: Add adapter stub for Huey implementation.

#### Task T7.2.2: Write queue parity tests
Subtask ST7.2.2.a: Test same contract behavior across both adapters.
Subtask ST7.2.2.b: Test retry policy semantics under transient failure.
Subtask ST7.2.2.c: Test idempotency with duplicated enqueue attempts.

#### Task T7.2.3: Implement Huey adapter and cutover controls
Subtask ST7.2.3.a: Implement Huey-backed task enqueue and consume logic.
Subtask ST7.2.3.b: Add feature flag for queue backend selection.
Subtask ST7.2.3.c: Add operational docs for queue cutover.

## Epic E8 (Legacy, Deprecated 2026-03-12): Product UX Differentiation and Trust
Context: Competitive analysis shows differentiation comes from passive semantic discovery with transparent confidence and explainability.

### Story S8.1: Backlinks and semantic suggestion surfaces
Context: Users need contextual "why this link exists" UI without interrupting writing flow.

#### Task T8.1.1: Build suggestion UI structure
Subtask ST8.1.1.a: Add sidebar sections for backlinks, suggested concepts, and related notes.
Subtask ST8.1.1.b: Add inline context snippet component.
Subtask ST8.1.1.c: Add confidence badge component and thresholds.

#### Task T8.1.2: Write suggestion UX tests
Subtask ST8.1.2.a: Test ranking by confidence and relevance.
Subtask ST8.1.2.b: Test one-click confirm promotes suggestion to persistent link.
Subtask ST8.1.2.c: Test suppression/dismiss behavior for low-value suggestions.

#### Task T8.1.3: Implement suggestion rendering and feedback logic
Subtask ST8.1.3.a: Connect suggestion API to sidebar UI.
Subtask ST8.1.3.b: Persist confirmation and dismissal feedback events.
Subtask ST8.1.3.c: Reflect feedback in subsequent ranking behavior.

### Story S8.2: Global and local graph UX defaults
Context: Scoping guidance recommends local graph default because global graph is noisy without filtering.

#### Task T8.2.1: Build default graph navigation structure
Subtask ST8.2.1.a: Set local graph as default route context.
Subtask ST8.2.1.b: Add explicit control to request global graph.
Subtask ST8.2.1.c: Add confidence and category filters in graph controls.

#### Task T8.2.2: Write graph UX acceptance tests
Subtask ST8.2.2.a: Test local graph loads first for every note context.
Subtask ST8.2.2.b: Test global graph only loads on explicit user action.
Subtask ST8.2.2.c: Test filters materially reduce visual clutter.

#### Task T8.2.3: Implement graph UX defaults
Subtask ST8.2.3.a: Apply routing/state defaults for local graph.
Subtask ST8.2.3.b: Implement global graph load action and progress state.
Subtask ST8.2.3.c: Persist user graph filter preferences.

## Epic E9 (Legacy, Deprecated 2026-03-12): Deployment, Operations, and Observability
Context: The architecture includes multiple runtime components. Operational visibility and repeatable deployment are needed early.

### Story S9.1: Local/dev deployment profile
Context: Developers need one-command startup for web, api, db, and optional redis.

#### Task T9.1.1: Build deployment structure
Subtask ST9.1.1.a: Create compose config for core services.
Subtask ST9.1.1.b: Add service healthcheck definitions.
Subtask ST9.1.1.c: Add startup dependency ordering.

#### Task T9.1.2: Write deployment tests
Subtask ST9.1.2.a: Test clean startup from empty environment.
Subtask ST9.1.2.b: Test restart behavior for api service without data loss.
Subtask ST9.1.2.c: Test service health endpoint checks.

#### Task T9.1.3: Implement deployment scripts and docs
Subtask ST9.1.3.a: Add helper commands for start/stop/reset.
Subtask ST9.1.3.b: Add troubleshooting guide for common startup issues.
Subtask ST9.1.3.c: Add environment variable reference docs.

### Story S9.2: Runtime metrics, logs, and alerts
Context: NLP correctness and latency regressions must be visible to keep user trust.

#### Task T9.2.1: Build observability structure
Subtask ST9.2.1.a: Define structured log schema for save/process/sync flows.
Subtask ST9.2.1.b: Define metrics names for queue depth, latency, errors.
Subtask ST9.2.1.c: Add correlation IDs across web -> api -> DB operations.

#### Task T9.2.2: Write observability validation tests
Subtask ST9.2.2.a: Test that critical flows emit required log fields.
Subtask ST9.2.2.b: Test metric counters and histograms are updated.
Subtask ST9.2.2.c: Test error traces include actionable context.

#### Task T9.2.3: Implement telemetry instrumentation
Subtask ST9.2.3.a: Add structured logging middleware.
Subtask ST9.2.3.b: Add stage-level timers for NLP pipeline.
Subtask ST9.2.3.c: Add alerts for repeated processing failures
