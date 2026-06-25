# Datacube V2 — local development shortcuts
# Run `make` or `make help` for targets.

SHELL := /bin/bash
.DEFAULT_GOAL := help

BACKEND_DIR   := backend
UI_DIR        := UI/datacube-UI
COMPOSE_DEV   := docker-compose.dev_enhanced.yml
UV            := uv
NPM           := npm

# Match backend/.env.example defaults for native dev / tests
export SECRET_KEY              ?= dev-insecure-key
export MONGODB_URI             ?= mongodb://127.0.0.1:27017
export MONGODB_DATABASE        ?= datacube_metadata
export MONGODB_COLLECTION      ?= metadata
export AUTH_DB_NAME            ?= datacube_auth
export FILE_STORAGE_DB_NAME    ?= datacube_files
export DJANGO_SETTINGS_MODULE  ?= project.settings.development

.PHONY: help setup install env backend-sync backend-migrate backend-run backend-shell \
        backend-check backend-collectstatic ui-install ui-dev ui-build \
        test test-ci docker-up docker-down docker-build docker-logs docker-ps \
        celery dev-backend dev-ui clean

help: ## Show this help
	@grep -E '^[a-zA-Z0-9_.-]+:.*##' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

setup: env backend-sync backend-migrate ui-install ## First-time setup (env, deps, migrate, npm)
	@echo "Setup complete. Try: make dev-backend  (and in another terminal) make dev-ui"

install: setup ## Alias for setup

env: ## Copy backend/.env.example → backend/.env if missing
	@if [ ! -f $(BACKEND_DIR)/.env ]; then \
		cp $(BACKEND_DIR)/.env.example $(BACKEND_DIR)/.env; \
		echo "Created $(BACKEND_DIR)/.env — edit MongoDB and secrets before running."; \
	else \
		echo "$(BACKEND_DIR)/.env already exists."; \
	fi

backend-sync: ## uv sync (backend dependencies)
	cd $(BACKEND_DIR) && $(UV) sync

backend-migrate: ## Django migrate (SQLite + Django tables)
	cd $(BACKEND_DIR) && $(UV) run python manage.py migrate

backend-run: ## Run Django dev server on :8000
	cd $(BACKEND_DIR) && $(UV) run python manage.py runserver 0.0.0.0:8000

backend-shell: ## Django shell
	cd $(BACKEND_DIR) && $(UV) run python manage.py shell

backend-check: ## Django system check
	cd $(BACKEND_DIR) && $(UV) run python manage.py check

backend-collectstatic: ## Collect admin static files into backend/staticfiles/
	cd $(BACKEND_DIR) && $(UV) run python manage.py collectstatic --noinput

ui-install: ## npm install (frontend)
	cd $(UI_DIR) && $(NPM) install

ui-dev: ## Vite dev server (default :5173)
	cd $(UI_DIR) && $(NPM) run dev

ui-build: ## Production frontend build
	cd $(UI_DIR) && $(NPM) run build

dev-backend: backend-run ## Alias: Django on :8000

dev-ui: ui-dev ## Alias: Vite dev server

celery: ## Celery worker (requires Redis on :6379)
	cd $(BACKEND_DIR) && $(UV) run celery -A project worker -Q analytics,maintenance -l info

test: ## Run backend pytest (api + analytics)
	cd $(BACKEND_DIR) && $(UV) run pytest api/tests analytics/tests -q

test-ci: ## Run the same checks as GitHub Actions CI
	cd $(BACKEND_DIR) && $(UV) sync --frozen --all-groups
	cd $(BACKEND_DIR) && $(UV) run pytest
	cd $(BACKEND_DIR) && $(UV) run python manage.py check

docker-up: ## Full stack via Docker (redis, backend, celery, nginx, react-app)
	docker compose -f $(COMPOSE_DEV) up --build

docker-down: ## Stop Docker dev stack
	docker compose -f $(COMPOSE_DEV) down

docker-build: ## Build Docker dev images without starting
	docker compose -f $(COMPOSE_DEV) build

docker-logs: ## Follow Docker dev logs
	docker compose -f $(COMPOSE_DEV) logs -f

docker-ps: ## Show Docker dev service status
	docker compose -f $(COMPOSE_DEV) ps

clean: ## Remove Python caches and frontend build output
	find $(BACKEND_DIR) -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	rm -rf $(UI_DIR)/dist
