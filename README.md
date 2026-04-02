# NeuroNote

NeuroNote is a local-first, AI-powered knowledge base. You write notes in a rich editor, and the system automatically extracts concepts, builds a knowledge graph, and lets you explore how your ideas connect — all without leaving your workspace.

**Key capabilities:**
- **Rich editor** — TipTap-based with slash commands, wiki-links (`[[Note Title]]`), block references (`((uid))`), LaTeX math, images, and checklists
- **Automatic concept extraction** — NLP pipeline (rule-based, spaCy, or Claude-powered) identifies entities and relations in every note
- **Knowledge graph** — Apache AGE typed property graph; explore your notes as a D3 force-directed graph with hop depth, confidence, and node-type filters
- **Concept Insight Panel** — click any concept or entity node in the graph to see all related notes, an AI-generated synthesis paragraph grounded solely in your notes, and curated external learning links
- **Backlinks** — know which notes reference any note or block
- **Organization** — subjects (notebooks), tags, pinned notes, archive, full-text search
- **Markdown export** — zip archive with note.md + assets folder

---

## Services

| Service | Description |
|---|---|
| `web/` | Next.js 14 frontend — workspace sidebar, rich editor, graph panels |
| `api/` | FastAPI backend — note persistence, NLP processing, graph queries, media |
| `shared/` | Versioned TypeScript + Python request/response contracts |
| `infra/` | Docker Compose stack (PostgreSQL 16 + AGE + pgvector, API, Web) |
| `tests/` | Unit, integration, performance, and E2E tests |

---

## Quick Start (Docker Compose)

```bash
# 1. Start the full stack
make compose-up

# 2. Apply database migrations
make compose-migrate

# 3. Open in browser
open http://localhost:3000
```

**Custom ports** (if defaults are busy):
```bash
WEB_PORT=3001 API_PORT=8001 DB_PORT=5433 make compose-up
```

**Stop:**
```bash
make compose-down
```

Default URLs: Web `http://localhost:3000` · API `http://localhost:8000` · Postgres `localhost:5432`

---

## AI Features

### NLP Extraction Profiles

Every note save triggers background entity and relation extraction. Three profiles are available:

| Profile | How it works |
|---|---|
| `rule-only` | Dictionary matching + deterministic regex (default, no external dependencies) |
| `hybrid-spacy` | Dictionary + spaCy NER + regex fallback |
| `llm-enhanced` | Claude API — highest quality, requires `ANTHROPIC_API_KEY` |

Set via environment variable in `infra/docker-compose.yml` or on the command line:

```bash
# Hybrid spaCy
NLP_EXTRACTION_PROFILE=hybrid-spacy \
NLP_MODEL_NAME=spacy:en_core_web_sm \
make compose-up

# LLM-enhanced (requires ANTHROPIC_API_KEY)
NLP_EXTRACTION_PROFILE=llm-enhanced \
ANTHROPIC_API_KEY=sk-ant-... \
make compose-up
```

Seeding custom terms for deterministic recall:
```bash
NLP_ENTITY_SEED_TERMS="machine learning,knowledge graph,entity resolution" \
make compose-up
```

### Concept Insight Panel

When you click any non-note node (concept, entity, relation) in either graph view, a panel opens showing:

1. **Related Notes** — all notes mentioning the concept, with snippets, clickable to open
2. **AI Insight** — a synthesis paragraph drawn *only* from your notes (requires `ANTHROPIC_API_KEY`)
3. **Further Learning** — AI-suggested reputable external resources (clearly labeled; verify before visiting)

Without `ANTHROPIC_API_KEY`, notes list and snippets still render — the insight section shows a config hint.

**API:**
```bash
curl "http://localhost:8000/v1/concepts/insight?label=machine+learning&limit_notes=10"
```

---

## Editor Features

