.PHONY: help setup backend-install backend-test backend-run frontend-install frontend-test frontend-build up down migrate

help:
	@echo "CNI Group Governance Portal — dev tasks"
	@echo "  make setup            install backend + frontend deps"
	@echo "  make up / down        start / stop postgres + redis (docker compose)"
	@echo "  make migrate          run Django migrations"
	@echo "  make backend-test     pytest"
	@echo "  make backend-run      run API on 127.0.0.1:8000"
	@echo "  make frontend-test    vitest"
	@echo "  make frontend-build   production build"

setup: backend-install frontend-install

backend-install:
	cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

backend-test:
	cd backend && . .venv/bin/activate && pytest

backend-run:
	cd backend && . .venv/bin/activate && python manage.py runserver 127.0.0.1:8000

migrate:
	cd backend && . .venv/bin/activate && python manage.py migrate

frontend-install:
	cd frontend && npm install

frontend-test:
	cd frontend && npm test

frontend-build:
	cd frontend && npm run build

up:
	docker compose up -d

down:
	docker compose down
