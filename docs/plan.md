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

## Progress Snapshot (2026-03-17)
- Overall status: `Epic E0 complete`; `Epic E1 complete`; `Epic E2 complete`; `Epic E3 complete`; `Epic E4 complete`; `Epic E5 complete`; `Epic E6 complete`; `Epic E7 complete`; `Epic E8 complete`; `Epic E9 complete`; `Epic E10 complete`; `Epic E11 in progress (S11.1 complete; S11.2 complete; S11.3 pending)`; `legacy Epics E6-E9 deprecated`; `commercial-track Epics E11-E12 active`.
- Completed stories: `S0.1 Repository and service skeleton`, `S0.2 Quality bar and test harnesses`.
- Completed stories: `S1.1 TipTap editor baseline`, `S1.2 Debounced autosave and processing triggers`.
- Completed stories: `S2.1 Core relational schema for notes and blocks`, `S2.2 Graph and vector extension activation`.
- Completed stories: `S3.1 spaCy + keyphrase + relation extraction pipeline`, `S3.2 NLP latency budget and performance regression control`.
- Completed stories: `S4.1 Five-layer resolution funnel`, `S4.2 Alias table persistence and feedback loop`.
- Completed stories: `S5.1 Typed node and relationship model`, `S5.2 Idempotent delete-and-replace synchronization`.
- Completed stories: `S6.1 Note workspace shell and navigation`, `S6.2 Organization primitives`.
- Completed stories: `S7.1 Common block and formatting feature set`, `S7.2 Slash commands and wiki-links`.
- Completed stories: `S8.1 Math authoring and rendering`, `S8.2 Image upload and markdown export`.
- Completed stories: `S10.1 Quick switcher and unified command surface`, `S10.2 Backlinks and linked mentions`, `S10.3 Selective block hierarchy and manual block references`.
- Completed stories: `S11.1 Local graph in note context`, `S11.2 Entity extraction and linking robustness for graph recall`.
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
- E9 kickoff reliability pass completed (2026-03-13):
  - Added PostgreSQL schema-qualified `note_assets` existence probe and undefined-table reconciliation fallback.
  - Added regression tests covering Postgres table probe behavior and runtime missing-table no-op path.
  - Validation results: compose API checks passed (`ruff`, `mypy`) and Python suite `111 passed, 5 skipped`.
- E9 UX redesign pass completed (2026-03-13):
  - Added major workspace/editor visual refresh with updated design tokens, panel hierarchy polish, and improved note row metadata clarity.
  - Added optimistic workspace interactions with rollback guarantees for rename/pin/delete failure paths.
  - Added regression coverage for optimistic pin and delete rollback behavior in workspace tests.
  - Validation results: `npm --prefix web run typecheck` passed; compose web tests `59 passed`; compose API suite `111 passed, 5 skipped`.
- E10 quick-switch foundation pass completed (2026-03-13):
  - Added workspace-global quick switcher (`Cmd/Ctrl+K`) with keyboard-first navigation (`Arrow`, `Enter`, `Escape`) and accessible dialog/listbox semantics.
  - Added searchable action + note result model for open/create/pin/archive flows with deterministic filtering.
  - Added workspace wiring for quick actions and archive toggle parity in context menu.
  - Validation results: compose web typecheck passed; targeted quick-switch tests passed (`22 passed`); full compose web suite `67 passed`.
- E10 backlinks and linked-mentions pass completed (2026-03-13):
  - Added backlink contracts and API endpoint (`GET /v1/notes/{note_id}/backlinks`) with deterministic wiki-link-based source ordering.
  - Added workspace linked-mentions modal with loading/error/empty/data states, retry affordance, keyboard close (`Escape`), and focus restore.
  - Added title-uniqueness write guardrail with `409 note_title_conflict` response for duplicate note-title saves.
  - Validation results: compose API suite `116 passed, 5 skipped`; compose web suite `71 passed`; compose checks (`ruff`, `mypy`, web typecheck) passed.
