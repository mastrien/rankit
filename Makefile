.PHONY: up down logs backend-lint backend-typecheck backend-test frontend-lint frontend-typecheck frontend-test e2e coverage-guard check-all

up:
	docker compose up -d --build --wait

down:
	docker compose down -v

logs:
	docker compose logs -f

backend-lint:
	cd backend && uv run ruff check . && uv run ruff format --check .

backend-typecheck:
	cd backend && uv run mypy config apps

backend-test:
	cd backend && uv run pytest --cov=apps --cov-report=term-missing

frontend-lint:
	cd frontend && npm run lint

frontend-typecheck:
	cd frontend && npm run typecheck

frontend-test:
	cd frontend && npm run test:coverage

e2e:
	cd e2e && npx playwright test

coverage-guard:
	python scripts/verify_coverage_floors.py

check-all: backend-lint backend-typecheck backend-test frontend-lint frontend-typecheck frontend-test coverage-guard
