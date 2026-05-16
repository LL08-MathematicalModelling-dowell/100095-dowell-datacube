import pytest
from unittest.mock import AsyncMock, MagicMock
from bson.objectid import ObjectId


class TestDatabaseOperations:

    def test_health_check(self, api_client):
        url = "/api/v2/health_check/"
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.json().get("status") == "healthy"

    @pytest.mark.django_db
    def test_create_database(self, authenticated_api_client, mocker):
        meta = {
            "_id": ObjectId(),
            "displayName": "test_database_01",
            "dbName": "internal_test_db",
        }
        coll_info = ["users", "products"]

        mocker.patch(
            "api.application.metadata_service.MetadataService.exists_db",
            new=AsyncMock(return_value=False),
        )
        mocker.patch(
            "api.application.database_service.DatabaseService.create_database_with_collections",
            new=AsyncMock(return_value=(meta, coll_info)),
        )

        url = "/api/v2/create_database/"
        data = {
            "db_name": "test_database_01",
            "collections": [
                {"name": "users", "fields": [{"name": "username", "type": "string"}]},
                {"name": "products", "fields": [{"name": "product_name", "type": "string"}]},
            ],
        }

        response = authenticated_api_client.post(url, data=data, format="json")

        assert response.status_code == 201
        assert response.json()["success"] is True
        assert response.json()["database"]["name"] == "test_database_01"

    @pytest.mark.django_db
    def test_list_databases(self, authenticated_api_client, mocker):
        rows = [
            {
                "id": str(ObjectId()),
                "name": "test_database_01",
                "num_collections": 2,
            }
        ]
        mocker.patch(
            "api.application.metadata_service.MetadataService.list_databases_paginated",
            new=AsyncMock(return_value=(1, rows)),
        )

        url = "/api/v2/list_databases/"
        response = authenticated_api_client.get(url)

        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "test_database_01" in [db["name"] for db in response.json()["data"]]

    @pytest.mark.django_db
    def test_list_collections(self, authenticated_api_client, mocker):
        database_id = str(ObjectId())
        cols = [
            {
                "name": "users",
                "num_documents": 0,
                "fields": [{"name": "username", "type": "string"}],
            },
            {
                "name": "products",
                "num_documents": 0,
                "fields": [{"name": "product_name", "type": "string"}],
            },
        ]
        mocker.patch(
            "api.application.metadata_service.MetadataService.list_collections_with_live_counts",
            new=AsyncMock(return_value=cols),
        )

        url = f"/api/v2/list_collections/?database_id={database_id}"
        response = authenticated_api_client.get(url)

        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "users" in [coll["name"] for coll in response.json()["collections"]]

    @pytest.mark.django_db
    def test_drop_collections(self, authenticated_api_client, mocker):
        database_id = str(ObjectId())

        mocker.patch(
            "api.application.metadata_service.MetadataService.get_db",
            new=AsyncMock(
                return_value={
                    "_id": ObjectId(database_id),
                    "dbName": "internal",
                    "collections": [
                        {"name": "users", "fields": []},
                        {"name": "products", "fields": []},
                    ],
                }
            ),
        )
        mocker.patch(
            "api.application.metadata_service.MetadataService.drop_collections",
            new=AsyncMock(return_value=["users", "products"]),
        )

        url = "/api/v2/drop_collections/"
        data = {
            "database_id": database_id,
            "collection_names": ["users", "products"],
        }

        response = authenticated_api_client.delete(url, data=data, format="json")

        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["dropped"] == ["users", "products"]

    @pytest.mark.django_db
    def test_data_crud(self, authenticated_api_client, mocker):
        database_id = str(ObjectId())

        mocker.patch(
            "api.application.metadata_service.MetadataService.check_quota_is_exceeded",
            new=AsyncMock(return_value=False),
        )

        mock_insert = MagicMock()
        mock_insert.inserted_ids = [ObjectId(), ObjectId()]
        mocker.patch(
            "api.application.document_service.DocumentService.create_docs",
            new=AsyncMock(return_value=mock_insert),
        )

        url = "/api/v2/crud/"
        data = {
            "database_id": database_id,
            "collection_name": "users",
            "documents": [
                {"username": "john_doe"},
                {"username": "jane_doe"},
            ],
        }

        response = authenticated_api_client.post(url, data=data, format="json")
        assert response.status_code == 201
        assert response.json()["success"] is True
        assert len(response.json()["inserted_ids"]) == 2