- Deterministic NLP/linking hardening pass completed (2026-03-14):
  - Added block-level entity mention extraction with deterministic dictionary-first spotting and span offsets.
  - Added deterministic resolver candidate ranking with configurable abstain threshold (`min_resolution_score`).
  - Graph sync now writes `Block -> Entity` `MENTIONS` edges from explicit mention evidence, replacing substring-only matching.
  - Validation results: focused API lint/type/tests passed (`ruff`, `mypy`, `27` tests across NLP/resolver/process/graph flows).
- Selective hierarchy + block reference pass completed (2026-03-14):
  - Replaced flattened block persistence with tree fields (`block_uid`, `parent_block_uid`, `sibling_order`) and migration `20260314_0006`.
  - Added block APIs: note block listing, block search, and block backlinks (`/v1/notes/{note_id}/blocks`, `/v1/blocks/search`, `/v1/blocks/{block_uid}/backlinks`).
  - Added editor selective nesting (`Tab`/`Shift+Tab` list-item indent/outdent only when valid) and inline block-reference insertion via `((...))` autocomplete.
  - Graph sync now writes deterministic `Block -> Block` `REFERS_TO` edges from explicit block-ref tokens.
  - Validation results: Python suite `132 passed, 5 skipped`; compose web suite `77 passed`; checks/typecheck passed.
- Notion-parity hierarchy/refinement pass completed (2026-03-14):
  - Updated editor nesting behavior to allow heading/paragraph and other core block indentation using `Tab`/`Shift+Tab` semantics aligned to Notion block nesting.
  - Added visual hierarchy hints and persisted block ancestry metadata (`parentBlockUid`, `indentLevel`) on editor blocks.
  - Upgraded note and block references to clickable hyperlink marks (`referenceLink`) while keeping deterministic backend reference extraction for graph/backlink flows.
  - Validation results: Python suite `135 passed, 5 skipped`; compose web suite `81 passed`; typecheck/check passed.
- E9 completion hardening pass completed (2026-03-14):
  - Added note-media reconciliation fallback for missing `note_assets` table errors during delete-mark phase to prevent note-save `500`s in partially migrated runtimes.
  - Added workspace recent-chip selection sync to keep selected/highlighted state deterministic.
  - Added regression coverage for missing-table reconciliation in unit/integration tests and recent-chip highlight behavior in workspace tests.
  - Validation results: Python suite `137 passed, 5 skipped`; compose web suite `84 passed`; typecheck/check passed.
- Block UID collision hardening pass completed (2026-03-14):
  - Added backend block-UID normalization that rewrites duplicate `blockUid` values within a note payload and remaps dependent `parentBlockUid` values.
  - Added deep-copy normalization path so corrected block IDs are persisted back into note JSON, not only block table rows.
  - Added regression coverage for duplicate `blockUid` payloads and parent remapping behavior.
  - Validation results: Python suite `138 passed, 5 skipped`; `ruff` passed.
- Media schema repair migration pass completed (2026-03-14):
  - Added Alembic revision `20260314_0007` to repair drifted environments where `alembic_version` advanced but `public.note_assets` was missing.
  - Migration creates `public.note_assets` and `ix_note_assets_note_id` idempotently and safely in forward direction.
  - Validation results: Python suite `140 passed, 5 skipped`; live compose DB verified (`alembic_version=20260314_0007`, `public.note_assets` present).
- Media transaction + SSR hardening pass completed (2026-03-14):
  - Made PostgreSQL `note_assets` existence probe transaction-neutral to avoid implicit session autobegin before media route transaction blocks.
  - Added TipTap `immediatelyRender: false` to eliminate SSR hydration mismatch warnings in Next.js runtime.
  - Validation results: Python suite `140 passed, 5 skipped`; web typecheck passed; targeted TipTap web tests passed in compose.
- E11 local graph pass completed (2026-03-15):
  - Added local graph API (`GET /v1/graph/local/{note_id}`) with deterministic filtering (`max_hops`, `limit_nodes`, `min_confidence`, `include_types`) and bounded payload semantics.
  - Added local graph service with note-neighborhood traversal (wiki-link outgoing + inbound backlinks), entity extraction, deterministic sort order, and truncation flagging.
  - Added interactive local graph panel in workspace with sigma+graphology canvas, keyboard-accessible filters, and note-node navigation.
  - Validation results: API `ruff` and `mypy` passed; Python suite `147 passed, 5 skipped`; web typecheck passed; web suite `87 passed`.
