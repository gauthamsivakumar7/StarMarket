.PHONY: up down migrate seed run test frontend-install frontend-dev frontend-build

up:
	docker compose up -d

down:
	docker compose down

migrate:
	alembic upgrade head

seed:
	python scripts/seed.py

run:
	uvicorn app.main:app --reload

test:
	pytest tests/ -v

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build
