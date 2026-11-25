# AGENTS.md

Operational rules for AI coding agents working in **Rankit**.
Base structure adapted from Fabio Akita's *"Clean Code pra Agentes de IA"* (2026).

## Code style

- Functions: 4-20 lines. Split if longer.
- Files: under 500 lines. Split by responsibility.
- One thing per function, one responsibility per module (SRP).
- Names: specific and unique. Avoid `data`, `handler`, `Manager`.
  Prefer names that return <5 grep hits in the codebase.
- Types: explicit everywhere. No `any`, no untyped `dict`, no untyped functions.
- No code duplication. Extract shared logic into a function/module.
- Early returns over nested ifs. Max 2 levels of indentation.
- Exception messages must include the offending value and expected shape.

## Comments

- Keep your own comments. Don't strip them on refactor — they carry
  intent and provenance.
- Write WHY, not WHAT. Skip `// increment counter` above `i++`.
- Docstrings on public functions: intent + one usage example.
- Reference issue numbers / commit SHAs when a line exists because
  of a specific bug or upstream constraint.

## Tests

- Tests run with a single command:
  - Backend: `uv run pytest --cov=apps --cov-report=term-missing` (inside `backend/`)
  - Frontend: `npm run test:coverage` (inside `frontend/`)
  - E2E: `npx playwright test` (inside `e2e/` against running stack)
- Every new function gets a test. Bug fixes get a regression test.
- Mock external I/O (API, DB, filesystem) in unit tests with named fake classes,
  not inline stubs.
- Integration tests run against real PostgreSQL (never SQLite).
- Tests must be F.I.R.S.T: fast, independent, repeatable,
  self-validating, timely.

## Dependencies

- Inject dependencies through constructor/parameter, not global/import.
- Wrap third-party libs (TMDB, IGDB, Google Books, HTTP clients) behind a
  thin interface owned by this project.

## Structure

- Follow the framework's convention:
  - Backend: Django + DRF + SimpleJWT under `backend/config/` and `backend/apps/<domain>/`.
  - Frontend: Next.js App Router + TypeScript + SmoothUI under `frontend/src/`.
  - E2E: Playwright specs under `e2e/tests/`.
- Prefer small focused modules over god files.
- Predictable paths: `models.py`, `services.py`, `serializers.py`, `views.py`, `urls.py`, `tests/`.

## Formatting

- Use the language default formatter (`ruff format` / `ruff check` for Python,
  `prettier` + `eslint` for TypeScript/Next.js). Don't discuss style beyond that.

## Logging

- Structured JSON when logging for debugging / observability (Django `StructuredJsonLogFormatter`).
- Plain text only for user-facing CLI output.

## Git & Pull Request Workflow

- Never commit or push code directly to `main`.
- Always create a dedicated branch per feature/task (`feat/...`, `fix/...`, `chore/...`).
- Keep commits small, atomic, and formatted with Conventional Commits (`feat:`, `fix:`, `chore:`, `test:`, `docs:`, `ci:`).
- Always open a Pull Request and verify CI quality gates pass before merging.

## Coverage Ratchet Policy

- Minimum initial test coverage is **80%** (backend `fail_under` in `backend/pyproject.toml`,
  frontend `lines`/`functions`/`branches`/`statements` in `frontend/vitest.config.ts`).
- Coverage minimum must NEVER drop below 80%.
- Whenever achieved coverage exceeds the current minimum, update the minimum threshold
  to the new floored integer percentage in a dedicated commit before opening/updating the PR.

## Defensive Programming

- Set explicit timeouts on all outbound HTTP requests (TMDB, IGDB, Google Books).
- Use bounded retries with backoff only on idempotent reads.
- Provide deterministic local mock/fallback providers when external API keys are unset.
- Validate all incoming payloads with strict DRF serializers and TypeScript runtime guards.
- Store auth tokens in HttpOnly cookies; never expose JWT secrets or tokens in `localStorage`.

## Verification Commands

- Backend lint + typecheck + tests:
  `cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy config apps && uv run pytest --cov=apps --cov-report=term-missing`
- Frontend lint + typecheck + tests + build:
  `cd frontend && npm run lint && npm run typecheck && npm run test:coverage && npm run build`
- Coverage floor guard:
  `python scripts/verify_coverage_floors.py`
- Full stack Docker + E2E:
  `docker compose up -d --build --wait && cd e2e && npx playwright test`

## Clean Up

- Remove temporary files, `.coverage` artifacts outside git, and unused containers/volumes (`docker compose down -v`) after local verification.
