# NeuroNote

NeuroNote is a monorepo with a web frontend, a Python API service, shared contracts, and infrastructure configuration.

## Services
- `web/`: Next.js frontend with workspace sidebar (create/open/right-click actions), pinned/all note sections, organization controls, editor autosave orchestration, and API clients.
- `api/`: FastAPI service for health, note persistence/listing, organization-aware note queries, deterministic note-processing endpoints (block-level entity mentions + canonical resolution), note/block backlink retrieval, block hierarchy APIs, media asset upload/retrieval/deletion, and markdown export.
- `shared/`: versioned request/response contracts shared across services.
- `infra/`: local infrastructure orchestration.
- `tests/`: repository-level structure and integration tests.

## Project Docs
- `docs/codex.md`: project working instructions.
- `docs/plan.md`: executable implementation plan and architecture decisions.
- `docs/initial_scoping_doc.md`: original scoping and requirements baseline.
- `docs/decisions.md`: non-plan implementation notes and operational decisions.

## Recommended Workflow (Docker Compose + uv)
This is the default way to run NeuroNote now. API commands still use `uv`, but inside Docker containers.

### Quick Start
1. Ensure Docker Desktop is running.
2. Start full stack:
   - `make compose-up`
   - If default ports are busy:
     - `WEB_PORT=3001 API_PORT=8001 DB_PORT=5433 make compose-up`
3. Apply migrations:
   - `make compose-migrate`
4. Run API checks:
   - `make compose-check`
5. Run API tests:
   - `make compose-test`
6. Open browser:
   - `http://localhost:3000`
7. Stop stack:
   - `make compose-down`

Schema ownership is migration-first:
- `DB_AUTO_CREATE=false` in compose API runtime.
- PostgreSQL auto-create is disabled in app startup logic.
- Migration `20260307_0002` is idempotent for pre-existing `entity_aliases` tables.
- Migration `20260311_0003` is idempotent for pre-existing `notes.note_title` columns.
- Migration `20260312_0004` is idempotent for workspace-organization schema (`notes` flags + `note_tags`).
- Migration `20260313_0005` is idempotent for media schema (`note_assets`).
- Migration `20260314_0006` backfills tree block fields (`block_uid`, `parent_block_uid`, `sibling_order`) and constraints.

### Common Commands
- API checks: `make compose-check`
- API tests: `make compose-test`
- PostgreSQL extension tests: `make compose-test-db`
- Bootstrap DB extensions manually: `make compose-bootstrap-extensions`
- Stream logs: `make compose-logs`

### Default URLs
- Web: `http://localhost:3000`
- API: `http://localhost:8000`
- Postgres: `localhost:5432`

If you override `WEB_PORT` / `API_PORT` / `DB_PORT`, use those port numbers in URLs and DB clients.

## Local Fallback (Native uv)
Use this only if you explicitly want a non-container local run.

1. `make setup`
2. `make check`
3. `make test`
4. `make run-api-db` and `make run-web`

`make run-api` still enables sqlite auto-create for quick local-only bootstrapping.

## Validate Processing Flow
1. Save a note through API:
   - Use heredoc payload to avoid shell-escaped JSON issues:
```bash
curl -sS -X PUT http://127.0.0.1:8000/v1/notes/demo-note \
  -H 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{"note_id":"demo-note","note_title":"Graph Reasoning Notes","subject_id":"inbox","tags":["graph","ml"],"is_pinned":true,"is_archived":false,"content_json":{"type":"doc","content":[{"type":"paragraph","content":[{"type":"text","text":"Machine Learning improves Graph Reasoning across Notes"}]}]},"content_text":"Machine Learning improves Graph Reasoning across Notes","updated_at":"2026-03-07T12:00:00Z"}
JSON
```
2. Trigger processing:
   - Hash helper: `HASH=$(printf 'Graph Reasoning Notes\n\nMachine Learning improves Graph Reasoning across Notes' | shasum -a 256 | awk '{print $1}')`
```bash
curl -sS -X POST http://127.0.0.1:8000/v1/process-note \
  -H 'Content-Type: application/json' \
  -d "{\"note_id\":\"demo-note\",\"content_text\":\"Graph Reasoning Notes\n\nMachine Learning improves Graph Reasoning across Notes\",\"content_hash\":\"$HASH\",\"updated_at\":\"2026-03-07T12:00:00Z\"}"
```
3. Poll status:
   - `curl http://127.0.0.1:8000/v1/process-status/<job_id>`
4. Expected status flow:
   - `queued -> running -> completed` (or `failed` with `error` populated).

## Validate Startup Backfill Status
After API startup (PostgreSQL mode), check async backfill progress:

```bash
curl -sS http://127.0.0.1:8000/v1/backfill-status
```

Response shape:
- `total_notes`
- `processed_notes`
- `failed_notes`
- `in_progress`

