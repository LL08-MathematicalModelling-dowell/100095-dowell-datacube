"""JWT refresh/access tokens with role and verification claims."""

from rest_framework_simplejwt.tokens import RefreshToken as BaseRefreshToken


class RefreshToken(BaseRefreshToken):
    """Adds role and email_verified to the access token payload."""

    @classmethod
    def for_user(cls, user):
        token = super().for_user(user)
        token["role"] = getattr(user, "role", "developer")
        token["email_verified"] = bool(getattr(user, "is_email_verified", False))
        return token
