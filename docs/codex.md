# Codex Project Instructions
1. You are a senior software engineer
2. This project uses `uv` and a uv virtual environment for this environment.
3. Come up with a plan for the desired task using SOLID principles, document that plan in a temporary file.
4. Always create the project structure first, then write test cases for all viable scenarios, and only then implement the logic. Document everything in that temporary file.
5. Always run tests against the written test cases after implementation.
6. Always write neat slop-free/minimal but descriptive comments and docs for everything we do.
7. After any code changes always scan for deadcode and do cleanup
8. Make sure what we implemented aligns with the plan.
9. Update codebase relevant documentation.
10. Delete temporary file
11. For bugs always prioritise permanent fixes and NOT quick fixes
12. For UI/UX work, define explicit acceptance criteria in the temp plan (interaction, loading, error, keyboard,
  accessibility).
13. For frontend behavior changes, write/adjust tests first for all user-visible scenarios, then implement.
14. Every destructive action must have both mouse and keyboard access parity.
15. Do not rely on `onBlur` as the only trigger for critical UX flows (filters, saves, actions).
16. Use a consistent visual system (tokens/variables, spacing scale, typography scale); avoid ad-hoc styling.
17. Frontend validation gate is mandatory: `npm --prefix web run typecheck` and web tests (use compose runtime if
local toolchain is unstable).
18. When local runtime is platform-broken, use Docker Compose as canonical validation path and document it in `docs/
decisions.md`.