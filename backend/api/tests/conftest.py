import pytest
from bson import ObjectId

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
