# NeuroNote Epic Release Checklist

Use this checklist at the end of **every** epic.  
Run gates in order. Do not skip or reorder gates after a failure.

## Rules
- Compose-first workflow is mandatory.
- UI/manual verification is mandatory for every epic.
- No manual JSON typing in shell; use heredoc payloads.
- A gate failure blocks release.

## 1) Preflight
### Commands
```bash
git status --short
docker info >/dev/null
```

### Pass
- Working tree state is known.
- Docker daemon is reachable.

### Fail
- Docker unavailable.

### Retry
- Start Docker Desktop and rerun this gate.

## 2) Runtime Bring-up
### Commands
```bash
make compose-down
make compose-up
make compose-migrate
make compose-bootstrap-extensions
```

### Pass
- `db`, `api`, `web` services are up.
- Migration command exits successfully.

### Fail
- Any compose or migration command exits non-zero.

### Retry
- If schema is inconsistent, run `make compose-down` and `make compose-up` again, then rerun migrations.

## 3) Static Quality Gate
### Commands
```bash
make compose-check
cd web && npm run lint && npm run typecheck
```

### Pass
- `ruff`, `mypy`, TypeScript, and lint all pass.

### Fail
- Any static check fails.

### Retry
- Fix the reported issues and rerun this gate.

## 4) Automated Test Gate
### Commands
```bash
make compose-test
make compose-test-db
```

### Pass
- Integration/unit suites pass.
- DB extension/graph-vector tests pass.

### Fail
- Any test failure or crash.

### Retry
- Fix failures, rerun failing target, then rerun full gate.

## 5) API + Processing Smoke Gate
### Commands
```bash
curl -sS http://127.0.0.1:8000/health

curl -sS -X PUT http://127.0.0.1:8000/v1/notes/release-smoke-note \
  -H 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{"note_id":"release-smoke-note","note_title":"Release Smoke Note","subject_id":"inbox","tags":["release"],"is_pinned":false,"is_archived":false,"content_json":{"type":"doc","content":[{"type":"paragraph","content":[{"type":"text","text":"Machine Learning links to [[Release Neighbor]]"}]}]},"content_text":"Machine Learning links to [[Release Neighbor]]","updated_at":"2026-03-17T12:00:00Z"}
JSON

HASH=$(printf 'Release Smoke Note\n\nMachine Learning links to [[Release Neighbor]]' | shasum -a 256 | awk '{print $1}')
curl -sS -X POST http://127.0.0.1:8000/v1/process-note \
  -H 'Content-Type: application/json' \
  -d "{\"note_id\":\"release-smoke-note\",\"content_text\":\"Release Smoke Note\\n\\nMachine Learning links to [[Release Neighbor]]\",\"content_hash\":\"$HASH\",\"updated_at\":\"2026-03-17T12:00:00Z\"}"
```

Then poll:
```bash
curl -sS http://127.0.0.1:8000/v1/process-status/<job_id>
curl -sS "http://127.0.0.1:8000/v1/graph/local/release-smoke-note?max_hops=1&limit_nodes=80&min_confidence=0&include_types=note,entity,relation"
```

### Pass
- `/health` returns `{"status":"ok"}`.
- Process job reaches `completed`.
- Local graph endpoint returns `200` and valid payload.

### Fail
- Any `500`, failed process job, or invalid graph payload.

### Retry
- Check logs gate, fix root cause, rerun this gate.

## 6) UI/UX Manual Gate (Required)
### Steps
1. Open `http://localhost:3000`.
2. Create note, rename note, pin/unpin note, delete note (mouse and keyboard where applicable).
3. Confirm pinned section behavior and no duplicate note rows.
4. In editor:
   - Slash command executes on `Enter`.
   - `[[note refs]]` autocomplete and navigation works.
   - `((block refs))` insertion and navigation works.
   - Selective nesting (`Tab` / `Shift+Tab`) behaves correctly.
5. Confirm no runtime errors in browser (especially React hook-order errors).

### Pass
- All listed interactions work end-to-end.
- No critical UI/runtime regression.

### Fail
- Broken UX flow, navigation mismatch, or runtime crash.

### Retry
- Fix issue, refresh app, rerun full UI gate.

## 7) Observability / Logs Gate
### Commands
```bash
make compose-logs
```

### Pass
- No repeated critical errors:
  - missing table/relation errors,
  - transaction lifecycle errors,
  - uniqueness floods from deterministic IDs,
  - repeated 500s for touched endpoints.

### Fail
- Any recurring critical backend/db/runtime error.

### Retry
- Fix cause, restart affected service if needed, rerun affected gates.

## 8) Docs + Dead-Code Gate
### Checklist
- Architecture changes captured in `docs/plan.md`.
- Non-architecture implementation notes captured in `docs/decisions.md`.
- No dead/redundant code introduced by the epic.
- User-facing run/test instructions still match current commands.

### Pass
- Docs and codebase are aligned with shipped behavior.

### Fail
- Missing docs updates or dead code remains.

### Retry
- Update docs/cleanup and re-verify.

## 9) Final Sign-off Record
Copy this block into PR description or release notes:

```md
Release checklist sign-off
- Date:
- Epic:
- Commit SHA:
- Runtime: compose
- Gate 1 Preflight: PASS/FAIL
- Gate 2 Bring-up: PASS/FAIL
- Gate 3 Static quality: PASS/FAIL
- Gate 4 Automated tests: PASS/FAIL
- Gate 5 API smoke: PASS/FAIL
- Gate 6 UI/UX manual: PASS/FAIL
- Gate 7 Logs/observability: PASS/FAIL
- Gate 8 Docs/dead-code: PASS/FAIL
- Known risks/deferred items: none
```

Release is complete only when all gates are `PASS`.
