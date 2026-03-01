# NeuroNote: comprehensive project scoping research

**NeuroNote can become the first note-taking tool where writing a note automatically builds a typed knowledge graph — no brackets, no manual linking, no user effort.** This is the single biggest unmet need in the knowledge management space. Every major competitor (Roam, Obsidian, Logseq) requires manual `[[bracket]]` linking; only Mem.ai approaches automatic connection discovery, but it focuses on surfacing similar notes rather than building a persistent, entity-resolved graph with typed relationships. The technical stack to deliver this is mature and achievable: TipTap for editing, PostgreSQL with Apache AGE for unified storage, spaCy for NLP extraction at ~100ms per note, and Sigma.js for graph visualization at scale. What follows is a detailed technical blueprint across seven research areas.

---

## 1. The editor and frontend architecture

**TipTap is the clear winner for NeuroNote's rich text editor.** Built on ProseMirror (the gold standard document editing framework), TipTap provides a friendly abstraction layer with 100+ tree-shakable extensions, excellent React/Next.js integration via `@tiptap/react` hooks, and first-class Yjs collaboration support. Its headless architecture means full control over UI, and when custom behavior is needed, you can drop down to raw ProseMirror APIs. Liveblocks, the collaboration infrastructure company, explicitly recommends TipTap as their top editor pick for 2025.

**BlockNote** deserves consideration as an accelerator — it's built on top of TipTap and ProseMirror, providing Notion-style block editing out of the box (drag-and-drop, slash commands, nesting). However, at least one production team reported hitting schema rigidity walls and switching to raw TipTap. For NeuroNote's custom knowledge graph integration — where concept highlights, inline entity links, and custom block types are inevitable — TipTap's flexibility is worth the extra initial setup. **Slate.js** (and its batteries-included layer Plate) remains React-first but suffers from poor Android support and sparse documentation. **Lexical** (Meta) lacks pure collaborative editing support. Neither is recommended.

For real-time editing, the strategy should be **debounced autosave** (500–1000ms after last keystroke) for the MVP, graduating to **Yjs CRDT** integration via TipTap's `@tiptap/extension-collaboration` and the open-source Hocuspocus backend when collaboration is needed. Store TipTap/ProseMirror JSON directly in PostgreSQL's JSONB column — this preserves full document structure and is queryable. NLP processing should be triggered on a separate, more aggressive debounce (3–5 seconds after last edit, or on note blur/close) to avoid processing partial edits.

---

## 2. A single database can handle everything

The most impactful architectural decision is database strategy. Rather than running PostgreSQL for notes and Neo4j for the graph (doubling operational complexity, backup strategies, and hosting costs), **PostgreSQL with the Apache AGE extension** provides Cypher graph queries directly inside PostgreSQL. Combined with **pgvector** for semantic embeddings, a single database handles note storage (JSONB), knowledge graph traversal (Cypher via AGE), full-text search (tsvector), and vector similarity search — all with one connection pool, one backup, one hosting bill.

Apache AGE became an Apache Top Level Project in 2022. It stores graph data (nodes, edges with properties) as PostgreSQL tables and allows mixing SQL and Cypher in the same query. Performance is sufficient for a personal knowledge graph with thousands to tens of thousands of nodes, though it won't match Neo4j for deep traversals on massive datasets. Azure Database for PostgreSQL natively supports AGE, and Docker images are available for local development.

The alternative approaches break down as follows:

- **PostgreSQL + Neo4j (dual database)**: Gold standard for large-scale production but operationally complex. Neo4j Community Edition is single-instance only; Aura starts at ~$65/month. Only justified if graph query complexity outgrows AGE.
- **SurrealDB**: The most intriguing multi-model option — native document, graph, and vector search in one database with SQL-like syntax. Still maturing (v2.0 released recently), smaller community. Worth revisiting in 12–18 months.
- **ArangoDB**: More battle-tested multi-model database, but graph traversals are simulated via indexes (no index-free adjacency), making deep traversals slower than Neo4j.

If graph query performance becomes a bottleneck at scale, migrating the graph layer to Neo4j while keeping notes in PostgreSQL is a clean upgrade path. **Start with one database; split only when forced.**

---

## 3. The NLP pipeline processes a note in under 150 milliseconds

The core NLP pipeline should use **spaCy `en_core_web_lg`** as the primary model — it delivers **85.5% NER accuracy** at ~10,000 words per second on CPU, a sweet spot between the smaller models (lower accuracy) and the transformer model `en_core_web_trf` (89.8% accuracy but 15× slower on CPU). For a ~200-word note, the complete fast-path pipeline takes approximately **60–130ms**:

