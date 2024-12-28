import pytest
from rest_framework.test import APIClient
from bson.objectid import ObjectId

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def database_with_collections():
    return {
        "database_id": str(ObjectId()),
        "database_name": "test_database",
        "collections": [
            "users",
            "products",
            "orders"
        ]
    }

@pytest.mark.django_db
def test_create_database_integration(api_client):
    url = "http://127.0.0.1:8000/api/create_database/"
    data = {
    "db_name": "test_database",
    "collections": [
        {"name": "users", "fields": [{"name": "username", "type": "string"}]},
        {"name": "products", "fields": [{"name": "product_name", "type": "string"}]}
    ]
}

    response = api_client.post(url, data=data, format="json")
    assert response.status_code == 201
    assert response.json()["success"] is True
    assert response.json()["database"]["name"] == "test_database"

@pytest.mark.django_db
def test_list_databases_integration(api_client):
    url = "http://127.0.0.1:8000/api/list_databases/"
    response = api_client.get(url, format="json")
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "data" in response.json()

@pytest.mark.django_db
def test_list_collections_integration(api_client, database_with_collections):
    db_id = database_with_collections["database_id"]
    url = f"http://127.0.0.1:8000/api/list_collections/?database_id={db_id}"
    response = api_client.get(url, format="json")
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "data" in response.json()

@pytest.mark.django_db
def test_drop_collections_integration(api_client, database_with_collections):
    db_id = database_with_collections["database_id"]
    collections = database_with_collections["collections"]

    url = "http://127.0.0.1:8000/api/drop_collections/"
    response = api_client.delete(
        url,
        data={
            "database_id": db_id,
            "collection_names": collections
        },
        format="json"
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["details"]["dropped_collections"] == len(collections)

@pytest.mark.django_db
def test_data_crud_operations_integration(api_client, database_with_collections):
    db_id = database_with_collections["database_id"]
    collection_name = "users"

    # Create data
    url = "http://127.0.0.1:8000/api/crud/"
    data = {
        "database_id": db_id,
        "collection_name": collection_name,
        "data": [
            {"username": "john_doe", "email": "john@example.com"},
            {"username": "jane_doe", "email": "jane@example.com"}
        ]
    }
    response = api_client.post(url, data=data, format="json")
    assert response.status_code == 201
    assert response.json()["success"] is True

    # Read data
    url = f"http://127.0.0.1:8000/api/crud/?database_id={db_id}&collection_name={collection_name}"
    response = api_client.get(url, format="json")
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert len(response.json()["data"]) == 2

    # Update data
    url = "http://127.0.0.1:8000/api/crud/"
    update_data = {
        "database_id": db_id,
        "collection_name": collection_name,
        "operation": "update",
        "query": {"username": "john_doe"},
        "update_data": {"email": "new_email@example.com"}
    }
    response = api_client.put(url, data=update_data, format="json")
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Delete data
    delete_data = {
        "database_id": db_id,
        "collection_name": collection_name,
        "operation": "soft_delete",
        "query": {"username": "john_doe"}
    }
    response = api_client.delete(url, data=delete_data, format="json")
    assert response.status_code == 200
    assert response.json()["success"] is True
