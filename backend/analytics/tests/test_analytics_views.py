from django.test import TestCase

# Create your tests here.
import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from rest_framework import status

from analytics.views.analytics_views import AnalyticsDashboardView, AnalyticsStorageView


@pytest.fixture
def mock_user():
    """Create a mock authenticated user with a string primary key."""
    user = type('User', (), {'pk': '123', 'is_authenticated': True})()
    return user


@pytest.fixture
def request_factory():
    """Django request factory for building test requests."""
    return RequestFactory()


@pytest.mark.asyncio
class TestAnalyticsDashboardView:
    """Test suite for AnalyticsDashboardView."""

    async def test_get_dashboard_success(self, request_factory, mock_user, mocker):
        """Valid request returns dashboard charts."""
        # Mock AnalyticsService and its method
        mock_service = mocker.patch('api.views.analytics_views.AnalyticsService')
        mock_service.return_value.get_dashboard_charts.return_value = {
            "historical": [{"date": "2023-01-01", "ops": 100}],
            "today_hourly": [{"_id": 10, "ops": 5}]
        }

        # Build request with query parameters
        request = request_factory.get('/analytics/dashboard/', {'db_id': 'db123', 'days': 7})
        request.user = mock_user

        view = AnalyticsDashboardView()
        response = await view.get(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'historical' in response.data['data']
        assert 'today_hourly' in response.data['data']

        # Verify service was instantiated with correct user and method called correctly
        mock_service.assert_called_once_with(user_id='123')
        mock_service.return_value.get_dashboard_charts.assert_called_once_with(db_id='db123', days=7)

    async def test_get_dashboard_default_days(self, request_factory, mock_user, mocker):
        """When days is omitted, default to 7."""
        mock_service = mocker.patch('api.views.analytics_views.AnalyticsService')
        mock_service.return_value.get_dashboard_charts.return_value = {}

        request = request_factory.get('/analytics/dashboard/', {'db_id': 'db123'})
        request.user = mock_user

        view = AnalyticsDashboardView()
        response = await view.get(request)

        assert response.status_code == 200
        mock_service.return_value.get_dashboard_charts.assert_called_once_with(db_id='db123', days=7)

    async def test_get_dashboard_missing_db_id(self, request_factory, mock_user):
        """Missing db_id triggers validation error (400)."""
        request = request_factory.get('/analytics/dashboard/', {})
        request.user = mock_user

        view = AnalyticsDashboardView()
        response = await view.get(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # The exact error structure depends on your validate_serializer implementation
        # Typically it returns a dict with field errors
        assert 'db_id' in str(response.data)

    async def test_get_dashboard_invalid_days(self, request_factory, mock_user):
        """days less than 1 should be rejected."""
        request = request_factory.get('/analytics/dashboard/', {'db_id': 'db123', 'days': 0})
        request.user = mock_user

        view = AnalyticsDashboardView()
        response = await view.get(request)

        assert response.status_code == 400
        # days field should have validation error
        assert 'days' in str(response.data)

    async def test_get_dashboard_service_error(self, request_factory, mock_user, mocker):
        """Service exception is caught and returns 500."""
        mock_service = mocker.patch('api.views.analytics_views.AnalyticsService')
        mock_service.return_value.get_dashboard_charts.side_effect = Exception("DB connection error")

        request = request_factory.get('/analytics/dashboard/', {'db_id': 'db123', 'days': 7})
        request.user = mock_user

        view = AnalyticsDashboardView()
        # Assuming @BaseAPIView.handle_errors converts exception to error response
        response = await view.get(request)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'DB connection error' in response.data.get('message', '')


@pytest.mark.asyncio
class TestAnalyticsStorageView:
    """Test suite for AnalyticsStorageView."""

    async def test_get_storage_success(self, request_factory, mock_user, mocker):
        """Valid request returns storage statistics."""
        mock_service = mocker.patch('api.views.analytics_views.AnalyticsService')
        expected_data = {
            "timestamp": "2023-01-01T00:00:00",
            "size_mb": 12.5
        }
        mock_service.return_value.get_storage_stats.return_value = expected_data

        request = request_factory.get('/analytics/storage/', {'db_id': 'db123'})
        request.user = mock_user

        view = AnalyticsStorageView()
        response = await view.get(request)

        assert response.status_code == 200
        assert response.data['success'] is True
        assert response.data['data'] == expected_data
        mock_service.assert_called_once_with(user_id='123')
        mock_service.return_value.get_storage_stats.assert_called_once_with(db_id='db123')

    async def test_get_storage_no_stats(self, request_factory, mock_user, mocker):
        """When no stats exist, service returns empty dict and view passes it through."""
        mock_service = mocker.patch('api.views.analytics_views.AnalyticsService')
        mock_service.return_value.get_storage_stats.return_value = {}

        request = request_factory.get('/analytics/storage/', {'db_id': 'db123'})
        request.user = mock_user

        view = AnalyticsStorageView()
        response = await view.get(request)

        assert response.status_code == 200
        assert response.data['data'] == {}

    async def test_get_storage_missing_db_id(self, request_factory, mock_user):
        """Missing db_id triggers validation error (400)."""
        request = request_factory.get('/analytics/storage/', {})
        request.user = mock_user

        view = AnalyticsStorageView()
        response = await view.get(request)

        assert response.status_code == 400
        assert 'db_id' in str(response.data)

    async def test_get_storage_service_error(self, request_factory, mock_user, mocker):
        """Service exception is caught and returns 500."""
        mock_service = mocker.patch('api.views.analytics_views.AnalyticsService')
        mock_service.return_value.get_storage_stats.side_effect = Exception("MongoDB error")

        request = request_factory.get('/analytics/storage/', {'db_id': 'db123'})
        request.user = mock_user

        view = AnalyticsStorageView()
        response = await view.get(request)

        assert response.status_code == 500
        assert 'MongoDB error' in response.data.get('message', '')