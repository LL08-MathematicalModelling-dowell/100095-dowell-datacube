from locust import HttpUser, task, between
import json
from bson.objectid import ObjectId

class APILoadTest(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        """Setup initial data for the load test."""
        self.database_id = str(ObjectId())  # Mock database ID
        self.collection_name = "users"  # Mock collection name
        self.collection_names = ["users", "products"]  # Mock collection names
        self.base_headers = {
            "Content-Type": "application/json"
        }

    @task
    def create_database(self):
        """Task to test creating a database."""
        url = "/api/create_database/"
        payload = {
            "db_name": "test_database_load",
            "collections": [
                {"name": "users", "fields": [{"name": "username", "type": "string"}]},
                {"name": "products", "fields": [{"name": "product_name", "type": "string"}]}
            ]
        }
        self.client.post(url, data=json.dumps(payload), headers=self.base_headers)

    @task
    def list_databases(self):
        """Task to test listing databases."""
        url = "/api/list_databases/"
        self.client.get(url, headers=self.base_headers)

    @task
    def list_collections(self):
        """Task to test listing collections in a database."""
        url = f"/api/list_collections/?database_id={self.database_id}"
        self.client.get(url, headers=self.base_headers)

    @task
    def data_crud_post(self):
        """Task to test creating data in a collection."""
        url = "/api/data_crud/"
        payload = {
            "database_id": self.database_id,
            "collection_name": self.collection_name,
            "data": [{"username": "load_user", "email": "load_user@example.com"}]
        }
        self.client.post(url, data=json.dumps(payload), headers=self.base_headers)

    @task
    def data_crud_get(self):
        """Task to test fetching data from a collection."""
        url = f"/api/data_crud/?database_id={self.database_id}&collection_name={self.collection_name}"
        self.client.get(url, headers=self.base_headers)

    @task
    def drop_collections(self):
        """Task to test dropping collections from a database."""
        url = "/api/drop_collections/"
        payload = {
            "database_id": self.database_id,
            "collection_names": self.collection_names
        }
        self.client.delete(url, data=json.dumps(payload), headers=self.base_headers)
