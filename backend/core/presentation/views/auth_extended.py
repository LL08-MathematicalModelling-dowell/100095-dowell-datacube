"""OTP email auth, OAuth PKCE (Google/GitHub), profile avatar, account deletion."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from django.conf import settings
from django.http import HttpResponse
from django.urls import reverse
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from core.infrastructure.authentication import MongoUser
from core.infrastructure.jwt_tokens import RefreshToken
from core.infrastructure.managers import user_manager
from core.infrastructure.permissions import IsRoleAdmin
from core.infrastructure.auth_throttles import OAuthThrottle, RegisterThrottle
from core.infrastructure.oauth_pkce import (
    exchange_github_code,
    exchange_google_code,
    github_primary_email,
    github_profile,
    google_userinfo,
)
from core.infrastructure.otp import OtpPurpose, generate_numeric_code, save_otp_challenge, verify_otp_challenge
from core.infrastructure.resend_client import send_otp_email
from core.infrastructure.roles import normalize_role
from core.infrastructure.user_access import effective_email_verified
from core.presentation.serializers import (
    AdminSetUserRoleSerializer,
    EmailOnlyRegistrationSerializer,
    GitHubOAuthSerializer,
    GoogleOAuthSerializer,
    OtpRequestSerializer,
    OtpVerifySerializer,
)


logger = logging.getLogger(__name__)


def _first_name_from_user(user_doc: dict, email: str) -> str:
    return (user_doc.get("firstName") or email.split("@")[0]).strip() or "there"


def send_otp_email_challenge(email: str, purpose: OtpPurpose) -> Response:
    """Create OTP for an existing user and send via email (safe response if user missing)."""
    user_doc = user_manager.get_user_by_email(email)
    if not user_doc:
        return Response(
            {"message": "If an account matches, an email was sent."},
            status=status.HTTP_200_OK,
        )
    if purpose == "register" and user_doc.get("is_email_verified"):
        return Response(
            {"message": "If an account matches, an email was sent."},
            status=status.HTTP_200_OK,
        )
    if purpose == "login_email" and not effective_email_verified(user_doc):
        return Response(
            {"message": "If an account matches, an email was sent."},
            status=status.HTTP_200_OK,
        )
    if purpose == "reset_password" and not effective_email_verified(user_doc):
        return Response(
            {"message": "If an account matches, an email was sent."},
            status=status.HTTP_200_OK,
        )

    code = generate_numeric_code()
    save_otp_challenge(user_id=user_doc["_id"], purpose=purpose, code=code)
    try:
        send_otp_email(
            to_email=email,
            first_name=_first_name_from_user(user_doc, email),
            code=code,
            purpose=purpose,
        )
    except Exception as e:
        logger.exception("Failed to send OTP: %s", e)
        return Response(
            {"error": "Could not send email. Try again later."},
            status=status.HTTP_502_BAD_GATEWAY,
        )
    return Response(
        {"message": "If an account matches, an email was sent."},
        status=status.HTTP_200_OK,
    )


_ALLOWED_AVATAR_TYPES = frozenset(
    {"image/jpeg", "image/png", "image/webp", "image/gif"},
)
_MAX_AVATAR_BYTES = 3 * 1024 * 1024


class OTPRequestThrottle(AnonRateThrottle):
    scope = "otp"
    rate = "30/hour"


class EmailOnlyRegistrationView(APIView):
    """Create a passwordless user and email a registration OTP."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [RegisterThrottle]

    def post(self, request):
        serializer = EmailOnlyRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user_doc = serializer.save()
        code = generate_numeric_code()
        save_otp_challenge(user_id=user_doc["_id"], purpose="register", code=code)
        try:
            send_otp_email(
                to_email=user_doc["email"],
                first_name=_first_name_from_user(user_doc, user_doc["email"]),
                code=code,
                purpose="register",
            )
        except Exception as e:
            logger.exception("Failed to send registration OTP: %s", e)
            return Response(
                {"error": "Could not send verification email. Try again later."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response(
            {"message": "Check your email for a verification code."},
            status=status.HTTP_201_CREATED,
        )


class OtpRequestView(APIView):
    """Request an emailed OTP (complete email verification or passwordless login)."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [OTPRequestThrottle]

    def post(self, request):
        serializer = OtpRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        email = serializer.validated_data["email"]
        purpose: OtpPurpose = serializer.validated_data["purpose"]
        return send_otp_email_challenge(email, purpose)


class OtpVerifyView(APIView):
    """Verify OTP and issue JWTs (registration or passwordless login)."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OtpVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]
        purpose: OtpPurpose = serializer.validated_data["purpose"]

        user_doc = user_manager.get_user_by_email(email)
        if not user_doc:
            return Response({"error": "Invalid code or email."}, status=status.HTTP_400_BAD_REQUEST)

        if purpose == "register":
            if user_doc.get("is_email_verified"):
                return Response({"error": "Account already verified."}, status=status.HTTP_400_BAD_REQUEST)
        elif purpose == "login_email":
            if not effective_email_verified(user_doc):
                return Response(
                    {"error": "Complete email verification before signing in."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if not verify_otp_challenge(user_id=user_doc["_id"], purpose=purpose, code=code):
            return Response({"error": "Invalid or expired code."}, status=status.HTTP_400_BAD_REQUEST)

        if purpose == "register":
            user_manager.set_email_verified(user_doc["_id"], True)
            user_doc = user_manager.get_user_by_id(str(user_doc["_id"]))

        proxy = MongoUser(user_doc)
        refresh = RefreshToken.for_user(proxy)
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "firstName": user_doc.get("firstName", ""),
                "lastName": user_doc.get("lastName", ""),
                "role": proxy.role,
                "email_verified": proxy.is_email_verified,
            }
        )


def _oauth_error(message: str, status_code=status.HTTP_400_BAD_REQUEST):
    return Response({"error": message}, status=status_code)


class GoogleOAuthPKCEView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [OAuthThrottle]

    def post(self, request):
        serializer = GoogleOAuthSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        cid = getattr(settings, "GOOGLE_OAUTH_CLIENT_ID", "") or ""
        secret = getattr(settings, "GOOGLE_OAUTH_CLIENT_SECRET", "") or ""
        if not cid or not secret:
            return _oauth_error("Google OAuth is not configured.", status.HTTP_503_SERVICE_UNAVAILABLE)

        data = serializer.validated_data
        try:
            token_payload = exchange_google_code(
                code=data["code"],
                code_verifier=data["code_verifier"],
                redirect_uri=data["redirect_uri"],
                client_id=cid,
                client_secret=secret,
            )
        except Exception as e:
            logger.warning("Google token exchange failed: %s", e)
            return _oauth_error("Google sign-in failed.")

        access_token = token_payload.get("access_token")
        if not access_token:
            return _oauth_error("Google did not return an access token.")

        try:
            info = google_userinfo(access_token)
        except Exception as e:
            logger.warning("Google userinfo failed: %s", e)
            return _oauth_error("Could not load Google profile.")

        if not info.get("email_verified", True):
            return _oauth_error("Google email is not verified.")

        email = info.get("email")
        if not email:
            return _oauth_error("Google account has no email.")

        sub = info.get("sub")
        if not sub:
            return _oauth_error("Google account identifier missing.")

        user_doc = user_manager.upsert_oauth_user(
            email,
            info.get("given_name") or "",
            info.get("family_name") or "",
            "google",
            str(sub),
        )
        proxy = MongoUser(user_doc)
        refresh = RefreshToken.for_user(proxy)
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "firstName": user_doc.get("firstName", ""),
                "lastName": user_doc.get("lastName", ""),
                "role": proxy.role,
                "email_verified": proxy.is_email_verified,
            }
        )


