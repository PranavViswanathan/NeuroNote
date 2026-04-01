# Decisions Log (Non-Plan Additions)

This file captures implementation notes and additions that are useful context but do not change the executable project plan.

Architectural decisions are tracked in `docs/plan.md` under `Architecture Decisions`.

## 2026-03-29 (Validated Baseline Refresh)
- Re-ran the compose-first release gates against the current E11 graph/NLP baseline:
  - `compose-up`
  - `compose-migrate`
  - `compose-bootstrap-extensions`
  - `compose-check`
  - `compose-test`
  - `compose-test-db`
  - web `lint`, `typecheck`, and `test`
- Validation outcomes:
  - Python suites: `156 passed, 5 skipped`
  - DB extension/vector suite: `5 passed`
  - Web suite: `87 passed`
  - Live API smoke succeeded for `/health`, note save, processing completion, and local graph payload generation.
- Fixed one real regression discovered during the baseline pass:
  - Hybrid spotting merge logic was allowing lower-quality contained spans from repeated lowercase token fallback to survive alongside better phrase spans.
  - Example bad behavior: `graph reasoning` could yield extra mention spans for `graph` and `reasoning`.
  - Fix: accept longer spans first and discard contained spans after a better span is accepted.
- Fixed one follow-on lowercase recall issue:
  - `eren explores ...` was incorrectly treated as a lowercase entity phrase, which suppressed the intended repeated single-token entity recall for `eren`.
  - Fix: expanded lowercase action-token filtering to reject `explore` / `explores` phrase windows.
- Environment note:
  - Host-side `curl http://127.0.0.1:8000/...` from the Codex sandbox was unreliable during this validation pass even while compose services were healthy.
  - The live smoke gate was therefore verified from inside the running `api` container via loopback (`127.0.0.1:8000`), which exercised the same long-running FastAPI process successfully.

## 2026-03-29 (Local Graph Noise Hardening)
- Debug outcome:
  - The local graph API was functionally healthy but still noisy because it performed entity extraction over synthetic title+body text.
  - That let note titles and explicit `[[linked note]]` targets appear as entity nodes even though the graph already modeled them as note nodes connected by `LINKS_TO`.
- Implementation:
  - `LocalGraphService` now extracts entities from persisted block/body content, not note-title-prefixed synthetic text.
  - The local graph path now filters entity labels that normalize to:
    - the current note title,
    - explicit wiki-link target titles already represented as note links.
  - Local graph extraction now also seeds dictionary terms from the alias table for better parity with processing-time extraction.
- Regression coverage:
  - Added unit and integration tests proving note titles and wiki-link target titles are excluded from entity nodes while real body entities remain.
- Validation:
  - Targeted graph/NLP suites passed (`20 passed`).
  - Live smoke graph for a note linking `[[Graph Clean Neighbor]]` now returns only expected entity labels: `Machine Learning`, `graph reasoning`.

## 2026-03-17 (Release Gate Standardization)
- Added `docs/release_checklist.md` as the canonical epic completion checklist.
- Gate policy is now explicit and strict:
  - compose-first commands,
  - sequential gates (no skipping/reordering after failure),
  - mandatory UI/manual verification for every epic,
  - blocked release on any failed gate.
- Added documentation pointers so the checklist is part of normal workflow:
  - `README.md` (`Project Docs` and workflow note),
  - `docs/codex.md` (epic completion rule).

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

## 2026-03-14 (Deterministic NLP + Linking Hardening)
- Added deterministic block-level entity spotting module (`app/nlp/spotting.py`) with:
  - dictionary-first mention capture,
  - span offsets,
  - stable mention/entity ordering.
- Added resolver candidate ranking module (`app/nlp/resolution/ranking.py`) and integrated thresholded abstain behavior (`min_resolution_score`) in `EntityResolver`.
- Updated note processing and graph sync flow so `Block -> Entity` `MENTIONS` edges are driven by explicit extracted mention evidence, not substring scans.
- Added dedicated regression suites:
  - `tests/unit/test_entity_spotting.py`
  - `tests/unit/test_resolution_ranking.py`
  - updated NLP/resolver/process/graph unit coverage for mention-aware behavior.
- Validation/runtime notes:
  - local `uv run` panic still present in this environment;
  - verification run executed via `api/.venv/bin/{ruff,mypy,pytest}` with focused suites passing.