| Stage | Time | Purpose |
|-------|------|---------|
| spaCy full pipeline | ~20ms | Tokenization, POS tagging, dependency parsing, NER |
| PyTextRank keyphrases | ~5–10ms | Ranked concept phrase extraction |
| Entity resolution | ~10–50ms | Normalize, fuzzy match, deduplicate |
| Dependency-based relation extraction | ~5ms | Subject-verb-object triples |
| Embedding generation (MiniLM) | ~10–20ms | Sentence vectors for similarity |
| Database writes | ~10–30ms | Upsert graph nodes and edges |

Standard spaCy NER recognizes OntoNotes types (PERSON, ORG, GPE, DATE) but not abstract concepts like "machine learning" or "design patterns." Three strategies extend this: **EntityRuler** for pattern-based rules (fast, deterministic), **fine-tuned NER** trained on annotated note examples for custom labels (CONCEPT, TOPIC, TECHNOLOGY), and **spacy-llm** for zero-shot concept extraction via LLM prompting (best for prototyping, too slow for production throughput). **PyTextRank** adds graph-based keyphrase extraction as a spaCy pipeline component, excellent for identifying the most important concept phrases in each note.

For relation extraction, **dependency-based SVO (subject-verb-object) triple extraction** should be the primary fast layer — it runs at full spaCy speed and catches simple relational patterns. **REBEL** (Babelscape/rebel-large, a BART-based seq2seq model supporting 200+ Wikidata relation types) can serve as an optional enrichment layer for longer, well-structured notes, though its ~1.6GB model is heavy and biased toward formal text. For a personal tool, the dependency approach covers the critical 80% of relationships.

**Coreference resolution** (resolving "it" and "this approach" to their referents) is moderately important. The recommended library is **Coreferee** (works with spaCy 3.0–3.5, rule + neural hybrid) or **spaCy's experimental CoreferenceResolver**. Apply only to notes longer than 3 sentences — shorter notes rarely have ambiguous pronouns.

---

## 4. Entity resolution turns "ML" and "machine learning" into one node

Entity deduplication is critical for graph quality. A **five-layer funnel** handles progressively harder cases:

**Layer 1 — Normalization** (instant): Lowercase, strip hyphens/underscores, collapse whitespace. "Machine-Learning" → "machine learning." **Layer 2 — Abbreviation expansion**: Maintain a lookup table bootstrapped from Wikipedia abbreviation lists, grown organically by detecting patterns like "Machine Learning (ML)" in notes. **Layer 3 — Fuzzy string matching** with RapidFuzz (C++-optimized, threshold ≥ 90): Catches typos and word-order differences. **Layer 4 — Embedding similarity** with `all-MiniLM-L6-v2` (cosine similarity threshold ≥ 0.85): Catches semantic equivalence that string matching misses, but must be used as a candidate generator only — embeddings measure relatedness, not identity. **Layer 5 — Entity alias table**: All resolved aliases stored in a persistent table mapping aliases to canonical concept IDs, enabling instant exact-match lookups for previously resolved entities.

This funnel architecture means the vast majority of entities resolve in layers 1–2 (sub-millisecond), with progressively expensive methods applied only to genuinely ambiguous cases. User confirmation can optionally gate low-confidence matches, building the alias table through feedback.

---

## 5. The knowledge graph schema spans subjects by design

The graph should use a **block-level granularity** model with six node types and a rich relationship vocabulary:

**Node types**: `Subject` (organizational folder), `Note` (user-created document), `Block` (atomic content unit — paragraph, heading, list item), `Concept` (extracted semantic topic/idea), `Entity` (named entity — person, organization, place), `Tag` (user-assigned label). **Key relationship types**: `BELONGS_TO` (Note → Subject), `CONTAINS` (Note → Block), `MENTIONS` (Block → Concept/Entity, with confidence score and text span), `RELATED_TO` (Concept ↔ Concept), `CO_OCCURS_WITH` (Concept ↔ Concept, with frequency count), `PART_OF` (Concept → Concept for hierarchical relationships), and `APPEARS_IN` (Concept → Subject, tracking cross-subject presence).

Every NLP-extracted edge should carry a **`confidence` float (0.0–1.0)** enabling quality filtering. All nodes and relationships need `created_at` and `updated_at` timestamps. Concept nodes should maintain a denormalized `mention_count` for fast ranking. Block nodes store a `content_hash` (SHA-256) for efficient change detection.

