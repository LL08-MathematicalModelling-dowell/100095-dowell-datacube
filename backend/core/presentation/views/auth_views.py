import logging
import os

import stripe
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timezone
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenViewBase

from core.infrastructure.authentication import MongoUser, api_key_manager
from core.infrastructure.jwt_serializers import DatacubeTokenRefreshSerializer
from core.infrastructure.jwt_tokens import RefreshToken
from core.infrastructure.managers import user_manager
from core.infrastructure.otp import verify_otp_challenge
from core.infrastructure.user_access import effective_email_verified
from core.infrastructure.auth_throttles import (
    DemoLoginThrottle,
    LoginThrottle,
    PasswordResetThrottle,
    RegisterThrottle,
    TokenRefreshThrottle,
)
from core.presentation.serializers import (
    APIKeySerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ProfilePatchSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)
from core.presentation.views.auth_extended import OTPRequestThrottle, send_otp_email_challenge


logger = logging.getLogger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


class RegistrationView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [RegisterThrottle]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user_doc = serializer.save()
        user_id = user_doc["_id"]

        try:
            customer = stripe.Customer.create(
                email=user_doc["email"],
                name=f"{user_doc['firstName']} {user_doc['lastName']}",
                metadata={"datacube_user_id": str(user_id)},
            )
            user_manager.users_collection.update_one(
                {"_id": user_id},
                {"$set": {"stripe_customer_id": customer.id}},
            )
        except Exception as e:
            logger.warning("Could not create Stripe customer for new user: %s", e, exc_info=True)

        otp_resp = send_otp_email_challenge(user_doc["email"], "register")
        if otp_resp.status_code != status.HTTP_200_OK:
            return otp_resp

        return Response(
            {
                "message": "Registration successful. Check your email for a verification code to activate your account.",
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"error": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_doc = user_manager.get_user_by_email(email)

        if not user_doc or not user_manager.check_password(password, user_doc.get("password")):
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        if not effective_email_verified(user_doc):
            return Response(
                {
                    "error": "Email not verified. Use the verification code sent to your email or request a new code.",
                    "code": "email_unverified",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        proxy_user = MongoUser(user_doc)
        refresh = RefreshToken.for_user(proxy_user)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "firstName": user_doc.get("firstName", ""),
                "lastName": user_doc.get("lastName", ""),
                "role": proxy_user.role,
                "email_verified": proxy_user.is_email_verified,
            }
        )


class TokenRefreshView(TokenViewBase):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [TokenRefreshThrottle]
    serializer_class = DatacubeTokenRefreshSerializer


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetThrottle]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        return send_otp_email_challenge(email, "reset_password")


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]
        user_doc = user_manager.get_user_by_email(email)
        if not user_doc:
            return Response(
                {"error": "Invalid code or email."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not verify_otp_challenge(
            user_id=user_doc["_id"],
            purpose="reset_password",
            code=code,
        ):
            return Response(
                {"error": "Invalid or expired code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_password = serializer.validated_data["password"]
        hashed_password = user_manager.hash_pass(new_password)

        user_manager.users_collection.update_one(
            {"_id": user_doc["_id"]},
            {
                "$set": {
                    "password": hashed_password,
                    "auth_method": "password",
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )

        user_manager.clear_password_reset_token(user_doc["_id"])

        return Response(
            {"message": "Your password has been reset successfully. You can now log in."},
            status=status.HTTP_200_OK,
        )


class ResendVerificationEmailView(APIView):
    """Backward-compatible alias for requesting a registration/verification OTP (no JWT required)."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [OTPRequestThrottle]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response(
                {"email": ["This field is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return send_otp_email_challenge(email, "register")


class EmailVerificationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token):
        user_doc = user_manager.verify_email_token(token)
        if user_doc:
            return Response({"message": "Email verified successfully!"}, status=status.HTTP_200_OK)
        return Response(
            {"error": "Invalid or expired verification link."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        doc = user_manager.get_user_by_id(request.user.id)
        if not doc:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(UserSerializer(doc).data)

    def patch(self, request):
        doc = user_manager.get_user_by_id(request.user.id)
        if not doc:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProfilePatchSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            uid = ObjectId(request.user.id)
        except InvalidId:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        vd = serializer.validated_data
        kw = {}
        if "firstName" in vd:
            kw["first_name"] = vd["firstName"]
        if "lastName" in vd:
            kw["last_name"] = vd["lastName"]
        if kw:
            user_manager.update_profile(uid, **kw)
        doc = user_manager.get_user_by_id(request.user.id)
        return Response(UserSerializer(doc).data)


class APIKeyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        keys = api_key_manager.get_keys_for_user(request.user.id)
        serializer = APIKeySerializer(keys, many=True)
        return Response(serializer.data)

    def post(self, request):
        key_name = request.data.get("name")
        if not key_name:
            return Response(
                {"error": "A 'name' for the key is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_key = api_key_manager.generate_key(request.user.id, key_name)

        return Response(
            {
                "message": "API Key created successfully. Store it securely!",
                "key": new_key,
                "name": key_name,
            },
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request, key_id):
        was_deleted = api_key_manager.revoke_key(key_id, request.user.id)
        if was_deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"error": "Key not found or you do not have permission to delete it."},
            status=status.HTTP_404_NOT_FOUND,
        )


class DemoLoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [DemoLoginThrottle]

    def post(self, request):
        demo_email = getattr(settings, "DEMO_LOGIN_EMAIL", "samanta@dowellresearch.se")
        if getattr(settings, "DEMO_AUTO_ENSURE_USER", False):
            user_doc = user_manager.ensure_verified_demo_user(demo_email)
        else:
            user_doc = user_manager.get_user_by_email(demo_email)
        if not user_doc:
            return Response({"error": "Demo user not found"}, status=404)
        if not effective_email_verified(user_doc):
            return Response(
                {"error": "Demo user must have a verified email in the database."},
                status=status.HTTP_403_FORBIDDEN,
            )
        proxy_user = MongoUser(user_doc)
        refresh = RefreshToken.for_user(proxy_user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "role": proxy_user.role,
            }
        )
