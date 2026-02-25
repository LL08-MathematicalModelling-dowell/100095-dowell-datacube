import pytest
from bson import ObjectId
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def database_with_collections(mock_metadata_coll):
    db_id = str(ObjectId())
    mock_metadata_coll.find_one.return_value = {
        "_id": ObjectId(db_id),
        "database_name": "test_database",
        "collections": [
            {"name": "users", "fields": [{"name": "username", "type": "string"}]},
            {"name": "products", "fields": [{"name": "product_name", "type": "string"}]}
        ]
    }
    return {"database_id": db_id, "database_name": "test_database", "collections": ["users", "products"]}


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
    """Mock the file metadata collection."""
    mock_coll = AsyncMock()
    mocker.patch("django.conf.settings.FILE_METADATA_COLLECTION", mock_coll)
    return mock_coll

@pytest.fixture
def mock_gridfs_bucket(mocker):
    """Mock the AsyncGridFSBucket class."""
    mock_bucket = AsyncMock()
    mocker.patch("gridfs.asynchronous.AsyncGridFSBucket", return_value=mock_bucket)
    return mock_bucket

@pytest.fixture
def metadata_service(user_id, mock_metadata_collection, mock_file_metadata_collection, mock_mongo_client):
    from api.services.metadata_service import MetadataService
    return MetadataService(user_id=user_id)

@pytest.fixture
def gridfs_service(user_id, mock_mongo_client, mock_gridfs_bucket):
    from api.services.gridfs_service import GridFSService
    return GridFSService(db_name="test_files", user_id=user_id)