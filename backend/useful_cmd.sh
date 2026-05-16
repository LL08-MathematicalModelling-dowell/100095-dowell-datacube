DJANGO_SETTINGS_MODULE=project.settings.development uvicorn project.asgi:application --reload --host 127.0.0.1 --port 8000

DJANGO_SETTINGS_MODULE=project.settings.production uvicorn project.asgi:application --reload --host 127.0.0.1 --port 8000


docker run -d --name datacube-redis -p 6379:6379 redis:7-alpine


DJANGO_SETTINGS_MODULE=project.settings.development celery -A project worker -Q analytics,maintenance -l info

docker compose -f docker-compose.prod_enhanced.yml up -d

# uv add gevent   # already in pyproject; use: uv sync

# Check health status of the backend container
docker inspect --format='{{json .State.Health}}' bb81fa2b578c
docker inspect --format='{{json .State.Health}}' datacube-backend

cd backend
uv sync                 # app + dev tools
uv run python manage.py runserver
uv run pytest ...
uv sync --no-dev        # production-like (matches Docker)

uv run pytest api/tests analytics/tests

uv run pytest api/tests analytics/tests