import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch

@pytest.mark.django_db
class TestDataCrudViewPost:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def url(self):
        return reverse('data-crud-view-post')

    @patch('api.views.DataCrudView.async_post')
    def test_post_success(self, mock_async_post, api_client, url):
        mock_async_post.return_value = {
            "success": True,
            "message": "Documents inserted successfully",
            "inserted_ids": ["60d5f9b3f3a3c2a1d4e8b456"]
        }
        data = {
            "database_id": "60d5f9b3f3a3c2a1d4e8b456",
            "collection_name": "test_collection",
            "data": {"field1": "value1", "field2": "value2"}
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True
        assert response.data["message"] == "Documents inserted successfully"

    @patch('api.views.DataCrudView.async_post')
    def test_post_invalid_data(self, mock_async_post, api_client, url):
        mock_async_post.side_effect = ValueError("Invalid fields: field3")
        data = {
            "database_id": "60d5f9b3f3a3c2a1d4e8b456",
            "collection_name": "test_collection",
            "data": {"field3": "value3"}
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False
        assert "Invalid fields: field3" in response.data["message"]

    @patch('api.views.DataCrudView.async_post')
    def test_post_server_error(self, mock_async_post, api_client, url):
        mock_async_post.side_effect = Exception("Server error")
        data = {
            "database_id": "60d5f9b3f3a3c2a1d4e8b456",
            "collection_name": "test_collection",
            "data": {"field1": "value1", "field2": "value2"}
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data["success"] is False
        assert "Server error" in response.data["message"]