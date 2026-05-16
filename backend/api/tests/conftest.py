import pytest
from bson import ObjectId
from unittest.mock import AsyncMock, MagicMock
from types import SimpleNamespace
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def api_user_id():
    """Valid ObjectId string for paths that cast user id to ObjectId."""
    return str(ObjectId())


@pytest.fixture
def api_user(api_user_id):
    """Minimal user for DRF force_authenticate (Mongo views use user.pk and role for RBAC)."""
    return SimpleNamespace(pk=api_user_id, id=api_user_id, is_authenticated=True, role="developer")


@pytest.fixture
def authenticated_api_client(api_client, api_user):
    api_client.force_authenticate(user=api_user)
    return api_client


@pytest.fixture
def database_with_collections(mock_metadata_collection):
    db_id = str(ObjectId())
    mock_metadata_collection.find_one.return_value = {
        "_id": ObjectId(db_id),
        "database_name": "test_database",
        "collections": [
            {"name": "users", "fields": [{"name": "username", "type": "string"}]},
            {"name": "products", "fields": [{"name": "product_name", "type": "string"}]},
        ],
    }
    return {
        "database_id": db_id,
        "database_name": "test_database",
        "collections": ["users", "products"],
    }


@pytest.fixture
def user_id():
    return str(ObjectId())


@pytest.fixture
def db_id():
    return str(ObjectId())


@pytest.fixture
def file_id():
    return str(ObjectId())


@pytest.fixture
def mock_mongo_client(mocker):
    """Mock the MongoDB client and its collections."""
    mock_client = AsyncMock()
    mock_client.__getitem__ = MagicMock(return_value=AsyncMock())
    mocker.patch("django.conf.settings.MONGODB_CLIENT", mock_client)
    return mock_client


@pytest.fixture
def mock_metadata_collection(mocker):
    """Mock the metadata collection for databases."""
    mock_coll = AsyncMock()
    mocker.patch("django.conf.settings.METADATA_COLLECTION", mock_coll)
    return mock_coll


@pytest.fixture
def mock_file_metadata_collection(mocker):
    """
    File metadata collection: Motor-style async methods, sync find() cursor chain.
    """
    coll = MagicMock()
    coll.insert_one = AsyncMock()
    coll.delete_one = AsyncMock()
    coll.find_one = AsyncMock()
    coll.count_documents = AsyncMock()
    coll.find = MagicMock()
    mocker.patch("django.conf.settings.FILE_METADATA_COLLECTION", coll)
    return coll


@pytest.fixture
def metadata_service(user_id, mock_metadata_collection, mock_file_metadata_collection, mock_mongo_client):
    from api.application.metadata_service import MetadataService

    return MetadataService(user_id=user_id)


@pytest.fixture
def gridfs_service(user_id, mock_mongo_client, mocker):
    """GridFSService with AsyncGridFSBucket and real Mongo client patched."""
    mock_bucket = MagicMock()
    mocker.patch(
        "api.application.gridfs_service.AsyncGridFSBucket",
        return_value=mock_bucket,
    )
    from api.application.gridfs_service import GridFSService

    svc = GridFSService(db_name="test_files", user_id=user_id)
    return svc


@pytest.fixture(autouse=True)
def _stub_analytics_task_delay(mocker):
    """Avoid Redis/Celery brokers during API tests."""
    for name in (
        "log_http_request_task",
        "log_db_operation_task",
        "log_mongo_detail_task",
        "log_performance_task",
        "log_client_info_task",
        "log_error_task",
        "log_slow_query_task",
    ):
        mocker.patch(f"analytics.tasks.{name}.delay", return_value=None)
