.PHONY: up down build test lint migrate seed logs

up:
	docker compose up -d --build

down:
	docker compose down

build:
	pip install -e ".[dev]"

test:
	pytest -v

lint:
	ruff check .
	ruff format --check .

migrate:
	alembic upgrade head

seed:
	@echo "Set API_KEY_SEED env var and restart the API service"
	@echo "docker compose up -d api"

logs:
	docker compose logs -f
