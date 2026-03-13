# Codex Internal Improvement Protocol (NeuroNote)

Date: 2026-03-12
Audience: Codex only

## Non-Negotiable Execution Order
1. Read `docs/codex.md` and `docs/plan.md` before implementation.
2. Create or confirm structure first.
3. Write/extend tests for viable scenarios.
4. Implement logic only after tests exist.
5. Run relevant checks/tests.
6. Remove dead code immediately.
7. Update docs (`plan.md` for architecture, `decisions.md` for non-plan notes).

## How I Failed Before (Do Not Repeat)
- Allowed local environment variance to consume time before switching to stable compose workflow.
- Relied on manual `curl` payload typing; this produced JSON false negatives.
- Missed schema-qualification risk under AGE search path behavior.
- Let temporary operational confusion linger instead of codifying repeatable commands.

## Hard Rules Going Forward
- Prefer permanent fixes; reject tactical patches unless explicitly requested as temporary.
- Treat `docker compose` + `uv` as default execution path for run/check/test unless user asks otherwise.
- For PostgreSQL + AGE: always schema-qualify non-graph SQL tables (`public.*`) in repository code.
- Keep Alembic migration-first ownership for Postgres; do not reintroduce runtime schema auto-create behavior.
- Use explicit transaction boundaries for multi-step DB workflows.
- Base dedupe/coalescing identity on persisted server state, not client assumptions.

## Operational Discipline
- If a command is error-prone when typed manually, provide a copy-safe one-liner or Make target.
- Validate with both static and behavioral checks for touched areas.
- If behavior changes architecture, update `docs/plan.md` in the same task.
- If behavior does not change architecture, log in `docs/decisions.md`.

## Quality Gate Before Declaring Done
- Tests for new behavior exist and pass.
- No orphaned/unused code introduced by the change.
- Docs for run/test/validation paths are current.
- Manual validation steps are deterministic and shell-safe.