- E11 entity-recall hardening pass completed (2026-03-17):
  - Added explicit extractor strategy interface and layered extraction path (dictionary + optional spaCy + regex fallback) with deterministic span merge behavior.
  - Added optional EntityRuler bootstrapping from alias/dictionary/seed terms plus profile-gated extraction controls (`rule-only`, `hybrid-spacy`).
  - Added per-layer extraction hit counters (`dictionary_hits`, `spacy_hits`, `regex_hits`, `merged_mentions`) surfaced on the NLP pipeline for observability.
  - Added regression coverage for lowercase multi-block mentions, overlap dedup stability, profile/env parsing, and local-graph lowercase entity payloads.
  - Validation results: Python suite `152 passed, 5 skipped`; web suite `87 passed`; web typecheck passed; API `ruff` and `mypy` passed.
- E11 lowercase recall follow-up completed (2026-03-18):
  - Replaced non-overlapping lowercase regex matching with deterministic sliding n-gram extraction for rule-only mode.
  - Lowercase phrase filtering now rejects verb/noise windows while allowing generic multi-word entity phrases.
  - Validation results: Python suite `153 passed, 5 skipped`; targeted graph/NLP suites passed.
- E11 validation baseline refreshed (2026-03-29):
  - Revalidated compose-first runtime flow: `compose-up`, `compose-migrate`, `compose-bootstrap-extensions`, `compose-check`, `compose-test`, `compose-test-db`, and web test/typecheck/lint gates.
  - Fixed hybrid extraction merge regression where repeated lowercase token fallback emitted contained subspans (`graph`, `reasoning`) alongside higher-quality phrase spans (`graph reasoning`).
  - Tightened lowercase phrase filtering to reject `explore`/`explores` action windows that were suppressing valid repeated-token entity mentions such as `eren`.
  - Validation results: Python suite `156 passed, 5 skipped`; DB suite `5 passed`; web suite `87 passed`; live API smoke verified `/health`, note save, processing completion, and `GET /v1/graph/local/{note_id}`.
- Roadmap rebaseline completed (2026-03-12):
  - Legacy unfinished `E6-E9` are deprecated for planning purposes.
  - New commercial-track roadmap is now defined as `E6 Workspace`, `E7 Editor Commands`, `E8 Math/Images/Export`, `E9 UX Hardening`, `E10 Hybrid Workflows`, `E11 Guided Graph`, and `E12 Launch Hardening`.
  - 2026-03-13 renumbering: prior planned `E9` moved to `E11` and prior planned `E10` moved to `E12` to prioritize UX debt burn-down.

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
- 2026-03-12: Legacy unfinished `E6-E9` are superseded by commercial-track `E6-E12`.
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
- 2026-03-13: Commercial-track roadmap sequencing is renumbered to prioritize UX debt burn-down before graph expansion.
  - Rationale: stabilize core workspace/editor behavior before expanding feature surface area.
  - Impacted areas: `docs/plan.md` (`E9-E12` sequencing and milestones).
- 2026-03-13: `note_assets` schema checks are PostgreSQL schema-qualified and reconciliation tolerates undefined-table errors.
  - Rationale: avoid false-positive schema checks and prevent note-save failures in partially migrated runtime environments.
  - Impacted areas: `api/src/app/services/note_asset_service.py`, `tests/unit/test_note_asset_service.py`.
- 2026-03-14: Media reconciliation tolerates missing `note_assets` errors in delete-mark path as well as read path.
  - Rationale: note saves must remain available when runtime schema is partially migrated or drifting.
  - Impacted areas: `api/src/app/services/note_asset_service.py`, `tests/unit/test_note_asset_service.py`, `tests/integration/test_notes_api.py`.
- 2026-03-13: Workspace quick-switch uses a unified result model (actions + notes) with keyboard-first execution semantics.
  - Rationale: keep discovery and command execution deterministic from one interaction surface (`Cmd/Ctrl+K`) and reduce command drift.
  - Impacted areas: `web/src/lib/workspace/quick-switch.ts`, `web/src/components/workspace/NotesWorkspace.tsx`, `web/src/components/workspace/NotesWorkspace.test.tsx`.
