"""Shared user context for application services (ownership + RBAC)."""

from __future__ import annotations

from api.infrastructure.rbac import assert_can_write_data
from core.infrastructure.roles import normalize_role


class UserServiceContext:
    """Binds API services to one user and enforces write role in the service layer."""

    def __init__(self, user_id: str, *, role: str | None = None) -> None:
        if not user_id:
            raise ValueError("user_id is required")
        self.user_id = str(user_id)
        self.role = normalize_role(role)

    def assert_can_write(self) -> None:
        assert_can_write_data(role=self.role)
