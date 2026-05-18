from rest_framework.permissions import SAFE_METHODS, BasePermission

from core.infrastructure.roles import ROLE_ADMIN, ROLE_ANALYST, ROLE_DEVELOPER, normalize_role


class IsDeveloperOrAdmin(BasePermission):
    message = "Developer or admin role required."

    def has_permission(self, request, view):
        if not request.user or not getattr(request.user, "is_authenticated", False):
            return False
        r = normalize_role(getattr(request.user, "role", None))
        return r in (ROLE_DEVELOPER, ROLE_ADMIN)


class BlockAnalystOnUnsafeMethods(BasePermission):
    """Analysts may use only safe HTTP methods (read-only)."""

    message = "Analyst role is read-only for this endpoint."

    def has_permission(self, request, view):
        if not request.user or not getattr(request.user, "is_authenticated", False):
            return False
        if normalize_role(getattr(request.user, "role", None)) == ROLE_ANALYST:
            return request.method in SAFE_METHODS
        return True
