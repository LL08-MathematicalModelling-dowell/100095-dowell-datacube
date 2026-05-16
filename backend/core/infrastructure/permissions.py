"""DRF permissions for role checks (email verification enforced in JWT/API key auth)."""

from rest_framework.permissions import BasePermission

from core.infrastructure.roles import ROLE_ADMIN, ROLE_ANALYST, normalize_role


class IsRoleAdmin(BasePermission):
    message = "Admin role required."

    def has_permission(self, request, view):
        u = request.user
        if not u or not getattr(u, "is_authenticated", False):
            return False
        return normalize_role(getattr(u, "role", None)) == ROLE_ADMIN


class IsRoleAnalystOrAdmin(BasePermission):
    message = "Analyst or admin role required."

    def has_permission(self, request, view):
        u = request.user
        if not u or not getattr(u, "is_authenticated", False):
            return False
        return normalize_role(getattr(u, "role", None)) in (ROLE_ADMIN, ROLE_ANALYST)
