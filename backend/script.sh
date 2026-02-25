celery -A project worker --loglevel=info -Q analytics,maintenance,celery
docker run -d --name datacube-redis -p 6379:6379 redis:7-alpine

uvicorn project.asgi:application --reload --host 127.0.0.1 --port 8000

DJANGO_SETTINGS_MODULE=project.settings.development DJANGO_SETTINGS_MODULE=project.settings.development uvicorn project.asgi:application --reload --host 127.0.0.1 --port 8000