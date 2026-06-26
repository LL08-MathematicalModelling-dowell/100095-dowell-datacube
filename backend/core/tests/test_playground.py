"""Tests for ephemeral playground sessions."""

from datetime import datetime, timedelta, timezone

import pytest
from django.test import override_settings
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture(autouse=True)
def _stub_seed(mocker):
    """Avoid touching real tenant DBs during start-endpoint tests."""
    mocker.patch(
        "core.presentation.views.playground_views.seed_playground_database_sync",
        return_value=None,
    )


@pytest.mark.django_db
def test_playground_start_disabled_when_flag_off(api_client):
    with override_settings(PLAYGROUND_ENABLED=False):
        response = api_client.post("/core/api/v2/playground/start/", {}, format="json")
    assert response.status_code == 404


@pytest.mark.django_db
@override_settings(PLAYGROUND_ENABLED=True, PLAYGROUND_MAX_ACTIVE_SESSIONS=500)
def test_playground_start_creates_session(api_client):
    response = api_client.post("/core/api/v2/playground/start/", {}, format="json")
    assert response.status_code == 200
    body = response.json()
    assert body["access"]
    assert body["refresh"]
    assert body["is_playground"] is True
    assert body["reused_session"] is False
    assert body["playground_session_id"]
    assert "pg_session" in response.cookies


@pytest.mark.django_db
@override_settings(PLAYGROUND_ENABLED=True)
def test_playground_start_reuses_session(api_client):
    first = api_client.post("/core/api/v2/playground/start/", {}, format="json")
    session_id = first.json()["playground_session_id"]

    second = api_client.post(
        "/core/api/v2/playground/start/",
        {"session_id": session_id},
        format="json",
    )
    assert second.status_code == 200
    assert second.json()["reused_session"] is True
    assert second.json()["playground_session_id"] == session_id


@pytest.mark.django_db
@override_settings(PLAYGROUND_ENABLED=True, PLAYGROUND_MAX_ACTIVE_SESSIONS=1)
def test_playground_capacity_limit(api_client, mocker):
    mocker.patch(
        "core.application.playground_service.user_manager.count_live_playground_sessions",
        side_effect=[0, 1],
    )
    mocker.patch(
        "core.application.playground_service.user_manager.count_live_playground_sessions_by_ip",
        return_value=0,
    )
    first = api_client.post("/core/api/v2/playground/start/", {}, format="json")
    assert first.status_code == 200

    second_client = APIClient()
    second = second_client.post("/core/api/v2/playground/start/", {}, format="json")
    assert second.status_code == 503


def test_playground_is_live_respects_expiry():
    from core.infrastructure.playground import playground_is_live

    expired = {
        "is_playground": True,
        "playground_expires_at": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    live = {
        "is_playground": True,
        "playground_expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    assert playground_is_live(expired) is False
    assert playground_is_live(live) is True