## 2026-03-14 (Selective Hierarchy + Block References)
- Added block-tree persistence and migration:
  - `blocks` now carries `block_uid`, `parent_block_uid`, `sibling_order`.
  - migration `20260314_0006_block_tree` backfills missing identifiers and sibling order.
- Added block APIs for editor/linking flows:
  - `GET /v1/notes/{note_id}/blocks`
  - `GET /v1/blocks/search`
  - `GET /v1/blocks/{block_uid}/backlinks`
- Added editor-level block reference UX:
  - typing `((` opens block-reference lookup,
  - selecting an option inserts canonical `((block_uid))` token.
- Added selective nesting default behavior:
  - `Tab` indents only when list nesting is valid,
  - `Shift+Tab` outdents only when valid,
  - behavior does not override active slash/wiki/block-ref menus.
- Added graph sync reference edges:
  - `GraphSyncService` emits deterministic `REFERS_TO` edges for explicit block references.

## 2026-03-14 (Notion-Parity Nesting + Hyperlink References)
- Verified Notion keyboard semantics from official Notion help docs:
  - `Tab` nests current content under the block above,
  - `Shift+Tab` un-nests by one level.
- Updated editor hierarchy behavior to match this interaction model for core block types (not list-only).
- Introduced `referenceLink` mark for clickable note and block references in-editor:
  - note refs render as clickable `[[Title]]`,
  - block refs render as readable labels linked to target note/block anchor.
- Backend block-reference extraction now supports both:
  - legacy token form `((block_uid))`,
  - mark-based references (`referenceLink` with `dataBlockUid` / `href` block anchors).

## 2026-03-14 (Hierarchy UX Polish)
- Added hierarchy hint refinement in editor:
  - hint now includes explicit action text and parent preview where applicable.
- Added stronger hierarchy visuals:
  - indentation rails for nested blocks (`data-indent-level`),
  - consistent nested spacing.
- Added stronger reference affordance:
  - clickable reference links now have hover/focus treatment for clearer interactivity.
- Added regression coverage for hierarchy hint formatting and parent preview text utility paths.

## 2026-03-14 (E9 Completion Hardening)
- Added resilient note-save fallback when media reconciliation hits missing `note_assets` errors during delete-mark operations.
- Added unit and integration regressions to lock missing-table behavior for both reconciliation read and write paths.
- Synced workspace recent-chip interaction so selected and highlighted note state update together.
- Validation:
  - Python `ruff` and `mypy` passed via `api/.venv/bin/*`.
  - Python tests passed: `137 passed, 5 skipped`.
  - Web tests passed in compose runtime: `84 passed`.

## 2026-03-14 (Block UID Collision Hardening)
- Added server-side duplicate `blockUid` normalization during block extraction.
- Added `parentBlockUid` remapping to canonicalized UIDs when duplicate IDs are encountered.
- Added deep-copy normalization before extraction so corrected block IDs persist to note JSON payloads.
- Added regression coverage for duplicate `blockUid` and parent-remap behavior.
- Validation:
  - Python tests passed: `138 passed, 5 skipped`.
  - Python lint passed: `ruff check`.

## 2026-03-14 (Media Schema Repair Migration)
- Added forward repair migration `20260314_0007_note_assets_repair` to guarantee `public.note_assets` exists when prior migration chains were advanced but media table creation was skipped.
- Repair migration behavior:
  - create `public.note_assets` only when missing,
  - create `ix_note_assets_note_id` only when missing,
  - keep downgrade as no-op (irreversible repair semantics).
- Added migration unit tests in `tests/unit/test_note_assets_repair_migration.py`.
- Applied and verified on live compose DB:
  - `alembic_version = 20260314_0007`
  - `to_regclass('public.note_assets') = public.note_assets`

## 2026-03-14 (Media Transaction + SSR Hardening)
- Fixed media route transaction failure (`A transaction is already begun on this Session.`):
  - PostgreSQL table probe now uses bind-level execution and no longer starts a session transaction implicitly.
- Added regression coverage to ensure Postgres table probe path does not call `session.execute`.
- Fixed TipTap SSR hydration warning by setting `immediatelyRender: false` in editor initialization.
- Validation:
  - Python tests passed: `140 passed, 5 skipped`.
  - Web typecheck passed.
  - TipTap web tests passed in compose runtime.

