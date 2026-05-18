# Datacube backend — handy commands (run from `backend/`)
# Requires: https://github.com/astral-sh/uv

# --- Setup ---
cd backend
uv sync --all-groups          # app + dev/test deps
# uv sync --frozen --all-groups # CI-style (exact lockfile)
# uv sync --no-dev              # production-like (matches Docker)

# --- Django dev server ---
export DJANGO_SETTINGS_MODULE=project.settings.development uv run python manage.py runserver 127.0.0.1:8000
# uv run python manage.py check
# uv run python manage.py migrate

# --- ASGI (uvicorn) ---
export DJANGO_SETTINGS_MODULE=project.settings.development uv run uvicorn project.asgi:application --reload --host 127.0.0.1 --port 8000

# export DJANGO_SETTINGS_MODULE=project.settings.production
# uv run uvicorn project.asgi:application --reload --host 127.0.0.1 --port 8000

# --- Celery (needs Redis) ---
export DJANGO_SETTINGS_MODULE=project.settings.development uv run celery -A project worker -Q analytics,maintenance -l info

# --- Tests ---
export DJANGO_SETTINGS_MODULE=project.settings.development
uv run pytest
uv run pytest api/tests analytics/tests
uv run python manage.py check

# --- Redis (local, for Celery) ---
docker run -d --name datacube-redis -p 6379:6379 redis:7-alpine

# --- Docker (production stack) ---
# docker compose -f docker-compose.prod_enhanced.yml up -d
# docker compose -f docker-compose.prod_enhanced.yml build

# --- Container health ---
# docker inspect --format='{{json .State.Health}}' datacube-backend

DJANGO_SETTINGS_MODULE=project.settings.development uv run uvicorn project.asgi:application --reload --host 127.0.0.1 --port 8000

DJANGO_SETTINGS_MODULE=project.settings.development uv run celery -A project worker -Q analytics,maintenance -l info