class GitHubOAuthPKCEView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [OAuthThrottle]

    def post(self, request):
        serializer = GitHubOAuthSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        cid = getattr(settings, "GITHUB_OAUTH_CLIENT_ID", "") or ""
        secret = getattr(settings, "GITHUB_OAUTH_CLIENT_SECRET", "") or ""
        if not cid or not secret:
            return _oauth_error("GitHub OAuth is not configured.", status.HTTP_503_SERVICE_UNAVAILABLE)

        data = serializer.validated_data
        try:
            token_payload = exchange_github_code(
                code=data["code"],
                code_verifier=data["code_verifier"],
                redirect_uri=data["redirect_uri"],
                client_id=cid,
                client_secret=secret,
            )
        except Exception as e:
            logger.warning("GitHub token exchange failed: %s", e)
            return _oauth_error("GitHub sign-in failed.")

        access_token = token_payload.get("access_token")
        if not access_token:
            return _oauth_error("GitHub did not return an access token.")

        try:
            profile = github_profile(access_token)
            email, verified = github_primary_email(access_token)
        except Exception as e:
            logger.warning("GitHub profile fetch failed: %s", e)
            return _oauth_error("Could not load GitHub profile.")

        if not email:
            return _oauth_error(
                "No verified email on GitHub. Add a verified email to your GitHub account.",
            )
        if not verified:
            return _oauth_error("GitHub email is not verified.")

        sub = str(profile.get("id") or "")
        if not sub:
            return _oauth_error("GitHub user id missing.")

        name = (profile.get("name") or "").split(None, 1)
        first = name[0] if name else ""
        last = name[1] if len(name) > 1 else ""

        user_doc = user_manager.upsert_oauth_user(
            email,
            first,
            last,
            "github",
            sub,
        )
        proxy = MongoUser(user_doc)
        refresh = RefreshToken.for_user(proxy)
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "firstName": user_doc.get("firstName", ""),
                "lastName": user_doc.get("lastName", ""),
                "role": proxy.role,
                "email_verified": proxy.is_email_verified,
            }
        )


