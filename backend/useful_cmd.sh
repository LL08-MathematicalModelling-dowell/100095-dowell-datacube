DJANGO_SETTINGS_MODULE=project.settings.development uvicorn project.asgi:application --reload --host 127.0.0.1 --port 8000
DJANGO_SETTINGS_MODULE=project.settings.production uvicorn project.asgi:application --reload --host 127.0.0.1 --port 8000


docker run -d --name datacube-redis -p 6379:6379 redis:7-alpine
DJANGO_SETTINGS_MODULE=project.settings.development celery -A project worker --loglevel=info -Q analytics,maintenance,celery --pool=gevent

celery -A project worker --loglevel=info -Q analytics,maintenance,celery

celery -A project beat --loglevel=info


DJANGO_SETTINGS_MODULE=project.settings.development celery -A project worker --loglevel=info -Q analytics,maintenance,celery --pool=solo

pip install gevent

# Check health status of the backend container
docker inspect --format='{{json .State.Health}}' bb81fa2b578c
docker inspect --format='{{json .State.Health}}' datacube-backend