| Feature | How to trigger |
|---|---|
| Block type menu | Toolbar buttons (Paragraph, H1–H3, Bullet, Numbered, Checklist, Quote, Code, Divider) |
| Slash commands | Type `/` anywhere (e.g. `/h1`, `/bullet`, `/code`) |
| Command palette | `Cmd+K` / `Ctrl+K` |
| Wiki-link | `[[Note Title]]` — autocomplete + quick-create for new notes |
| Block reference | `((` — search and insert a reference to any block |
| Inline math | Wrap LaTeX in `$...$` or use the mathInline node |
| Block math | Use the mathBlock node or `/math` slash command |
| Linked mentions | Click "Linked mentions" in the editor panel |
| Keyboard shortcuts | `?` or the help button opens the shortcut reference |

---

## Knowledge Graph

### Local Graph (per-note)

Shows the neighborhood of a single note — note nodes, entity nodes, and relation edges up to N hops away.

**API:**
```bash
curl "http://localhost:8000/v1/graph/local/{note_id}?max_hops=1&limit_nodes=80&min_confidence=0.35&include_types=note,entity,relation"
```

Filter parameters:
- `max_hops` — neighborhood depth (1–2)
- `limit_nodes` — max nodes returned (1–150)
- `min_confidence` — entity confidence threshold (0.0–1.0)
- `include_types` — comma-separated: `note`, `entity`, `relation`

**UI:** Switch to the "Graph" tab in any note editor. Click a note node to open that note. Click any other node to open the Concept Insight Panel.

### Global Graph

Shows the full cross-note knowledge graph.

**API:**
```bash
curl "http://localhost:8000/v1/graph/global?limit_nodes=500&min_confidence=0.0&include_types=note,entity,relation"
```

**UI:** Accessible from the workspace sidebar global graph button.

---

## Organization

### Notes list filters

```bash
curl "http://localhost:8000/v1/notes?limit=20&offset=0&search=graph&subject_id=inbox&tag=ml&is_archived=false"
```

| Parameter | Description |
|---|---|
| `search` | Case-insensitive title + body text search |
| `subject_id` | Filter by subject/notebook |
| `tag` | Filter by normalized tag |
| `is_archived` | `false` (default) or `true` for archived notes |
| `is_pinned` | Optional `true`/`false` pinned filter |

### Subjects & Tags

Subjects (notebooks) and tags are managed via the note editor's three-dots menu. Notes can be assigned a subject, multiple tags, pinned, and archived. Pinned notes appear at the top of the sidebar.

---

## Project Docs

| File | Contents |
|---|---|
| `docs/plan.md` | Executable implementation plan and epic history |
| `docs/decisions.md` | Architecture decisions and operational notes |
| `docs/initial_scoping_doc.md` | Original requirements baseline |
| `docs/release_checklist.md` | Mandatory end-of-epic release gate sequence |
| `docs/retrospective_learnings.md` | Implementation insights |
| `docs/LLM.md` | LLM integration notes |
| `shared/contracts/README.md` | Versioned contract documentation |

---

## Development

### Common commands

```bash
make compose-up          # Start full stack
make compose-migrate     # Apply DB migrations
make compose-check       # Run API health checks
make compose-test        # Run API test suite
make compose-test-db     # Run PostgreSQL extension tests
make compose-logs        # Stream container logs
make compose-down        # Stop all containers
```

### Local fallback (no Docker)

```bash
make setup
make check
make test
make run-api-db   # Start API + local DB
make run-web      # Start Next.js dev server
```

### Schema management

Schema is migration-first (`DB_AUTO_CREATE=false` in the compose API runtime). Always run `make compose-migrate` after pulling changes that include new migrations.

Migration history:
- `20260307_0001` — core schema (notes, blocks, entities, entity_aliases)
- `20260307_0002` — entity_aliases idempotent repair
- `20260311_0003` — `notes.note_title` column
- `20260312_0004` — workspace organization (flags + note_tags)
- `20260313_0005` — media schema (note_assets)
- `20260314_0006` — block tree fields (block_uid, parent_block_uid, sibling_order)
- `20260314_0007` — note_assets schema drift repair
- `20260330_0008` — semantic embeddings (pgvector)
- `20260401_0009` — processing jobs persistence
- `20260402_0010` — concept registry

---

## API Reference

