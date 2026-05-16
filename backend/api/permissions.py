from django.conf import settings
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from core.infrastructure.roles import ROLE_ADMIN, ROLE_ANALYST, ROLE_DEVELOPER, normalize_role


class IsAdminUserOrInternalIP(BasePermission):
    """
    Allows access only to admin users or requests from internal IP addresses.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:  # pyright: ignore[reportIncompatibleMethodOverride]
        if request.user and request.user.is_staff:
            return True
        ip_addr: str | None = request.META.get("REMOTE_ADDR")
        internal_ips: set[str] = set(settings.INTERNAL_IPS)
        if ip_addr is not None and ip_addr in internal_ips:
            return True
        return False


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
