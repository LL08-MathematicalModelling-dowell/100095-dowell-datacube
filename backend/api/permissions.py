from rest_framework.permissions import BasePermission
from django.conf import settings
from rest_framework.request import Request
from rest_framework.views import APIView


class IsAdminUserOrInternalIP(BasePermission):
    """
    Allows access only to admin users or requests from internal IP addresses.
    """
    def has_permission(self, request: Request, view: APIView) -> bool: # pyright: ignore[reportIncompatibleMethodOverride]
        """
        Check if the user is an admin or if the request comes from an internal IP address.
        """
        # Check if the user is an admin
        if request.user and request.user.is_staff:
            return True

        # Check if the request comes from an internal IP
        # REMOTE_ADDR might not always be present or reliable depending on your proxy setup
        ip_addr: str | None = request.META.get('REMOTE_ADDR')
        internal_ips: set[str] = set(settings.INTERNAL_IPS) 

        if ip_addr is not None and ip_addr in internal_ips:
            return True

        return False