## 2026-03-15 (Epic E11 S11.1 Local Graph Delivery)
- Added local graph contracts (Python + TypeScript) and API route `GET /v1/graph/local/{note_id}`.
- Added `LocalGraphService` with deterministic neighborhood traversal:
  - outbound wiki links and inbound backlinks,
  - optional entity extraction,
  - filter-driven include types,
  - hard node-limit truncation with deterministic ordering.
- Added workspace local graph panel with:
  - interactive sigma+graphology canvas,
  - keyboard/mouse filter controls,
  - note-node click navigation back into workspace selection.
- Added regression coverage:
  - API integration tests for neighborhood payload, truncation, and `404`,
  - service unit tests for second-hop traversal and type filtering,
  - UI tests for panel loading/error/render states.
- Validation:
  - API checks passed (`ruff`, `mypy` via `api/.venv/bin/*`),
  - Python tests passed: `147 passed, 5 skipped`,
  - Web typecheck passed,
  - Web tests passed: `87 passed`.

## 2026-03-17 (NLP Recall Gap and Hybrid Extraction Plan)
- Debug outcome:
  - Confirmed a production gap where lowercase informal notes can yield zero extracted entities, resulting in local graph payloads with only a note node and no mention edges.
  - Root cause: current spotting path is dictionary + title-case + acronym fallback; resolver/linker cannot recover entities that are never extracted.
- Decision:
  - Adopt a hybrid mention detection strategy for graph-facing extraction:
    - deterministic dictionary/EntityRuler first,
    - spaCy NER pass second,
    - deterministic regex fallback third,
    - stable dedup/ordering and existing resolver ranking unchanged.
  - Keep deterministic abstain (`NIL`) behavior to protect precision and avoid over-linking.
- Rationale:
  - Improves recall for real note-writing style (mixed casing, shorthand, informal prose) without replacing the current deterministic resolver architecture.
  - Preserves explainability by recording layer provenance and confidence.
- High-trust references consulted:
  - spaCy model and pipeline guidance: https://spacy.io/models/
  - spaCy EntityRuler API (deterministic matching): https://spacy.io/api/entityruler
  - spaCy EntityLinker/KB APIs (candidate-linking architecture): https://spacy.io/api/entitylinker and https://spacy.io/api/kb/
  - BLINK (bi-encoder + cross-encoder EL baseline): https://aclanthology.org/2020.emnlp-main.519/
  - REL (practical neural EL framework): https://github.com/informagi/REL
  - GLiNER (lightweight modern NER baseline): https://aclanthology.org/2024.naacl-long.300/

## 2026-03-17 (Epic E11 S11.2 Delivery: Hybrid Extraction + Recall Hardening)
- Implemented extraction structure and profile controls:
  - Added extractor strategy boundary (`dictionary`, `spacy`, `regex`) in `api/src/app/nlp/extractors.py`.
  - Added NLP config gates in `api/src/app/nlp/config.py`:
    - `NLP_EXTRACTION_PROFILE` (`rule-only` | `hybrid-spacy`)
    - `NLP_ENABLE_REGEX_FALLBACK`
    - `NLP_ENTITY_SEED_TERMS` (comma-separated seeded dictionary terms)
- Implemented deterministic hybrid extraction flow:
  - `api/src/app/nlp/spotting.py` now performs deterministic merge ordering and span-level dedup across extractor layers.
  - Added optional EntityRuler pattern bootstrapping for spaCy handles using alias/dictionary/seed terms.
- Added observability counters:
  - `NoteNlpPipeline` now records `dictionary_hits`, `spacy_hits`, `regex_hits`, and `merged_mentions`.
  - Counters are retrievable via `get_last_extraction_hit_counts()`.
- Added robustness regression coverage:
  - `tests/unit/test_entity_spotting.py`: lowercase multi-block recall + overlap dedup stability.
  - `tests/unit/test_nlp_pipeline.py`: per-layer extraction counters.
  - `tests/unit/test_nlp_config.py`: profile/seed env parsing.
  - `tests/unit/test_local_graph_service.py`: lowercase fixture yields entity + `MENTIONS` edges in local graph payload.
