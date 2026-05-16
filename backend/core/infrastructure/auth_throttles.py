"""DRF throttles for unauthenticated / sensitive auth endpoints."""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class LoginThrottle(AnonRateThrottle):
    scope = "login"


class RegisterThrottle(AnonRateThrottle):
    scope = "register"


class OAuthThrottle(AnonRateThrottle):
    scope = "oauth"


class DemoLoginThrottle(AnonRateThrottle):
    scope = "demo_login"


class PasswordResetThrottle(AnonRateThrottle):
    scope = "password_reset"


class TokenRefreshThrottle(AnonRateThrottle):
    scope = "token_refresh"


class AuthenticatedBurstThrottle(UserRateThrottle):
    """Optional global burst cap for logged-in API users (not applied by default)."""

    scope = "user_burst"
