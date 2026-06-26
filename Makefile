# Datacube V2 — local development shortcuts
# Run `make` or `make help` for targets.

SHELL := /bin/bash
.DEFAULT_GOAL := help

# ====================== Variables ======================
BACKEND_DIR   := backend
UI_DIR        := UI/datacube-UI
COMPOSE_DEV   := docker-compose.dev_enhanced.yml

UV            := uv
NPM           := npm

# Environment defaults
export SECRET_KEY              ?= dev-insecure-key
export MONGODB_URI             ?= mongodb://127.0.0.1:27017
export MONGODB_DATABASE        ?= datacube_metadata
export MONGODB_COLLECTION      ?= metadata
export AUTH_DB_NAME            ?= datacube_auth
export FILE_STORAGE_DB_NAME    ?= datacube_files
export DJANGO_SETTINGS_MODULE  ?= project.settings.development

# ====================== Phony Targets ======================
.PHONY: help setup install env backend-sync backend-migrate backend-run \
        backend-shell backend-check backend-collectstatic \
        ui-install ui-dev ui-build \
        dev dev-all dev-backend dev-ui dev-redis dev-redis-down \
        restart restart-backend restart-redis \
        celery test test-ci \
        docker-up docker-down docker-build docker-logs docker-ps \
        clean

# ====================== Help ======================
help: ## Show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ====================== Setup ======================
setup: env backend-sync backend-migrate ui-install ## First-time setup
	@echo "✅ Setup complete!"
	@echo ""
	@echo "Quick start options:"
	@echo "   make dev-all          # Redis + Backend + UI"
	@echo "   make dev              # Redis + Backend only"
	@echo "   make celery           # Celery worker (in separate terminal)"

install: setup ## Alias for setup

env: ## Copy .env.example → .env if missing
	@if [ ! -f $(BACKEND_DIR)/.env ]; then \
		cp $(BACKEND_DIR)/.env.example $(BACKEND_DIR)/.env; \
		echo "✅ Created $(BACKEND_DIR)/.env"; \
	else \
		echo "ℹ️  $(BACKEND_DIR)/.env already exists"; \
	fi

# ====================== Backend ======================
backend-sync: ## Sync backend dependencies with uv
	cd $(BACKEND_DIR) && $(UV) sync

backend-migrate: ## Run Django migrations
	cd $(BACKEND_DIR) && $(UV) run python manage.py migrate

backend-run: ## Run Django development server (uvicorn)
	cd $(BACKEND_DIR) && \
		$(UV) run uvicorn project.asgi:application \
			--reload \
			--host 0.0.0.0 \
			--port 8000 \
			--workers 4 \
			--log-level info

backend-shell: ## Open Django shell
	cd $(BACKEND_DIR) && $(UV) run python manage.py shell

backend-check: ## Run Django system checks
	cd $(BACKEND_DIR) && $(UV) run python manage.py check

backend-collectstatic: ## Collect static files
	cd $(BACKEND_DIR) && $(UV) run python manage.py collectstatic --noinput

# ====================== Frontend ======================
ui-install: ## Install frontend dependencies
	cd $(UI_DIR) && $(NPM) install

ui-dev: ## Start Vite dev server
	cd $(UI_DIR) && $(NPM) run dev

ui-build: ## Build frontend for production
	cd $(UI_DIR) && $(NPM) run build

# ====================== Development ======================
dev-redis: ## Ensure Redis is running
	@echo "Ensuring dev-redis is running..."
	@docker start dev-redis 2>/dev/null || \
		docker run -d \
			--name dev-redis \
			-p 6379:6379 \
			--restart unless-stopped \
			redis:7-alpine >/dev/null && \
		echo "✅ dev-redis started"

dev-redis-down: ## Stop and remove dev-redis
	@docker stop dev-redis 2>/dev/null || true
	@docker rm -f dev-redis 2>/dev/null || true
	@echo "✅ dev-redis stopped and removed"

dev-backend: backend-run ## Start backend only

dev-ui: ui-dev ## Start frontend only

dev: dev-redis ## Start Redis + Backend
	@echo "🚀 Starting development environment (Redis + Backend)..."
	@echo "→ Frontend: Run 'make dev-ui' in another terminal"
	@$(MAKE) --no-print-directory dev-backend

dev-all: dev-redis ## Start full web stack: Redis + Backend + UI
	@echo "🚀 Starting full development stack..."
	@echo "Backend  → http://localhost:8000"
	@echo "Frontend → http://localhost:5173"
	@echo "Celery   → Run 'make celery' in another terminal if needed"
	@$(MAKE) -j2 --no-print-directory dev-backend dev-ui

# ====================== Restart ======================
restart-redis: ## Restart only Redis
	@echo "Restarting dev-redis..."
	@$(MAKE) --no-print-directory dev-redis-down
	@$(MAKE) --no-print-directory dev-redis

restart-backend: ## Restart only backend
	@echo "Restarting backend..."
	@pkill -f "uvicorn project.asgi" 2>/dev/null || true
	@$(MAKE) --no-print-directory dev-backend

restart: restart-redis restart-backend ## Restart Redis + Backend

# ====================== Celery ======================
celery: dev-redis ## Start Celery worker (recommended in separate terminal)
	cd $(BACKEND_DIR) && $(UV) run celery -A project worker -Q analytics,maintenance -l info

# ====================== Testing ======================
test: ## Run tests (quiet)
	cd $(BACKEND_DIR) && $(UV) run pytest api/tests analytics/tests -q

test-ci: ## Run full CI checks
	cd $(BACKEND_DIR) && $(UV) sync --frozen --all-groups
	cd $(BACKEND_DIR) && $(UV) run pytest
	cd $(BACKEND_DIR) && $(UV) run python manage.py check

# ====================== Docker ======================
docker-up: ## Start full stack with docker-compose
	docker compose -f $(COMPOSE_DEV) up --build

docker-down: ## Stop full Docker stack
	docker compose -f $(COMPOSE_DEV) down

docker-build: ## Build Docker images
	docker compose -f $(COMPOSE_DEV) build

docker-logs: ## Follow Docker logs
	docker compose -f $(COMPOSE_DEV) logs -f

docker-ps: ## Show Docker services status
	docker compose -f $(COMPOSE_DEV) ps

# ====================== Maintenance ======================
clean: ## Clean caches and build artifacts
	find $(BACKEND_DIR) -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf $(UI_DIR)/dist
	@echo "✅ Clean completed"