## Validate Entity Resolution Flow
1. Confirm a canonical alias:
```bash
curl -sS -X POST http://127.0.0.1:8000/v1/entity-aliases/confirm \
  -H 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{"alias_text":"ML","canonical_entity_id":"concept-machine-learning","canonical_name":"Machine Learning","confidence":0.95}
JSON
```
2. Preview resolution output (resolved + unresolved):
```bash
curl -sS -X POST http://127.0.0.1:8000/v1/entity-aliases/resolve-preview \
  -H 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{"entities":[{"entity_id":"entity-1","text":"ML","label":"acronym","confidence":0.8},{"entity_id":"entity-2","text":"xqzv_123","label":"acronym","confidence":0.4}]}
JSON
```
3. Check calibration metrics:
   - `curl http://127.0.0.1:8000/v1/entity-aliases/calibration`

## Validate Deterministic Mention Evidence Flow
1. Save a note with multiple blocks where only one block contains a target entity.
2. Trigger `/v1/process-note` and wait for `completed`.
3. Confirm graph note node still exists:
   - `docker compose -f infra/docker-compose.yml exec -T db psql -U neuronote -d neuronote -c "LOAD 'age'; SET search_path = ag_catalog, \"\\$user\", public; SELECT * FROM cypher('neuronote', \\$\\$ MATCH (n:Note {id:'demo-note'}) RETURN n.id \\$\\$) AS (id agtype);"`
4. Confirm `MENTIONS` edges are block-scoped and mention-evidence based:
   - `docker compose -f infra/docker-compose.yml exec -T db psql -U neuronote -d neuronote -c "LOAD 'age'; SET search_path = ag_catalog, \"\\$user\", public; SELECT * FROM cypher('neuronote', \\$\\$ MATCH (b:Block)-[r:MENTIONS]->(e:Entity) WHERE r.source_note_id='demo-note' RETURN b.id, e.id, r.mention_text, r.start_offset, r.end_offset \\$\\$) AS (block_id agtype, entity_id agtype, mention_text agtype, start_offset agtype, end_offset agtype);"`

## Validate Workspace Filters
The notes list endpoint supports workspace organization filters:

```bash
curl -sS "http://127.0.0.1:8000/v1/notes?limit=20&offset=0&search=graph&subject_id=inbox&tag=ml&is_archived=false"
```

Useful query params:
- `search`: title/body text search (case-insensitive)
- `subject_id`: filter by subject/notebook id
- `tag`: filter by normalized tag
- `is_archived`: defaults to `false`; set `true` to list archived notes
- `is_pinned`: optional pinned-only filter (`true`/`false`)

## Validate Workspace UI Behavior
1. Open `http://localhost:3000`.
2. Confirm editor text is visible immediately in the selected note without clicking into the canvas first.
3. Confirm the editor supports multiline content (paragraphs render as separate lines).
4. Right-click a note row in `Pinned` or `All notes`:
   - `Rename note` prompts and updates title.
   - `Pin note` / `Unpin note` moves notes between `Pinned` and `All notes`.
   - `Delete note` removes the note from the list.
5. Validate interaction quality:
   - Filter inputs auto-refresh list after a short debounce (no blur required).
   - `Shift+F10` on a focused note row opens the same context menu.
   - On API load failure, use `Retry` to re-fetch list content.

## Validate Backlinks + Title Conflict Guardrail (Epic E10)
1. Create target and source notes with explicit wiki-link references:
```bash
curl -sS -X PUT http://127.0.0.1:8000/v1/notes/backlink-target \
  -H 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{"note_id":"backlink-target","note_title":"Backlink Target","subject_id":"inbox","tags":[],"is_pinned":false,"is_archived":false,"content_json":{"type":"doc","content":[{"type":"paragraph","content":[{"type":"text","text":"Target note"}]}]},"content_text":"Target note","updated_at":"2026-03-13T13:00:00Z"}
JSON

curl -sS -X PUT http://127.0.0.1:8000/v1/notes/backlink-source-1 \
  -H 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{"note_id":"backlink-source-1","note_title":"Source One","subject_id":"inbox","tags":[],"is_pinned":false,"is_archived":false,"content_json":{"type":"doc","content":[{"type":"paragraph","content":[{"type":"text","text":"Reference [[Backlink Target]] from source"}]}]},"content_text":"Reference [[Backlink Target]] from source","updated_at":"2026-03-13T13:01:00Z"}
JSON
```
2. Query backlinks for the target:
```bash
curl -sS http://127.0.0.1:8000/v1/notes/backlink-target/backlinks
```
Expected:
- response includes `backlink-source-1` in `items`.
3. Validate duplicate-title conflict response:
```bash
curl -sS -X PUT http://127.0.0.1:8000/v1/notes/conflict-a \
  -H 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{"note_id":"conflict-a","note_title":"Duplicate Guard","subject_id":"inbox","tags":[],"is_pinned":false,"is_archived":false,"content_json":{"type":"doc","content":[{"type":"paragraph","content":[{"type":"text","text":"A"}]}]},"content_text":"A","updated_at":"2026-03-13T13:10:00Z"}
JSON

curl -sS -X PUT http://127.0.0.1:8000/v1/notes/conflict-b \
  -H 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{"note_id":"conflict-b","note_title":"Duplicate Guard","subject_id":"inbox","tags":[],"is_pinned":false,"is_archived":false,"content_json":{"type":"doc","content":[{"type":"paragraph","content":[{"type":"text","text":"B"}]}]},"content_text":"B","updated_at":"2026-03-13T13:11:00Z"}
JSON
```
Expected:
- second request returns `409` with `detail.code = "note_title_conflict"`.