- Validation:
  - Python tests: `152 passed, 5 skipped`.
  - Web checks/tests: typecheck passed, `87` tests passed.
  - API static checks: `ruff` and `mypy` passed.

## 2026-03-18 (Lowercase Recall Follow-up)
- Expanded rule-only lowercase spotting fallback from non-overlapping regex matches to deterministic sliding n-gram extraction.
- Lowercase phrase filter now rejects stopword/verb windows but allows generic multi-word entity phrases without domain-token hard-coding.
- This improves recall for notes like `bayesian inference` / `variational methods` while keeping obvious action/noise phrases out.
- Validation:
  - Targeted spotting/NLP/local-graph suites passed.
  - Full Python suite passed: `153 passed, 5 skipped`.

## 2026-03-31 (Phase 1: Critical Production Blockers — UI/UX Spec)

Phase 1 of `docs/ui_ux_improvement_spec.md` delivered across 10 tasks. Goal: eliminate prototype-era UI patterns and establish a production-quality baseline.

**Task 1.1 — Replace `window.prompt()` with Modal Dialogs**
- Created `web/src/components/ui/Modal.tsx`: generic overlay dialog with `role="dialog"`, `aria-modal`, backdrop-click-to-close, and Escape key close.
- Created `web/src/components/ui/InputModal.tsx`: controlled input form inside Modal for single-field prompts (rename note, enter LaTeX).
- Replaced all `window.prompt()` calls in `NotesWorkspace.tsx` (rename note) and `TipTapEditor.tsx` (insert LaTeX inline, insert LaTeX block).
- Added `ConfirmModal.tsx` for destructive-action confirmation (note delete), replacing bare `window.confirm()`.

**Task 1.2 — Design System Foundation (Tokens + Focus Styles)**
- Added CSS custom properties to `globals.css` for color, spacing, radius, shadow, and typography tokens (`--color-*`, `--space-*`, `--radius-*`, `--shadow-*`, `--font-*`).
- Applied tokens uniformly across workspace and editor surfaces.
- Added visible `:focus-visible` ring using `--color-focus-ring` on all interactive elements — keyboard users now get a clear focus indicator everywhere.

**Task 1.3 — Fix Developer-Facing UI Strings**
- Replaced processing-status badges (`queued`, `processing`, `done`, `failed`) with user-facing copy (`Analyzing…`, `Ready`, `Analysis failed`).
- Replaced `save-status` raw strings with `Saving…`, `Saved`, `Save failed`.

**Task 1.4 — HTML Metadata (SEO, Favicons, Open Graph)**
- Updated `web/src/app/layout.tsx` with full `<meta>` set: title template, description, Open Graph tags, Twitter card.
- Added favicon reference set (SVG + fallback PNG) to `public/`.

**Task 1.5 — Global Error Boundary**
- Created `web/src/components/ui/ErrorBoundary.tsx` as a React class component error boundary.
- Wrapped the workspace root in `ErrorBoundary` so uncaught render errors show a recovery UI instead of a blank white screen.

**Task 1.6 — Toast Notification System**
- Created `web/src/components/ui/Toast.tsx` + `web/src/lib/toast.ts`: lightweight imperative toast API (`toast.success`, `toast.error`, `toast.info`).
- Toasts auto-dismiss after 4 s; manual dismiss via × button; ARIA `role="status"` for live region announcements.
- Replaced inline error string rendering in workspace with toast calls for non-fatal failures.

**Task 1.7 — Skeleton Loading States**
- Added skeleton shimmer components for the note list (`NoteListSkeleton`) and editor (`EditorSkeleton`) to replace blank panels during initial data fetch.
- CSS `@keyframes shimmer` animation via `globals.css`.

**Task 1.8 — Improve Empty States with CTAs**
- Note list empty state now renders an illustration + "Create your first note" CTA button rather than a bare text message.
- Search empty state distinguishes "no results for query" from "no notes yet".

**Task 1.9 — Improve Error Messages (Consistent + Actionable)**
- Standardized all user-visible error strings to follow `What went wrong. What to do.` format.
- Network/API errors now surface a `Retry` button where a retry is meaningful.

**Task 1.10 — Standardize Button Components**
- Created `web/src/components/ui/Button.tsx` with `variant` (`primary` | `secondary` | `ghost` | `danger`) and `size` props.
- Replaced ad-hoc `<button>` elements across workspace and editor with the shared component for consistent styling and disabled/loading states.

