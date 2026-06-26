"""Ephemeral playground session endpoint.

Sync DRF view: session start and seeding use only sync PyMongo (auth DB +
SYNC_MONGODB_CLIENT). This endpoint never touches AsyncMongoClient, so it
cannot bind the global async client to a per-request event loop and break
analytics / dashboard async views afterward.
"""

import logging

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.application.playground_service import (
    PlaygroundCapacityError,
    seed_playground_database_sync,
    start_or_resume_playground,
)
from core.infrastructure.authentication import MongoUser
from core.infrastructure.jwt_tokens import RefreshToken
from core.infrastructure.playground import (
    PLAYGROUND_COOKIE,
    get_client_ip,
    playground_enabled,
    read_playground_session_id,
)

logger = logging.getLogger(__name__)


class PlaygroundStartView(APIView):
    """Create or resume an ephemeral playground session and return JWTs."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = []

    def post(self, request):
        if not playground_enabled():
            return Response(
                {"error": "Playground is not enabled on this server."},
                status=status.HTTP_404_NOT_FOUND,
            )

        session_id = read_playground_session_id(request)
        ip = get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        try:
            user_doc, reused = start_or_resume_playground(
                session_id=session_id,
                ip=ip,
                user_agent=user_agent,
            )
        except PlaygroundCapacityError as exc:
            return Response(
                {"error": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        if not reused:
            try:
                seed_playground_database_sync(str(user_doc["_id"]))
            except Exception:
                logger.exception(
                    "Playground seed failed for user %s", user_doc.get("_id")
                )

        proxy_user = MongoUser(user_doc)
        refresh = RefreshToken.for_user(proxy_user)
        expires_at = user_doc.get("playground_expires_at")
        session_out = user_doc.get("playground_session_id")

        body = {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "firstName": user_doc.get("firstName", "Playground"),
            "lastName": user_doc.get("lastName", "Guest"),
            "role": proxy_user.role,
            "email_verified": True,
            "is_playground": True,
            "playground_session_id": session_out,
            "playground_expires_at": expires_at.isoformat() if expires_at else None,
            "reused_session": reused,
        }
        response = Response(body, status=status.HTTP_200_OK)

        cookie_max_age = int(
            getattr(settings, "PLAYGROUND_COOKIE_MAX_AGE_SECONDS", 30 * 24 * 3600)
        )
        secure_cookie = not getattr(settings, "DEBUG", False)
        response.set_cookie(
            PLAYGROUND_COOKIE,
            session_out,
            max_age=cookie_max_age,
            httponly=True,
            secure=secure_cookie,
            samesite="Lax",
        )
        return response