**The graph must be global, spanning all subjects.** This is essential because NeuroNote's core value proposition is discovering cross-subject connections — a concept like "Bayesian inference" appearing in both a Statistics subject and a Machine Learning subject is exactly the kind of insight the system should surface. Subject membership is tracked via `APPEARS_IN` relationships, and the UI provides subject-scoped filtering without fragmenting the underlying graph.

Block-based storage (rather than document-based) is strongly recommended for NLP integration. Each block has a clean `content` field that NLP models consume directly, extraction results map precisely to block-level spans, and when a block changes, only that block needs reprocessing. Store blocks in PostgreSQL with a `rich_content` JSONB column (ProseMirror JSON format) and a plain-text `content` column for NLP consumption.

---

## 6. Sigma.js renders thousands of nodes at interactive framerates

For graph visualization, **Sigma.js with `@react-sigma/core`** is the primary recommendation. Its WebGL rendering handles **thousands of nodes smoothly** — critical for a knowledge graph that grows indefinitely. The `graphology` data model cleanly separates graph data structure from rendering, making it straightforward to compute local and global subgraph views. The React integration provides hooks-based API (`useLoadGraph`, `useRegisterEvents`, `useSigma`), and `graphology-layout-forceatlas2` can run layout computation in a Web Worker to avoid blocking the main thread.

The performance hierarchy across rendering technologies is significant: **SVG** caps out at ~500–1,000 nodes (DOM overhead), **Canvas** handles ~3,000–10,000 nodes, and **WebGL** pushes to 10,000–100,000+ nodes. Both Obsidian and Logseq use PIXI.js (WebGL with Canvas fallback) for their graph views — NeuroNote should target the same performance tier.

**react-force-graph-2d** is the simpler alternative — the API is trivially simple (pass a `graphData` prop with `{nodes: [], links: []}`) and Canvas-based 2D rendering handles graphs up to ~4,000 elements. It's ideal for rapid prototyping and sufficient if the graph stays under a few thousand nodes. **Cytoscape.js** offers the richest layout algorithm ecosystem (force-directed, hierarchical, radial, dagre, klay) and built-in graph analysis (PageRank, betweenness centrality) but performance degrades beyond ~10,000 elements.

Implementation should follow the Obsidian pattern: **local graph by default** (1–3 hops from the current note, always computed client-side) and **global graph on demand** (pre-computed server-side via graphology on Node.js for graphs exceeding 3,000 nodes, with cached positions sent to the client for rendering-only). Node size should reflect connection count (degree centrality) for instant visual hierarchy, and color coding by concept type (person, topic, technology) provides categorical context.

---

## 7. Background processing should start embarrassingly simple

For a personal tool, a full distributed task queue is overkill. The recommended progression:

**Phase 1 (start here)**: FastAPI's built-in `BackgroundTasks` — zero additional infrastructure. When a note is saved, the Next.js API route calls the Python FastAPI service, which returns `202 Accepted` immediately and processes the note in a background thread. The frontend polls for completion. If the Python service restarts mid-processing, the job is lost — acceptable for a single-user app since the note will reprocess on next save. **No Redis, no message broker, no task queue.**

**Phase 2 (when reliability matters)**: Add **Huey** — a lightweight Python task queue backed by Redis. Huey's performance is excellent (3.62s for 20,000 jobs in benchmarks), setup is minimal (`pip install huey`, decorate functions with `@huey.task()`, run `huey_consumer.py`), and it supports retries, priority queues, and periodic scheduling. Redis also serves as pub/sub for notifying the frontend when processing completes.

The processing trigger should be **debounced on-save**: wait 2–3 seconds after the last edit, then auto-save and queue processing. At the queue level, coalesce rapid edits by replacing any existing pending job for the same note rather than creating duplicates. The pipeline itself should be a **single monolithic task** (not broken into separate queued stages) because spaCy's pipeline components are tightly coupled and splitting them adds serialization overhead with zero benefit for single-user processing.

**Full-note reprocessing** is strongly recommended over incremental/diff-based processing. spaCy processes ~10,000 words/second — a 2,000-word note takes under 200ms. The engineering cost of building sentence-level diffing, maintaining NLP context boundaries, and reconciling partial graph updates vastly exceeds the processing time saved. Use a **delete-and-replace pattern**: on each processing run, delete all graph entries sourced from that note (tracked via `source_note_id`), then insert fresh extractions. This ensures idempotency and handles deletions automatically.

---

## 8. Competitive landscape reveals one clear gap