**Validation (Phase 1 complete)**
- Web typecheck passed.
- Web test suite passed: `87 passed` (includes regression coverage for modal interactions, confirm dialogs, optimistic rollbacks).
- One follow-up fix commit: updated existing tests that hard-coded old UI strings after Phase 1 label changes.

---

## 2026-03-31 (Phase 2: Core UX Polish — UI/UX Spec)

Phase 2 of `docs/ui_ux_improvement_spec.md` delivered across 6 tasks. Goal: match Notion/Obsidian interaction quality for the core editing and navigation loop.

**Task 2.1 — Design System Foundation (Phase 2 extension)**
- Extended CSS token set with animation/transition tokens (`--transition-fast`, `--transition-base`).
- Added `.interactive` utility class for consistent pointer cursor + transition on clickable elements.

**Task 2.2 — Hover & Focus States**
- Added hover highlight and focus ring to every note row in the sidebar list.
- Added hover/active states to toolbar buttons, context menu items, and tag chips.
- All states use design tokens; no hardcoded hex values.

**Task 2.3 — Keyboard Shortcut Documentation Modal**
- Created `web/src/components/ui/ShortcutsModal.tsx`: full reference table of keyboard shortcuts organized by section (Navigation, Editor, Actions).
- Trigger: `?` key when focus is not inside a text input; also accessible via Help button in workspace header.
- Modal uses existing `Modal.tsx` base; table styled with monospace `<kbd>` elements.

**Task 2.4 — Resizable Graph Panel**
- Made the local graph panel horizontally resizable via a drag handle on its left edge.
- Resize implemented with `mousedown`/`mousemove`/`mouseup` listeners and a CSS `cursor: col-resize` affordance.
- Panel width clamped to `[240px, 600px]`; width persisted in `localStorage` across sessions.
- Graph canvas receives `key={panelWidth}` to force Sigma re-mount on resize completion.

**Task 2.5 — Subject & Tag Picker Components**
- Created `web/src/components/editor/SubjectPicker.tsx`: combobox-style input with dropdown suggestions, keyboard navigation (Enter to commit, Escape to close), outside-click close, and "Use…" option for new subjects.
- Created `web/src/components/editor/TagPicker.tsx`: chip-based multi-select with:
  - Enter or comma key to add a tag,
  - × button to remove individual chips,
  - Backspace on empty input removes the last chip,
  - autocomplete dropdown filtered to exclude already-added tags,
  - "Add…" option for tags not in suggestions.
- Both components use `useId()` for accessible `aria-controls` linkage, `role="listbox"` / `role="option"` semantics, and `mouseDown` + `e.preventDefault()` on options to prevent input blur before selection.
- `aria-expanded` is explicitly coerced to `boolean` (`!!showDropdown`) — TypeScript requires `Booleanish | undefined`, not `string | boolean`.
- `NoteEditor.tsx` updated: replaced plain `<input>` fields for Subject and Tags with `SubjectPicker` and `TagPicker`. Tags are stored internally as `string[]`; `TagPicker` receives `parseTagsInput(tagsInput)` and emits `tags.join(", ")` back via `handleTagsChange`.
- `NotesWorkspace.tsx` updated: added `availableSubjects` and `availableTags` as `useMemo` values derived from loaded `notes` state — no extra API calls required since note list already carries `subject_id` and `tags`.

**Task 2.6 — Full-Text Search with Result Highlighting**
- Backend search was already implemented in `note_repository.py` via `func.lower(Note.note_title).like(like_pattern) OR func.lower(Note.content_text).like(like_pattern)`.
- Added frontend highlighting: `highlightMatch(text, query)` function in `NotesWorkspace.tsx` splits text on a regex built from the escaped query and wraps matching spans in `<mark className="search-highlight">`.
  - Special regex characters in the query are escaped via `.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")` before building the `RegExp`.
  - Returns `React.ReactNode` to allow inline `<mark>` elements inside note title and preview text.
- Applied to both `note_title` and `content_text` preview in the note list.
- `.search-highlight` CSS: `background: #fef08a; border-radius: 2px;` (yellow highlight, no bold/italic changes).

