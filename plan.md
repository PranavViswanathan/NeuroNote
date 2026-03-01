# NeuroNote Implementation Plan

## Purpose
This document translates `initial_scoping_doc.md` into executable action items with full context, organized as:

- Epic
- Story
- Task
- Subtask

Each story follows the working rule from `codex.md`:

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

## Progress Snapshot (2026-03-01)
- Overall status: `Epic E0 complete`; `Epics E1-E9 not started`.
- Completed stories: `S0.1 Repository and service skeleton`, `S0.2 Quality bar and test harnesses`.
- Validation evidence:
  - `make setup` completed with `uv` and created `api/.venv`.
  - `make check` passed (`ruff`, `mypy`).
  - `make test` passed (`15` tests) and `tests/unit/test_structure.py` passed (`2` tests).
- Noted environment behavior: shell `VIRTUAL_ENV=.venv` differs from project `api/.venv`; `uv` ignores the shell env and uses project env correctly.

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

## Epic E1: Editor and Frontend Architecture
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

## Epic E2: Unified Database (PostgreSQL + Apache AGE + pgvector)
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

## Epic E3: NLP Pipeline (Fast Path)
Context: Product value depends on near-real-time extraction. The scoping doc targets ~60-130ms for common notes.

### Story S3.1: spaCy + keyphrase + relation extraction pipeline
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

### Story S3.2: NLP latency budget and performance regression control
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

## Epic E4: Entity Resolution and Canonicalization
Context: Graph usefulness depends on deduplicating aliases and near-duplicates into canonical entities.

### Story S4.1: Five-layer resolution funnel
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

### Story S4.2: Alias table persistence and feedback loop
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

## Epic E5: Global Knowledge Graph Schema and Sync
Context: NeuroNote differentiation depends on a typed, cross-subject, confidence-aware graph that stays in sync with note edits.

### Story S5.1: Typed node and relationship model
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

### Story S5.2: Idempotent delete-and-replace synchronization
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

## Epic E6: Graph Visualization (Sigma.js + Graphology)
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

## Epic E7: Background Processing and Queue Evolution
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

## Epic E8: Product UX Differentiation and Trust
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

## Epic E9: Deployment, Operations, and Observability
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
Subtask ST9.2.3.c: Add alerts for repeated processing failures.

## Cross-Epic Test Case Matrix (Minimum Viable Scenarios)
Context: These are mandatory scenarios that validate the full architecture promised in the scoping doc.

1. Note editing and autosave
- User edits a note rapidly for 30 seconds; only debounced saves are persisted.
- Last stable content is preserved after refresh.

2. Processing trigger and status
- Note save triggers async processing and returns immediately.
- Job status transitions are visible and terminal state is reachable.

3. NLP extraction quality baseline
- Common entities, keyphrases, and simple SVO relations are extracted from representative notes.
- Low-confidence outputs are flagged and can be filtered.

4. Entity resolution
- Abbreviations and orthographic variants resolve to canonical entities where alias evidence exists.
- Ambiguous matches remain unresolved when below confidence thresholds.

5. Graph synchronization
- Reprocessing same note is idempotent.
- Deleting concept text from note removes corresponding graph artifacts.

6. Graph visualization
- Local graph loads by default and remains interactive.
- Global graph requires explicit request and uses cached layouts when available.

7. Reliability and operations
- Service restart does not corrupt persisted note/graph state.
- Errors are logged with traceable IDs and surface meaningful diagnostics.

## Milestone Sequence
M1: In progress (`E0 complete`, `E1 pending`).
M2: E2 data layer and E3 baseline NLP complete.
M3: E4 resolution + E5 graph sync complete.
M4: E6 visualization + E7 async pipeline complete.
M5: E8 UX differentiation + E9 operational readiness complete.

## Definition of Done for Any Story
1. Structure artifacts created first.
2. Test cases written and reviewed before logic implementation.
3. Logic implemented with minimal, clear, slop-free comments and docs.
4. Test suite executed and passing for the written scenarios.
5. Acceptance criteria and operational notes documented.
