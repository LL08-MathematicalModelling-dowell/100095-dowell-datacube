"""JWT refresh serializer compatible with Mongo users (no Django User FK)."""

from __future__ import annotations

from typing import Any

from rest_framework import serializers
from rest_framework_simplejwt.exceptions import TokenError

from core.infrastructure.jwt_tokens import RefreshToken


class DatacubeTokenRefreshSerializer(serializers.Serializer):
    """
    Issue a new access token from a refresh token without querying Django's User model.
    Does not use the token blacklist app (OutstandingToken.user requires a Django User).
    """

    refresh = serializers.CharField()
    access = serializers.CharField(read_only=True)

    default_error_messages = {"token_invalid": "Invalid or expired refresh token."}

    def validate(self, attrs: dict[str, Any]) -> dict[str, str]:
        try:
            refresh = RefreshToken(attrs["refresh"])
        except TokenError as e:
            raise serializers.ValidationError(
                {"refresh": self.error_messages["token_invalid"]},
                code="token_invalid",
            ) from e

        access = str(refresh.access_token)
        return {"access": access}