Analysis of seven major competitors reveals a stark divide: tools are either fully manual (Roam, Obsidian, Logseq, Reflect) or loosely AI-automated (Mem.ai). None combines entity extraction, relationship typing, continuous background processing, confidence scoring, and persistent knowledge graph construction.

**Roam Research** popularized bidirectional linking but is declining — $15/month with no free tier, a closed ecosystem, and a graph view widely considered the weakest among competitors. **Obsidian** has the best graph view (PIXI.js/WebGL, excellent local graph, rich filtering) and the closest existing approximation to NeuroNote via its **Smart Connections plugin** (AI embeddings for semantic note similarity). But Smart Connections is a bolt-on that shows similar notes in a sidebar — it doesn't extract entities, type relationships, or build a persistent graph. **Logseq** mirrors Roam's features as open-source and local-first but adds no automatic linking. **Mem.ai** is the most direct competitor, using AI for automatic categorization and "Similar Mems" surfacing, but it focuses on search and organization rather than building an explorable typed knowledge graph. **Tana** demonstrates the power of typed relationships (via supertags), showing that "Person X works on Project Y" is far more useful than "Page A links to Page B" — but all its typing is manual.

The UX patterns that work across all tools are: **sidebar backlinks panel** with surrounding context (not just titles), **local graph view** as default (global graph becomes an unnavigable hairball beyond ~500 notes), **confidence/relevance scoring** for transparent connection quality, and **inline context snippets** showing why a connection exists. NeuroNote should surface auto-discovered connections passively (sidebar, subtle inline indicators) rather than interrupting the writing flow, with one-click confirmation to promote suggestions to permanent links.

Athens Research — the open-source Roam clone backed by YC — shut down in 2022–2023 because pure cloning offered no differentiation. This reinforces that NeuroNote's automatic semantic processing is not just a feature but a survival requirement for differentiation.

---

## Recommended technology stack summary

| Decision | Recommendation | Rationale |
|----------|---------------|-----------|
| **Editor** | TipTap | Best extensibility, ProseMirror foundation, Yjs collaboration, 34k GitHub stars |
| **Database** | PostgreSQL + Apache AGE + pgvector | Single DB for notes (JSONB), graph (Cypher), embeddings (vectors) |
| **Backend** | Next.js API routes + FastAPI microservice | JS for CRUD/auth/SSR, Python for NLP pipeline |
| **NLP model** | spaCy `en_core_web_lg` + PyTextRank | 85.5% NER accuracy, ~10k words/sec, keyphrase extraction |
| **Embeddings** | `all-MiniLM-L6-v2` via sentence-transformers | 384d vectors, ~14k sentences/sec on GPU, stored in pgvector |
| **Entity resolution** | RapidFuzz + embedding similarity + alias table | Multi-layer funnel from fast deterministic to expensive semantic |
| **Graph visualization** | Sigma.js (`@react-sigma/core`) | WebGL rendering, handles 10k+ nodes, graphology ecosystem |
| **Task processing** | FastAPI BackgroundTasks → Huey (Phase 2) | Minimal infrastructure, adequate for single-user |
| **Real-time editing** | Debounced autosave → Yjs CRDT (Phase 2) | Start simple, add collaboration when needed |
| **Deployment** | Docker Compose (self-hosted) | Next.js + FastAPI + Redis + PostgreSQL on single VPS |

---

## Conclusion: what makes this achievable

Three technical insights de-risk this project significantly. First, **spaCy's processing speed** (~100ms per note on CPU) means background processing is nearly invisible — no complex distributed systems needed, just a simple debounced trigger and a single Python process. Second, **PostgreSQL with AGE + pgvector** eliminates the dual-database complexity that would otherwise dominate development time — one database handles notes, graph, and vectors with familiar tooling. Third, the **delete-and-replace idempotency pattern** means the sync problem between note content and knowledge graph reduces to a simple, reliable operation rather than a complex incremental reconciliation system.

The hardest unsolved problem is not infrastructure but NLP quality: **entity resolution across informal note-taking text** and **meaningful relationship extraction from fragmentary sentences**. Notes are not Wikipedia articles — they contain abbreviations, incomplete sentences, personal shorthand, and domain-specific jargon. The multi-layer entity resolution funnel and the ability to fine-tune spaCy's NER on annotated note samples are the key mitigations. Starting with a high-confidence threshold (showing fewer but more accurate connections) and letting users calibrate sensitivity through feedback will build trust in the automatic system faster than showing every possible connection immediately.