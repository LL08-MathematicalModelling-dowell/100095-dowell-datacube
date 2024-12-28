import pytest
from rest_framework.test import APIClient
from unittest.mock import patch
from bson.objectid import ObjectId

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def mock_metadata_coll(mocker):
    return mocker.patch("project.settings.METADATA_COLLECTION")

@pytest.fixture
def mock_mongo_client(mocker):
    return mocker.patch("project.settings.MONGODB_CLIENT")

class TestDatabaseOperations:

    def test_health_check(self, api_client):
        url = "/health_check/"
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        
    @pytest.mark.django_db
    def test_create_database(self, mock_metadata_coll, mock_mongo_client, api_client):
        url = "/api/create_database/"
        data = {
            "db_name": "test_database_01",
            "collections": [
                {"name": "users", "fields": [{"name": "username", "type": "string"}]},
                {"name": "products", "fields": [{"name": "product_name", "type": "string"}]}
            ]
        }

        mock_metadata_coll.insert_one.return_value.inserted_id = ObjectId()
        mock_mongo_client.__getitem__.return_value.__getitem__.return_value.create_collection.return_value = None

        response = api_client.post(url, data=data, format="json")

        assert response.status_code == 201
        assert response.json()["success"] is True
        assert response.json()["database"]["name"] == "test_database_01"

    @pytest.mark.django_db
    def test_list_databases(self, mock_metadata_coll, mock_mongo_client, api_client):
        mock_mongo_client.list_database_names.return_value = ["test_database_01"]
        url = "/api/list_databases/"

        response = api_client.get(url)
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "test_database_01" in [db["name"] for db in response.json()["data"]]

    @pytest.mark.django_db
    def test_list_collections(self, mock_metadata_coll, api_client):
        database_id = str(ObjectId())
        mock_metadata_coll.find_one.return_value = {
            "_id": ObjectId(database_id),
            "database_name": "test_database_01",
            "collections": [
                {"name": "users", "fields": [{"name": "username", "type": "string"}]},
                {"name": "products", "fields": [{"name": "product_name", "type": "string"}]}
            ]
        }

        url = f"/api/list_collections/?database_id={database_id}"
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "users" in [coll["name"] for coll in response.json()["data"]]

    @pytest.mark.django_db
    def test_drop_collections(self, mock_metadata_coll, mock_mongo_client, api_client):
        database_id = str(ObjectId())
        mock_metadata_coll.find_one.return_value = {
            "_id": ObjectId(database_id),
            "database_name": "test_database_01",
            "collections": [
                {"name": "users", "fields": [{"name": "username", "type": "string"}]},
                {"name": "products", "fields": [{"name": "product_name", "type": "string"}]}
            ]
        }

        url = "/api/drop_collections/"
        data = {
            "database_id": database_id,
            "collection_names": ["users", "products"]
        }

        mock_mongo_client.__getitem__.return_value.__getitem__.return_value.drop.return_value = None

        response = api_client.delete(url, data=data, format="json")

        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["details"]["dropped_collections"] == 2

    @pytest.mark.django_db
    def test_data_crud(self, mock_metadata_coll, mock_mongo_client, api_client):
        database_id = str(ObjectId())
        mock_metadata_coll.find_one.return_value = {
            "_id": ObjectId(database_id),
            "database_name": "test_database_01",
            "collections": [
                {"name": "users", "fields": [{"name": "username", "type": "string"}]}
            ]
        }

        # POST Data
        url = "/api/crud/"
        data = {
            "database_id": database_id,
            "collection_name": "users",
            "data": [{"username": "john_doe"}]
        }

        mock_mongo_client.__getitem__.return_value.__getitem__.return_value.insert_one.return_value.inserted_id = ObjectId()

        response = api_client.post(url, data=data, format="json")
        assert response.status_code == 201
        assert response.json()["success"] is True