## Validate Editor Command Surface (Epic E7)
1. Open any note editor in `http://localhost:3000`.
2. Use command buttons above the editor and confirm block transforms apply:
   - `Paragraph`, `H1`, `H2`, `H3`, `Bullet List`, `Numbered List`, `Checklist`, `Quote`, `Code Block`, `Divider`.
3. In the editor, type `/h1` and press `Enter`:
   - Slash menu appears and converts the current block to H1.
4. Press `Cmd+K` (macOS) or `Ctrl+K` (Windows/Linux):
   - Command palette opens, supports keyboard selection, and executes with `Enter`.
5. Type `[[` followed by part of a known note title:
   - Wiki-link suggestions appear.
6. Type `[[Some New Linked Note` and press `Enter`:
   - Quick-create option creates that note and inserts `[[Some New Linked Note]]` inline.
7. Click `Linked mentions` in the editor panel:
   - modal opens with loading/error/empty/data states.
   - pressing `Escape` closes the modal and restores focus to the trigger.

## Validate Block Hierarchy + Block References (Selective Nesting)
1. Confirm block tree API output after saving a note:
```bash
curl -sS http://127.0.0.1:8000/v1/notes/demo-note/blocks
```
Expected:
- each item includes `block_uid`, `parent_block_uid`, `sibling_order`, `block_index`.
2. Search block references by text:
```bash
curl -sS "http://127.0.0.1:8000/v1/blocks/search?q=graph&limit=10"
```
3. In the editor UI:
- create a bulleted list item and press `Tab` to indent, `Shift+Tab` to outdent.
- in headings/paragraphs, `Tab` nests the current block under the previous block and `Shift+Tab` outdents (Notion-style block hierarchy).
4. Insert a manual block reference:
- type `((` inside a note, choose a suggestion, and verify a readable clickable link is inserted.
5. Validate clickable references:
- clicking a `[[Note Title]]` reference navigates to the referenced note route.
- clicking a block reference navigates to the referenced note with block anchor hash.
6. Resolve block backlinks:
```bash
curl -sS http://127.0.0.1:8000/v1/blocks/<block_uid>/backlinks
```
Expected:
- `items` include source note/block and snippet where the token was used.

## Validate Math, Image, and Export Flow (Epic E8)
1. Save/update a note:
```bash
curl -sS -X PUT http://127.0.0.1:8000/v1/notes/demo-note \
  -H 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{"note_id":"demo-note","note_title":"Math + Image Demo","subject_id":"inbox","tags":[],"is_pinned":false,"is_archived":false,"content_json":{"type":"doc","content":[{"type":"paragraph","content":[{"type":"text","text":"Baseline content"}]}]},"content_text":"Baseline content","updated_at":"2026-03-13T12:00:00Z"}
JSON
```
2. Upload an image using JSON base64 payload:
```bash
B64=$(printf '\x89PNG\r\n\x1a\nabc' | base64)
curl -sS -X POST http://127.0.0.1:8000/v1/media/uploads \
  -H 'Content-Type: application/json' \
  --data-binary @- <<JSON
{"note_id":"demo-note","filename":"diagram.png","mime_type":"image/png","content_base64":"$B64"}
JSON
```
3. Use returned `asset_id` and `src` to save note content with math + image nodes:
```bash
curl -sS -X PUT http://127.0.0.1:8000/v1/notes/demo-note \
  -H 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{"note_id":"demo-note","note_title":"Math + Image Demo","subject_id":"inbox","tags":[],"is_pinned":false,"is_archived":false,"content_json":{"type":"doc","content":[{"type":"paragraph","content":[{"type":"text","text":"E="},{"type":"mathInline","attrs":{"latex":"mc^2"}}]},{"type":"mathBlock","attrs":{"latex":"x^2 + y^2"}},{"type":"image","attrs":{"src":"/v1/media/<asset_id>","assetId":"<asset_id>","alt":"diagram","filename":"<asset_id>.png"}}]},"content_text":"E=mc^2","updated_at":"2026-03-13T12:01:00Z"}
JSON
```
4. Export markdown zip and inspect output:
```bash
curl -sS http://127.0.0.1:8000/v1/notes/demo-note/export/markdown --output demo-note.zip
unzip -l demo-note.zip
unzip -p demo-note.zip note.md
```
Expected:
- archive contains `note.md` and `assets/<asset_id>.png`
- `note.md` contains inline math `$mc^2$`, block math `$$x^2 + y^2$$`, and relative image link `assets/<asset_id>.png`.

### E8 Migration Troubleshooting
If API logs show `relation "note_assets" does not exist`:
1. Apply latest migrations:
   - `make compose-migrate`
2. Retry the request.

Behavior before migration:
- note saves still work (media reconciliation safely no-ops),
- media upload/get/delete endpoints return migration-required errors until migration is applied.