### Notes

| Method | Path | Description |
|---|---|---|
| `GET` | `/v1/notes` | List notes (supports filters above) |
| `GET` | `/v1/notes/{note_id}` | Get a single note |
| `PUT` | `/v1/notes/{note_id}` | Create or update a note |
| `DELETE` | `/v1/notes/{note_id}` | Delete a note |
| `GET` | `/v1/notes/{note_id}/backlinks` | Note backlinks |
| `GET` | `/v1/notes/{note_id}/blocks` | Block tree for a note |
| `GET` | `/v1/notes/{note_id}/export/markdown` | Download markdown zip |

### Blocks

| Method | Path | Description |
|---|---|---|
| `GET` | `/v1/blocks/search?q=...&limit=10` | Search blocks by text |
| `GET` | `/v1/blocks/{block_uid}/backlinks` | Block backlinks |

### Processing

| Method | Path | Description |
|---|---|---|
| `POST` | `/v1/process-note` | Queue NLP processing for a note |
| `GET` | `/v1/process-status/{job_id}` | Poll job status (`queued→running→completed/failed`) |
| `GET` | `/v1/backfill-status` | Startup backfill progress |

### Graph

| Method | Path | Description |
|---|---|---|
| `GET` | `/v1/graph/local/{note_id}` | Local neighborhood graph |
| `GET` | `/v1/graph/global` | Full cross-note graph |
| `GET` | `/v1/concepts/insight` | AI concept insight (label + related notes) |

### Entity Aliases

| Method | Path | Description |
|---|---|---|
| `POST` | `/v1/entity-aliases/confirm` | Register a canonical alias |
| `POST` | `/v1/entity-aliases/resolve-preview` | Preview resolution output |
| `GET` | `/v1/entity-aliases/calibration` | Calibration metrics |

### Media

| Method | Path | Description |
|---|---|---|
| `POST` | `/v1/media/uploads` | Upload image (base64 JSON payload) |
| `GET` | `/v1/media/{asset_id}` | Retrieve media asset |
| `DELETE` | `/v1/media/{asset_id}` | Delete media asset |

### Connections

| Method | Path | Description |
|---|---|---|
| `GET` | `/v1/connections/{note_id}` | Immediate neighbors of a note |

---

## Validation Flows

### Processing pipeline

```bash
# 1. Save a note
curl -sS -X PUT http://127.0.0.1:8000/v1/notes/demo-note \
  -H 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{"note_id":"demo-note","note_title":"Graph Reasoning Notes","subject_id":"inbox","tags":["graph","ml"],"is_pinned":true,"is_archived":false,"content_json":{"type":"doc","content":[{"type":"paragraph","content":[{"type":"text","text":"Machine Learning improves Graph Reasoning across Notes"}]}]},"content_text":"Machine Learning improves Graph Reasoning across Notes","updated_at":"2026-03-07T12:00:00Z"}
JSON

# 2. Queue NLP processing
HASH=$(printf 'Graph Reasoning Notes\n\nMachine Learning improves Graph Reasoning across Notes' | shasum -a 256 | awk '{print $1}')
curl -sS -X POST http://127.0.0.1:8000/v1/process-note \
  -H 'Content-Type: application/json' \
  -d "{\"note_id\":\"demo-note\",\"content_text\":\"Graph Reasoning Notes\n\nMachine Learning improves Graph Reasoning across Notes\",\"content_hash\":\"$HASH\",\"updated_at\":\"2026-03-07T12:00:00Z\"}"

# 3. Poll until completed
curl http://127.0.0.1:8000/v1/process-status/<job_id>
```

### Entity alias resolution

```bash
# Register a canonical alias
curl -sS -X POST http://127.0.0.1:8000/v1/entity-aliases/confirm \
  -H 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{"alias_text":"ML","canonical_entity_id":"concept-machine-learning","canonical_name":"Machine Learning","confidence":0.95}
JSON

# Preview resolution
curl -sS -X POST http://127.0.0.1:8000/v1/entity-aliases/resolve-preview \
  -H 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{"entities":[{"entity_id":"entity-1","text":"ML","label":"acronym","confidence":0.8}]}
JSON

# Calibration metrics
curl http://127.0.0.1:8000/v1/entity-aliases/calibration
```