- 2026-03-13: Note titles are write-path unique with explicit `409` conflict semantics.
  - Rationale: keep wiki-link title targeting unambiguous for backlinks without destructive migration-side rewrites.
  - Impacted areas: `api/src/app/db/repositories/note_repository.py`, `api/src/app/routes/notes.py`, `tests/integration/test_notes_api.py`.
- 2026-03-13: Backlinks are derived from explicit `[[Title]]` references and surfaced as a workspace modal flow.
  - Rationale: provide deterministic, explainable linked-mention behavior while keeping v1 implementation lightweight.
  - Impacted areas: `api/src/app/routes/backlinks.py`, `shared/contracts/*/v1/backlink.*`, `web/src/components/workspace/BacklinksModal.tsx`.
- 2026-03-14: Entity linking evidence is block-first and mention-span driven.
  - Rationale: remove false-positive substring matches and make link provenance explainable and deterministic.
  - Impacted areas: `api/src/app/nlp/spotting.py`, `api/src/app/nlp/resolution/ranking.py`, `api/src/app/services/graph_sync_service.py`, `api/src/app/services/note_processing_service.py`.
- 2026-03-14: Block storage uses adjacency-list tree semantics and manual references use canonical `((block_uid))` tokens.
  - Rationale: preserve stable block identity under reordering/nesting and provide deterministic, explicit block-to-block linking.
  - Impacted areas: `api/src/app/db/models/block.py`, `api/src/app/db/repositories/block_repository.py`, `api/src/app/routes/blocks.py`, `api/src/app/services/graph_sync_service.py`, `web/src/components/editor/TipTapEditor.tsx`.
- 2026-03-14: Editor nesting behavior follows Notion-style block indentation semantics (`Tab` nest under previous block, `Shift+Tab` outdent).
  - Rationale: users expect uniform outliner-like hierarchy across headings, paragraphs, and common block types, not list-only indentation.
  - Impacted areas: `web/src/lib/editor/block-hierarchy.ts`, `web/src/lib/editor/extensions/block-hierarchy.ts`, `web/src/components/editor/TipTapEditor.tsx`.
- 2026-03-14: Block persistence normalizes duplicate `blockUid` values server-side.
  - Rationale: editor payload drift or copy/paste collisions must never cause `uq_blocks_note_id_block_uid` write failures.
  - Impacted areas: `api/src/app/db/repositories/block_repository.py`, `tests/unit/test_block_repository.py`.
- 2026-03-14: Media schema repair is migration-owned via forward idempotent revision.
  - Rationale: environments stamped at newer heads must still converge to required media schema (`public.note_assets`) without manual SQL.
  - Impacted areas: `api/alembic/versions/20260314_0007_note_assets_repair.py`, `tests/unit/test_note_assets_repair_migration.py`.
- 2026-03-14: PostgreSQL media schema probes must not start ORM transactions.
  - Rationale: preflight checks that autobegin sessions can cause nested transaction failures in write routes.
  - Impacted areas: `api/src/app/services/note_asset_service.py`, `tests/unit/test_note_asset_service.py`, `api/src/app/routes/media.py`.
- 2026-03-15: Local graph retrieval is deterministic and bounded by explicit filter controls.
  - Rationale: graph UX must stay explainable and performant under multi-note growth while remaining keyboard-operable.
  - Impacted areas: `api/src/app/routes/graph.py`, `api/src/app/services/local_graph_service.py`, `web/src/components/graph/LocalGraphPanel.tsx`, `web/src/components/workspace/NotesWorkspace.tsx`.
- 2026-03-17: Entity extraction for graph-facing workflows uses a deterministic-plus-statistical hybrid pipeline.
  - Rationale: dictionary-only and case-sensitive fallback spotting causes low recall on lowercase informal notes, which suppresses graph nodes/edges despite valid note content.
  - Impacted areas: `api/src/app/nlp/extractors.py`, `api/src/app/nlp/pipeline.py`, `api/src/app/nlp/spotting.py`, `api/src/app/nlp/config.py`, `api/src/app/services/local_graph_service.py`, `tests/unit/test_entity_spotting.py`, `tests/unit/test_nlp_pipeline.py`, `tests/unit/test_nlp_config.py`, `tests/unit/test_local_graph_service.py`.

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

