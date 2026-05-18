"""Role helpers for the data API (defense in depth alongside DRF permissions)."""

from __future__ import annotations

from core.infrastructure.roles import (
    ROLE_ADMIN,
    ROLE_ANALYST,
    ROLE_DEVELOPER,
    normalize_role,
)


class ReadOnlyRoleError(PermissionError):
    """Raised when an analyst attempts a mutating operation."""


def user_role(user) -> str:
    return normalize_role(getattr(user, "role", None))


def can_write_data(role: str | None = None, *, user=None) -> bool:
    """Developer and admin may mutate data; analyst is read-only."""
    r = role if role is not None else user_role(user)
    return r in (ROLE_DEVELOPER, ROLE_ADMIN)


def assert_can_write_data(*, role: str | None = None, user=None) -> None:
    if not can_write_data(role=role, user=user):
        raise ReadOnlyRoleError("Analyst role is read-only for this operation.")
