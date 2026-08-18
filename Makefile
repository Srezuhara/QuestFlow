.PHONY: up down migrate seed test test-backend test-frontend lint lint-backend lint-frontend \
	backend-venv backend-run backend-test backend-lint \
	frontend-install frontend-run frontend-test frontend-lint

# --- Docker Compose (postgres + api + worker + web) ---

up:
	docker compose up --build

down:
	docker compose down

migrate:
	docker compose exec api uv run alembic upgrade head

seed:
	@echo "not implemented yet"

test: test-backend test-frontend

test-backend:
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

backend-test:
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