## Epic E9: UX Debt Burn-Down and Interaction Reliability [Completed 2026-03-14]
Context: Current UX regressions and interaction inconsistency are the largest blocker to commercial trust. This epic prioritizes stability and clarity before adding more surface area.

### Story S9.1: Workspace information architecture consistency [Completed]
Context: Notes list behavior must be deterministic and free of duplicate/pinned drift.

#### Task T9.1.1: Build workspace reliability structure
Subtask ST9.1.1.a: Consolidate note list rendering to one source of truth for pinned/recent/all sections.
Subtask ST9.1.1.b: Define deterministic sorting and section fallback rules.
Subtask ST9.1.1.c: Add explicit loading/empty/error UI states for list and note panel.

#### Task T9.1.2: Write workspace UX regression tests
Subtask ST9.1.2.a: Test no duplicate note rows across pinned and unpinned sections.
Subtask ST9.1.2.b: Test rename/pin/archive/delete reflect immediately without refresh.
Subtask ST9.1.2.c: Test keyboard parity for context-menu actions and list navigation.

#### Task T9.1.3: Implement workspace UX hardening
Subtask ST9.1.3.a: Add optimistic UI updates with rollback on failures.
Subtask ST9.1.3.b: Add retry affordances for failed list/save operations.
Subtask ST9.1.3.c: Add deterministic selection and highlight behavior after list refresh.

### Story S9.2: Editor ergonomics and command reliability [Completed]
Context: Editor readability and command reliability must be predictable in all core writing flows.

#### Task T9.2.1: Build editor UX structure
Subtask ST9.2.1.a: Standardize typography/spacing tokens for content readability.
Subtask ST9.2.1.b: Harden slash-command surface with deterministic insertion behavior.
Subtask ST9.2.1.c: Add non-blocking inline error and status states for editor actions.

#### Task T9.2.2: Write editor UX regression tests
Subtask ST9.2.2.a: Test slash command selection inserts block type instead of fallback newline.
Subtask ST9.2.2.b: Test content visibility and multiline editing behavior on load/switch.
Subtask ST9.2.2.c: Test keyboard-only command navigation (`Arrow`, `Enter`, `Escape`).

#### Task T9.2.3: Implement editor UX hardening
Subtask ST9.2.3.a: Apply visual-system tokens and remove ad-hoc editor spacing.
Subtask ST9.2.3.b: Add robust command execution guardrails and user feedback.
Subtask ST9.2.3.c: Ensure status indicators never get stuck in invalid states.

## Epic E10: Hybrid Knowledge Workflows [Completed 2026-03-13]
Context: After UX debt burn-down, expand Notion-like productivity and Obsidian-like discovery in a single cohesive workflow.

### Story S10.1: Quick switcher and unified command surface [Completed]
Context: Fast note discovery and action execution should be available from anywhere.

#### Task T10.1.1: Build quick-switch structure
Subtask ST10.1.1.a: Add global quick-switcher trigger (`Cmd/Ctrl+K`) at workspace level.
Subtask ST10.1.1.b: Add searchable actions for open/create/filter/pin/archive.
Subtask ST10.1.1.c: Add keyboard-first navigation and selection behavior.

#### Task T10.1.2: Write quick-switch tests
Subtask ST10.1.2.a: Test note search/open/create flows from quick-switcher.
Subtask ST10.1.2.b: Test action execution parity for keyboard and mouse.
Subtask ST10.1.2.c: Test deterministic fallback behavior when no results are found.

#### Task T10.1.3: Implement unified command logic
Subtask ST10.1.3.a: Reuse shared command registry across editor and workspace.
Subtask ST10.1.3.b: Add contextual action grouping and ranking.
Subtask ST10.1.3.c: Add telemetry hooks for command adoption and failures.

### Story S10.2: Backlinks and linked mentions [Completed]
Context: Linking intelligence should make relationships explainable and actionable.

#### Task T10.2.1: Build backlink structure
Subtask ST10.2.1.a: Add note-scoped backlink query contract and API route.
Subtask ST10.2.1.b: Add linked-mentions panel in note context.
Subtask ST10.2.1.c: Add unresolved-link suggestion state and quick-create action.

