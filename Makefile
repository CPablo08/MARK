.PHONY: dev install env-sync api worker ui docker-up docker-down migrate start stop

start:
	@./scripts/start.sh --open

stop:
	@./scripts/stop.sh

install:
	pnpm install
	cd backend && pip3 install -e .
	@$(MAKE) playwright-install

playwright-install:
	cd backend && pip3 install playwright && playwright install chromium

env-sync:
	@test -f .env || (echo "Copy .env.example to .env first" && exit 1)
	cp .env backend/.env
	@grep -q VITE_API_URL apps/desktop/.env 2>/dev/null || echo "VITE_API_URL=http://127.0.0.1:8000" > apps/desktop/.env

docker-up:
	docker compose -f docker/docker-compose.yml up -d postgres redis qdrant

docker-down:
	docker compose -f docker/docker-compose.yml down

migrate:
	cd backend && alembic -c alembic.ini upgrade head

api: env-sync
	cd backend && PYTHONPATH=. python3 -m uvicorn mark_api.main:app --reload --host 127.0.0.1 --port 8000

worker: env-sync
	cd backend && PYTHONPATH=. python3 -m mark_core.worker

ui:
	pnpm dev

dev: env-sync
	@echo "Quick start: make start   (or ./scripts/start.sh)"
	@echo "Manual:      make api  +  make ui  (separate terminals)"
