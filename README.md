# QuestFlow

A gamified productivity app — tasks, habits, notes, and a focus timer, all feeding a single
XP/leveling engine. UI follows the "Neon Syndicate" cyberpunk design system.

Design mockups and the canonical token spec live in [`design/`](design/), with
[`design/neon_syndicate/DESIGN.md`](design/neon_syndicate/DESIGN.md) as the source of truth for
colors, typography, and spacing.

## Stack

- **Backend** — FastAPI + Postgres 16 + SQLAlchemy 2.0 (async) + Alembic + Pydantic v2, managed
  with [uv](https://github.com/astral-sh/uv). Strict `mypy` + `ruff`.
- **Frontend** — Vite + React 19 + TypeScript, Tailwind v4 (CSS-first `@theme`), TanStack Query +
  Zustand, React Router, `openapi-typescript` for generated API types. ESLint + Prettier + strict
  `tsc`.
- **Gamification** — append-only XP ledger, level curve, streaks, skill tree, achievements (see
  the plan, §3).
- **Environment** — Docker Compose: `postgres`, `api`, `worker` (APScheduler, stubbed until phase
  7), `web`.

## Running it

```bash
cp .env.example .env
make up             # postgres + api + worker + web (docker compose up)
make migrate         # alembic upgrade head
make seed             # (stub for now — real seed data lands in a later phase)
```

- API: http://localhost:8000 — health check at `/health`, interactive docs at `/docs`
- Web: http://localhost:5173

Other targets: `make down`, `make test` (backend pytest + frontend vitest), `make lint` (ruff +
mypy + eslint + tsc).

## Run locally without Docker

Both halves also run natively — useful for a faster inner loop than rebuilding containers.
Postgres itself still needs to be reachable somewhere (either `docker compose up postgres` on its
own, or a local install) for anything beyond `/health`.

**Backend** (needs [uv](https://github.com/astral-sh/uv); `pip install uv` if you don't have it):

```powershell
cd backend
uv sync --dev                              # creates backend\.venv and installs deps
backend\.venv\Scripts\Activate.ps1         # Windows PowerShell activation
uv run uvicorn app.main:app --reload       # or: uvicorn app.main:app --reload (once activated)
```

API comes up at http://localhost:8000/health. Equivalent Makefile shortcuts: `make backend-venv`,
`make backend-run`, `make backend-test`, `make backend-lint`.

**Frontend** (needs Node 22+):

```powershell
cd frontend
npm install
npm run dev
```

Dev server comes up at http://localhost:5173. Equivalent Makefile shortcuts:
`make frontend-install`, `make frontend-run`, `make frontend-test`, `make frontend-lint`.

## Repository layout

```
docker-compose.yml
Makefile
.env.example
backend/            # FastAPI app (see backend/app/)
frontend/           # Vite + React app (see frontend/src/)
design/             # Stitch mockups (code.html + screen.png) + DESIGN.md token spec
```

## Status

Built in phases. **Phases 0–2 are complete and verified** against the running stack:

- **0 — Scaffold**: Docker Compose (`postgres`/`api`/`worker`/`web`), both toolchains, CI-grade lint/type config.
- **1 — Auth & shell**: email+password (argon2id), JWT access tokens and opaque refresh tokens in
  httpOnly cookies, refresh rotation with reuse detection, the `components/ui` Neon Syndicate kit,
  and the responsive `AppShell`.
- **2 — Tasks & XP engine**: projects/tags/tasks with subtasks, the append-only `xp_events` ledger
  plus its `user_progress` projection, the level curve, and the Command Center dashboard with
  optimistic task completion.

Next: **phase 3 (Habits)** — streak math, the 30-day matrix, and the Habit Master page.

Quality gates on `main`: backend `ruff` + `mypy --strict` + 32 `pytest` tests; frontend `tsc`
+ `eslint` + `prettier` + `vitest`. All green.
