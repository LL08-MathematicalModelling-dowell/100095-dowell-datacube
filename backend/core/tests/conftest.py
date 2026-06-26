"""Shared fixtures for core app tests."""

import pytest

from core.infrastructure.managers import user_manager


@pytest.fixture(autouse=True)
def _isolate_playground_mongo():
    """Keep the real Mongo auth collection free of test playground users."""
    user_manager.users_collection.delete_many({"is_playground": True})
    yield
    user_manager.users_collection.delete_many({"is_playground": True})