### Block-scoped mention evidence

```bash
# Confirm MENTIONS edges are block-scoped
docker compose -f infra/docker-compose.yml exec -T db psql -U neuronote -d neuronote -c \
  "LOAD 'age'; SET search_path = ag_catalog, \"\$user\", public;
   SELECT * FROM cypher('neuronote', \$\$ MATCH (b:Block)-[r:MENTIONS]->(e:Entity)
   WHERE r.source_note_id='demo-note'
   RETURN b.id, e.id, r.mention_text, r.start_offset, r.end_offset \$\$)
   AS (block_id agtype, entity_id agtype, mention_text agtype, start_offset agtype, end_offset agtype);"
```

### Backlinks

```bash
# Create two notes where one references the other via wiki-link
curl -sS -X PUT http://127.0.0.1:8000/v1/notes/target-note \
  -H 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{"note_id":"target-note","note_title":"Target Note","subject_id":"inbox","tags":[],"is_pinned":false,"is_archived":false,"content_json":{"type":"doc","content":[{"type":"paragraph","content":[{"type":"text","text":"Target"}]}]},"content_text":"Target","updated_at":"2026-03-13T13:00:00Z"}
JSON

curl -sS -X PUT http://127.0.0.1:8000/v1/notes/source-note \
  -H 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{"note_id":"source-note","note_title":"Source Note","subject_id":"inbox","tags":[],"is_pinned":false,"is_archived":false,"content_json":{"type":"doc","content":[{"type":"paragraph","content":[{"type":"text","text":"See [[Target Note]]"}]}]},"content_text":"See [[Target Note]]","updated_at":"2026-03-13T13:01:00Z"}
JSON

curl http://127.0.0.1:8000/v1/notes/target-note/backlinks
```

### Duplicate title guardrail

```bash
# Second note with same title returns 409 note_title_conflict
curl -sS -X PUT http://127.0.0.1:8000/v1/notes/conflict-b \
  -H 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{"note_id":"conflict-b","note_title":"Duplicate Guard","subject_id":"inbox","tags":[],"is_pinned":false,"is_archived":false,"content_json":{"type":"doc","content":[{"type":"paragraph","content":[{"type":"text","text":"B"}]}]},"content_text":"B","updated_at":"2026-03-13T13:11:00Z"}
JSON
```

### Concept insight

```bash
curl "http://127.0.0.1:8000/v1/concepts/insight?label=machine+learning&limit_notes=10"
```

Expected response fields: `concept_label`, `notes_found`, `note_refs` (with `snippet`), `insight` (null without API key), `learning_links`, `generated_at`.

### Math + image + export

```bash
# Upload image
B64=$(printf '\x89PNG\r\n\x1a\nabc' | base64)
curl -sS -X POST http://127.0.0.1:8000/v1/media/uploads \
  -H 'Content-Type: application/json' \
  --data-binary @- <<JSON
{"note_id":"demo-note","filename":"diagram.png","mime_type":"image/png","content_base64":"$B64"}
JSON

# Export markdown zip
curl -sS http://127.0.0.1:8000/v1/notes/demo-note/export/markdown --output demo-note.zip
unzip -l demo-note.zip
```

### Startup backfill status

```bash
curl http://127.0.0.1:8000/v1/backfill-status
# Returns: total_notes, processed_notes, failed_notes, in_progress
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `relation "note_assets" does not exist` | Run `make compose-migrate` |
| Insight section shows config hint | Set `ANTHROPIC_API_KEY` in compose env |
| spaCy model not found | Install the model inside the API container or use `rule-only` profile |
| AGE concurrent lock error in logs | Known AGE issue with parallel note processing — non-critical, retries succeed |
| Port already in use | Use `WEB_PORT=3001 API_PORT=8001 make compose-up` |

Before declaring work complete, run the full gate sequence in `docs/release_checklist.md`.
