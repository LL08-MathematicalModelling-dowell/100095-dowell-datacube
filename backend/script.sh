celery -A project worker --loglevel=info -Q analytics,maintenance,celery
docker run -d --name datacube-redis -p 6379:6379 redis:7-alpine

uvicorn project.asgi:application --reload --host 127.0.0.1 --port 8000

DJANGO_SETTINGS_MODULE=project.settings.development uvicorn project.asgi:application --reload --host 127.0.0.1 --port 8000

pip install pytest pytest-django pytest-asyncio pytest-mock

pytest tests/test_analytics_views.py -v

pytest tests/test_analytics_api.py -v

pytest api/tests/test_gridfs_service.py -v

# In your setup script using the async client:
async def setup_indexes():
    db = settings.MONGODB_CLIENT[settings.FILE_STORAGE_DB_NAME]
    # Index for fast lookup of a specific user's files
    await db["user_files.files"].create_index([("metadata.user_id", 1), ("uploadDate", -1)])

# The GridFS 'files' collection in your shared database
db["user_storage.files"].create_index([("metadata.user_id", 1)])