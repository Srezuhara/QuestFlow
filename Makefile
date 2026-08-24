.PHONY: up down migrate seed seed-clean test test-db test-backend test-frontend lint lint-backend lint-frontend \
	backend-venv backend-run backend-test backend-lint \
	frontend-install frontend-run frontend-test frontend-lint \
	e2e e2e-clean

# --- Docker Compose (postgres + api + worker + web) ---

up:
	docker compose up --build

down:
	docker compose down

migrate:
	docker compose exec api uv run alembic upgrade head

seed:
	docker compose exec api uv run python -m app.db.seed

# Removes only seeded rows (demo user + leaderboard filler users), never a
# blind truncate — this is the dev database. Cascades handle the rest.
seed-clean:
	docker compose exec postgres psql -U questflow -d questflow \
		-c "DELETE FROM users WHERE email = 'demo@example.com' OR email LIKE 'seed_user%@example.com';"

# Creates (idempotently) and migrates the dedicated pytest database. Must be
# re-run after every new Alembic revision, or the test DB drifts from dev.
test-db:
	docker compose exec postgres psql -U questflow -d questflow -c "CREATE DATABASE questflow_test OWNER questflow;" || true
	docker compose exec -e DATABASE_URL=postgresql+asyncpg://questflow:questflow_dev_password@postgres:5432/questflow_test api uv run alembic upgrade head

test: test-backend test-frontend

test-backend: test-db
	docker compose exec api uv run pytest

test-frontend:
	docker compose exec web npm run test

lint: lint-backend lint-frontend

lint-backend:
	docker compose exec api uv run ruff check .
	docker compose exec api uv run mypy .

lint-frontend:
	docker compose exec web npm run lint
	docker compose exec web npm run typecheck

# --- Native (no Docker) ---
# Requires postgres reachable at the DATABASE_URL in backend/.env (or a
# local Postgres install) for anything beyond /health.

backend-venv:
	cd backend && uv sync --dev

backend-run:
	cd backend && uv run uvicorn app.main:app --reload

backend-test: test-db
	cd backend && uv run pytest

backend-lint:
	cd backend && uv run ruff check .
	cd backend && uv run mypy .

frontend-install:
	cd frontend && npm install

frontend-run:
	cd frontend && npm run dev

frontend-test:
	cd frontend && npm run test

frontend-lint:
	cd frontend && npm run lint
	cd frontend && npm run typecheck

# --- Playwright e2e (host-only, drives the running Docker stack) ---

e2e:
	cd frontend && npx playwright test

# Belt-and-braces for a crash mid-run. Per-test teardown (DELETE /auth/me)
# is the primary cleanup mechanism — see e2e/fixtures.ts.
e2e-clean:
	docker compose exec postgres psql -U questflow -d questflow \
		-c "DELETE FROM users WHERE email LIKE 'e2e+%@example.com';"