**Validation (Phase 2 complete)**
- Web typecheck passed.
- Web test suite passed after updating `NoteEditor.test.tsx` to use chip-based tag interaction (see test suite notes below).

---

## 2026-04-01 (Comprehensive Test Suite — Backend + Frontend)

Prior to this pass, the backend had zero pytest tests and the frontend had ~87 tests covering workspace and editor behavior but no component-level or API-client tests for Phase 2 additions.

**Backend — 71 pytest tests across 4 new files (`api/tests/`)**

`conftest.py` — shared fixtures:
- SQLite **file-based** DB via `tempfile.NamedTemporaryFile` (not in-memory).
  - Why: `note_asset_service.py` calls `inspect(engine)` which opens a second DB connection. With in-memory SQLite + `StaticPool`, SQLAlchemy's connection-pool reset-on-return issues a `ROLLBACK` mid-transaction, silently discarding all writes. File-based SQLite avoids this because the second connection still sees committed rows.
- FastAPI dependency override: `app.dependency_overrides[get_db_session] = override_get_db` where `override_get_db` is a generator yielding the test session.
- `PYTHONPATH=api/src:.` required to resolve `app.*` imports since `pyproject.toml` is at repo root but source lives in `api/src/`.
- Fixtures: `db_engine` (function-scoped, creates schema, deletes temp file on teardown), `session` (`autoflush=False, expire_on_commit=False`), `note_repo`, `block_repo`, `client` (FastAPI `TestClient`).

`test_note_repository.py` — 33 tests:
- `upsert_note`: normalization, tags, subject fallback to `inbox`, version increment, `409` conflict on duplicate title.
- `get_note`: present / missing.
- `list_notes`: all filter combinations (search, subject, tag, pinned, archived).
- `delete_note`, `list_backlinks_for_note`, wiki-link extraction.

`test_block_repository.py` — 18 tests:
- `replace_blocks`: UID generation, old block removal, `content_text` extraction.
- `list_blocks_for_note`, `search_blocks`, `list_block_backlinks`, `extract_block_refs`.

`test_notes_routes.py` — 11 tests:
- All CRUD HTTP endpoints with `200`/`204`/`400`/`404`/`409` response code assertions.

`test_backlinks_routes.py` — 9 tests:
- Note backlinks (empty, populated, `404`), block listing, block search, block backlinks (`404`, populated).

**Frontend — 46 new Vitest tests across 3 new files (`web/src/`)**

`components/editor/SubjectPicker.test.tsx` — 12 tests:
- Renders with value, dropdown on focus, suggestion filtering, `onChange` on click and Enter, "Use…" for new values, Escape closes, outside-click closes, disabled prop, value prop sync on external change.

`components/editor/TagPicker.test.tsx` — 13 tests:
- Chip rendering, remove chip (× button), add via Enter, add via comma, lowercase normalization, duplicate prevention, autocomplete dropdown, filtering already-added tags from suggestions, click suggestion, Backspace removes last tag, disabled prop, "Add…" option, clicking "Add…".

`lib/api-client.test.ts` — 21 tests:
- `global.fetch = vi.fn()` with `makeResponse(body, status)` helper.
- All API functions: URL construction, HTTP method/body, response parsing, `ApiClientError` on 4xx/5xx, `detail` field from JSON error body, `null` detail on non-JSON bodies, `Blob` handling for markdown export.

**NoteEditor test fix triggered by TagPicker integration:**
- `NoteEditor.test.tsx` "autosaves organization metadata updates" test broke because it used `fireEvent.change(tagsInput, { value: "graph, nlp" })` — a plain-text approach that no longer works with the chip-based `TagPicker`.
- Fix: simulate chip-based interaction:
  ```
  fireEvent.change(tags, { value: "graph" }) → fireEvent.keyDown(tags, { key: "," })
  fireEvent.change(tags, { value: "nlp" })   → fireEvent.keyDown(tags, { key: "Enter" })
  ```

**Validation (test suite complete)**
- Backend: `71 passed` via `PYTHONPATH=api/src:. api/.venv/bin/pytest api/tests/ -v`.
- Frontend: `133 passed` via `npm --prefix web run test`.
- Note: root `.venv` at repo root does not contain API deps. Use `api/.venv/bin/pytest` for backend tests.