#### Task T10.2.2: Write backlink tests
Subtask ST10.2.2.a: Test backlink accuracy and deterministic ordering.
Subtask ST10.2.2.b: Test jump-to-source behavior for each backlink item.
Subtask ST10.2.2.c: Test degraded behavior when backlink query fails.

#### Task T10.2.3: Implement backlink logic
Subtask ST10.2.3.a: Add backend backlink materialization query path.
Subtask ST10.2.3.b: Add UI rendering with loading/error/empty states.
Subtask ST10.2.3.c: Add inline explanation labels for why links exist.

### Story S10.3: Selective block hierarchy and manual block references [Completed 2026-03-14]
Context: Commercial note UX needs intuitive hierarchy behavior and explicit block-level linking that is deterministic and inspectable.

#### Task T10.3.1: Build tree block + block-ref structure [Completed]
Subtask ST10.3.1.a: Extend `blocks` schema with `block_uid`, `parent_block_uid`, `sibling_order` and preserve compatibility via migration.
Subtask ST10.3.1.b: Add block contracts and API surfaces for list/search/backlinks.
Subtask ST10.3.1.c: Add editor block-ref parser/token utilities and key-action model for indent/outdent behavior.

#### Task T10.3.2: Write hierarchy/reference tests [Completed]
Subtask ST10.3.2.a: Add repository tests for tree persistence, scoped block search, and block backlinks.
Subtask ST10.3.2.b: Add service tests for `REFERS_TO` edge emission from explicit `((block_uid))` references.
Subtask ST10.3.2.c: Add integration/frontend tests for block APIs and block-ref/key-handler utilities.

#### Task T10.3.3: Implement hierarchy/reference logic [Completed]
Subtask ST10.3.3.a: Implement recursive block extraction and adjacency-list persistence.
Subtask ST10.3.3.b: Implement selective nesting UX (`Tab` indent / `Shift+Tab` outdent only for valid list contexts).
Subtask ST10.3.3.c: Implement inline block-reference autocomplete/insertion and graph `REFERS_TO` synchronization.

## Epic E11: Guided Graph Experience (Local First + Global On Demand) [In Progress]
Context: Graph differentiation remains important, but with strict scope and performance boundaries.

### Story S11.1: Local graph in note context [Completed 2026-03-15]
Context: Local graph must be default, fast, and explainable.

#### Task T11.1.1: Build local graph structure [Completed]
Subtask ST11.1.1.a: Add local graph panel route/shell.
Subtask ST11.1.1.b: Add local neighborhood API endpoint.
Subtask ST11.1.1.c: Add confidence/type/depth filters.

#### Task T11.1.2: Write local graph tests [Completed]
Subtask ST11.1.2.a: Test empty/non-empty rendering.
Subtask ST11.1.2.b: Test node selection behavior.
Subtask ST11.1.2.c: Test deterministic filter updates.

#### Task T11.1.3: Implement local graph logic [Completed]
Subtask ST11.1.3.a: Add frontend graph adapter wiring.
Subtask ST11.1.3.b: Add local payload limits.
Subtask ST11.1.3.c: Add loading/error UX states.

### Story S11.2: Entity extraction and linking robustness for graph recall [Completed 2026-03-17]
Context: Graph quality is bounded by mention recall. Lowercase informal notes must still produce deterministic entity/link output.

#### Task T11.2.1: Build hybrid extraction structure [Completed]
Subtask ST11.2.1.a: Add explicit extractor strategy interface (dictionary, spaCy NER, regex fallback).
Subtask ST11.2.1.b: Add `EntityRuler` bootstrapping from alias table and seeded domain terms.
Subtask ST11.2.1.c: Add config gating for model/profile (`rule-only`, `hybrid-spacy`, fallback behavior).

#### Task T11.2.2: Write robustness tests first [Completed]
Subtask ST11.2.2.a: Test lowercase proper nouns in multi-block notes produce deterministic mentions.
Subtask ST11.2.2.b: Test alias+model overlap dedup keeps stable IDs and spans.
Subtask ST11.2.2.c: Test NIL/abstain behavior preserves precision for unresolved mentions.
Subtask ST11.2.2.d: Test local-graph payload contains entity and mention edges for previously failing lowercase note fixtures.

