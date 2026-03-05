DJANGO_SETTINGS_MODULE=project.settings.development uvicorn project.asgi:application --reload --host 127.0.0.1 --port 8000

docker run -d -p 6379:6379 redis:7-alpine

docker run -d --name datacube-redis -p 6379:6379 redis:7-alpine
celery -A project worker --loglevel=info -Q analytics,maintenance,celery --pool=gevent

celery -A project worker --loglevel=info -Q analytics,maintenance,celery

celery -A project beat --loglevel=info


celery -A project worker --loglevel=info -Q analytics,maintenance,celery --pool=solo

pip install gevent

