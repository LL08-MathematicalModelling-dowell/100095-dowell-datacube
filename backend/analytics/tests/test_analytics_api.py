import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import ANY

User = get_user_model()


@pytest.fixture
def api_client():
    """Return an API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, django_user_model):
    """Create a user and authenticate the client."""
    user = django_user_model.objects.create_user(
        username="testuser",
        password="testpass"
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def mock_analytics_service(mocker):
    """Mock the entire AnalyticsService class."""
    mock = mocker.patch("api.views.analytics_views.AnalyticsService")
    # Return a mock instance with async methods (but we call sync ones via sync_to_async)
    instance = mock.return_value
    instance.get_dashboard_charts.return_value = {
        "historical": [
            {"date": "2023-01-01", "total_ops": 100, "avg_latency": 15.5, "error_count": 2}
        ],
        "today_hourly": [
            {"_id": 10, "ops": 5, "latency": 12.3}
        ]
    }
    instance.get_storage_stats.return_value = {
        "doc_count": 1000,
        "size_mb": 5.2,
        "storage_mb": 6.1,
        "index_size_mb": 1.5
    }
    return mock


@pytest.fixture
def mock_pdf_generator(mocker):
    """Mock the PDF generator function."""
    return mocker.patch(
        "api.views.analytics_views.generate_pdf_report",
        return_value=b"%PDF-1.4 mock pdf content"
    )


@pytest.mark.django_db
class TestAnalyticsDashboardAPI:
    """Test the analytics dashboard endpoint."""

    def test_get_dashboard_success(self, authenticated_client, mock_analytics_service):
        """Valid request returns dashboard data."""
        url = reverse("analytics-dashboard")  # adjust name if different
        response = authenticated_client.get(url, {"db_id": "db123", "days": 7})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "historical" in response.data["data"]
        assert "today_hourly" in response.data["data"]

        # Verify service called with correct args
        mock_analytics_service.assert_called_once_with(user_id=str(ANY))
        instance = mock_analytics_service.return_value
        instance.get_dashboard_charts.assert_called_once_with(db_id="db123", days=7)

    def test_get_dashboard_default_days(self, authenticated_client, mock_analytics_service):
        """When days omitted, default to 7."""
        response = authenticated_client.get(url, {"db_id": "db123"})

        assert response.status_code == 200
        instance = mock_analytics_service.return_value
        instance.get_dashboard_charts.assert_called_once_with(db_id="db123", days=7)

    def test_get_dashboard_missing_db_id(self, authenticated_client):
        """Missing db_id returns 400."""
        response = authenticated_client.get(url, {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "db_id" in response.data

    def test_get_dashboard_invalid_days(self, authenticated_client):
        """Days less than 1 returns 400."""
        response = authenticated_client.get(url, {"db_id": "db123", "days": 0})

        assert response.status_code == 400
        assert "days" in response.data

    def test_get_dashboard_unauthenticated(self, api_client):
        """Unauthenticated request returns 401."""
        url = reverse("analytics-dashboard")
        response = api_client.get(url, {"db_id": "db123"})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestAnalyticsStorageAPI:
    """Test the storage endpoint."""

    def test_get_storage_success(self, authenticated_client, mock_analytics_service):
        """Valid request returns storage stats."""
        url = reverse("analytics-storage")  # adjust name if different
        response = authenticated_client.get(url, {"db_id": "db123"})

        assert response.status_code == 200
        assert response.data["success"] is True
        assert response.data["data"] == mock_analytics_service.return_value.get_storage_stats.return_value

        instance = mock_analytics_service.return_value
        instance.get_storage_stats.assert_called_once_with(db_id="db123")

    def test_get_storage_missing_db_id(self, authenticated_client):
        """Missing db_id returns 400."""
        response = authenticated_client.get(url, {})

        assert response.status_code == 400
        assert "db_id" in response.data

    def test_get_storage_unauthenticated(self, api_client):
        response = api_client.get(url, {"db_id": "db123"})
        assert response.status_code == 401


@pytest.mark.django_db
class TestAnalyticsExportAPI:
    """Test the export endpoint."""

    def test_export_pdf_success(self, authenticated_client, mock_analytics_service, mock_pdf_generator):
        """Valid request returns PDF file."""
        url = reverse("analytics-export")  # adjust name if different
        response = authenticated_client.get(url, {"db_id": "db123", "days": 30, "format": "pdf"})

        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"
        assert 'attachment; filename="analytics_report_' in response["Content-Disposition"]

        # Verify services called
        instance = mock_analytics_service.return_value
        instance.get_dashboard_charts.assert_called_once_with(db_id="db123", days=30)
        instance.get_storage_stats.assert_called_once_with(db_id="db123")

        # Verify PDF generator called with combined data
        expected_data = {
            "historical": instance.get_dashboard_charts.return_value["historical"],
            "today_hourly": instance.get_dashboard_charts.return_value["today_hourly"],
            "storage": instance.get_storage_stats.return_value
        }
        mock_pdf_generator.assert_called_once_with(
            data=expected_data, db_id="db123", days=30
        )

    def test_export_pdf_default_days(self, authenticated_client, mock_analytics_service, mock_pdf_generator):
        """Default days = 30."""
        response = authenticated_client.get(url, {"db_id": "db123", "format": "pdf"})

        assert response.status_code == 200
        instance = mock_analytics_service.return_value
        instance.get_dashboard_charts.assert_called_once_with(db_id="db123", days=30)

    def test_export_missing_db_id(self, authenticated_client):
        """Missing db_id returns 400."""
        response = authenticated_client.get(url, {"format": "pdf"})

        assert response.status_code == 400
        assert "db_id" in response.data

    def test_export_invalid_format(self, authenticated_client):
        """Unsupported format returns 400."""
        response = authenticated_client.get(url, {"db_id": "db123", "format": "csv"})

        assert response.status_code == 400
        # The serializer should reject invalid format; check error on 'format'
        assert "format" in response.data

    def test_export_unauthenticated(self, api_client):
        response = api_client.get(url, {"db_id": "db123", "format": "pdf"})
        assert response.status_code == 401