#### Task T11.2.3: Implement hybrid extraction logic [Completed]
Subtask ST11.2.3.a: Integrate spaCy NER stage into extraction with deterministic merge ordering.
Subtask ST11.2.3.b: Keep resolver ranking stack unchanged; feed higher-recall mention candidates.
Subtask ST11.2.3.c: Add observability counters for per-layer hit rates (dictionary vs spacy vs fallback).
Subtask ST11.2.3.d: Update runbooks for alias seeding and model download/runtime requirements.

### Story S11.3: Guided global graph
Context: Global graph should be explicit-action only with strict query bounds.

#### Task T11.3.1: Build guided global graph structure
Subtask ST11.3.1.a: Add explicit global graph action.
Subtask ST11.3.1.b: Add server-side limits/guards.
Subtask ST11.3.1.c: Add snapshot/layout caching.

#### Task T11.3.2: Write guided global tests
Subtask ST11.3.2.a: Test global graph is not loaded by default.
Subtask ST11.3.2.b: Test filters and limits are enforced.
Subtask ST11.3.2.c: Test cache hit/miss and invalidation behavior.

#### Task T11.3.3: Implement guided global logic
Subtask ST11.3.3.a: Add global graph API query path.
Subtask ST11.3.3.b: Add cache invalidation on note reprocessing.
Subtask ST11.3.3.c: Add safe uncached fallback behavior.

## Epic E12: Commercial Boundaries and Launch Hardening (Single-User Runtime)
Context: Collaboration is deferred, but launch needs clean SaaS-ready boundaries and operational hardening.

### Story S12.1: SaaS-ready boundaries without collaboration features
Context: Keep current single-user behavior while preventing future refactor traps.

#### Task T12.1.1: Build boundary structure
Subtask ST12.1.1.a: Add actor/workspace context abstraction hooks.
Subtask ST12.1.1.b: Add entitlement/billing hook boundaries.
Subtask ST12.1.1.c: Keep default runtime behavior unchanged.

#### Task T12.1.2: Write boundary tests
Subtask ST12.1.2.a: Test backward compatibility when hooks are disabled.
Subtask ST12.1.2.b: Test context injection safety for existing endpoints.
Subtask ST12.1.2.c: Test no regressions in current single-user flows.

#### Task T12.1.3: Implement hardening and telemetry
Subtask ST12.1.3.a: Add launch-critical telemetry events.
Subtask ST12.1.3.b: Add reliability checks for core workflows.
Subtask ST12.1.3.c: Update operational documentation.

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

4. Workspace quick-switch and backlink workflows
- `Cmd/Ctrl+K` quick-switch can open/create/filter notes without mouse-only actions.
- Linked-mentions modal lists backlinks with deterministic ordering and jump behavior.

5. Math and images
- Inline/block LaTeX persists and renders consistently.
- Image upload/insert/render/delete behavior is stable with validation and safe paths.

6. Export portability
- Markdown export emits `.md` plus `assets/` relative links for embedded images.
- Export includes deterministic math representation.

7. Processing trigger and status
- Note save triggers async processing and returns immediately.
- Job status transitions are visible and terminal state is reachable.

8. Graph synchronization and exploration
- Reprocessing the same note is idempotent and stale artifacts are removed.
- Local graph loads by default; guided global graph only loads on explicit user action.

9. Reliability and launch hardening
- Service restart does not corrupt note/graph state.
- Launch-critical telemetry and diagnostics are emitted for core capture/process/discover flows.

## Milestone Sequence
M1: Complete (`E0 complete`, `E1 complete`).
M2: E2 data layer and E3 baseline NLP complete.
M3: Complete (`E4 resolution complete`, `E5 graph sync complete`).
M4: Complete (`E6 workspace complete`, `E7 editor command surface complete`).
M5: E8 math/images/export complete.
M6: E9 UX debt burn-down and interaction reliability complete.
M7: E10 hybrid knowledge workflows complete.
M8: E11 guided graph experience complete.
M9: E12 commercial boundaries and launch hardening complete.

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