class UserAvatarView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        doc = user_manager.get_user_by_id(request.user.id)
        if not doc or not doc.get("avatar_file_id"):
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            grid_out = user_manager.avatar_bucket().open_download_stream(doc["avatar_file_id"])
            content_type = (grid_out.metadata or {}).get("contentType", "application/octet-stream")
            # Buffered: avatars are ≤3 MB; avoids ASGI sync-iterator warning on FileResponse.
            body = grid_out.read()
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return HttpResponse(body, content_type=content_type)

    def post(self, request):
        upload = request.FILES.get("file")
        if not upload:
            return Response({"error": "Missing file field 'file'."}, status=status.HTTP_400_BAD_REQUEST)
        content_type = upload.content_type or ""
        if content_type not in _ALLOWED_AVATAR_TYPES:
            return Response(
                {"error": f"Unsupported type. Allowed: {', '.join(sorted(_ALLOWED_AVATAR_TYPES))}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if upload.size and upload.size > _MAX_AVATAR_BYTES:
            return Response({"error": "File too large (max 3 MB)."}, status=status.HTTP_400_BAD_REQUEST)

        uid = ObjectId(request.user.id)
        user_manager.remove_avatar_file(uid)

        bucket = user_manager.avatar_bucket()
        file_id = bucket.upload_from_stream(
            upload.name or "avatar",
            upload,
            metadata={"user_id": str(uid), "contentType": content_type},
        )
        user_manager.set_avatar(uid, file_id)
        rel = reverse("core:user_avatar")
        return Response(
            {
                "message": "Avatar updated.",
                "avatar_url": request.build_absolute_uri(rel),
            }
        )

    def delete(self, request):
        try:
            uid = ObjectId(request.user.id)
        except InvalidId:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        user_manager.remove_avatar_file(uid)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AccountDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        try:
            uid = ObjectId(request.user.id)
        except InvalidId:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        user_manager.soft_delete_user(uid)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminSetUserRoleView(APIView):
    permission_classes = [IsAuthenticated, IsRoleAdmin]

    def post(self, request):
        serializer = AdminSetUserRoleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        email = serializer.validated_data["email"]
        role = normalize_role(serializer.validated_data["role"])
        doc = user_manager.get_user_by_email(email)
        if not doc:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        user_manager.users_collection.update_one(
            {"_id": doc["_id"]},
            {"$set": {"role": role, "updated_at": datetime.now(timezone.utc)}},
        )
        return Response({"message": "Role updated.", "email": email, "role": role})
