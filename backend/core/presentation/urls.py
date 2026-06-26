from django.urls import path, re_path

from .views.api_views import (
    UserStatsAPIView,
    APIKeyAPIView,
    DatabaseDetailAPIView,
)

from .views.auth_views import (
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RegistrationView,
    LoginView,
    ResendVerificationEmailView,
    UserProfileView,
    EmailVerificationView,
    TokenRefreshView,
    DemoLoginView,
)

from .views.auth_extended import (
    AccountDeleteView,
    AdminSetUserRoleView,
    EmailOnlyRegistrationView,
    GitHubOAuthPKCEView,
    GoogleOAuthPKCEView,
    OtpRequestView,
    OtpVerifyView,
    UserAvatarView,
)

from .views.playground_views import PlaygroundStartView


app_name = "core"

urlpatterns = [
    # --- Authentication API Endpoints ---
    re_path(r"^register/?$", RegistrationView.as_view(), name="register"),
    re_path(r"^auth/register/email-only/?$", EmailOnlyRegistrationView.as_view(), name="register_email_only"),
    re_path(r"^auth/otp/request/?$", OtpRequestView.as_view(), name="otp_request"),
    re_path(r"^auth/otp/verify/?$", OtpVerifyView.as_view(), name="otp_verify"),
    re_path(r"^auth/oauth/google/?$", GoogleOAuthPKCEView.as_view(), name="oauth_google"),
    re_path(r"^auth/oauth/github/?$", GitHubOAuthPKCEView.as_view(), name="oauth_github"),
    re_path(r"^login/?$", LoginView.as_view(), name="login"),
    re_path(r"^auth/token/refresh/?$", TokenRefreshView.as_view(), name="token_refresh"),
    # Must be before verify-email/<token>/ — otherwise "resend" is captured as the token.
    re_path(r"^verify-email/resend/?$", ResendVerificationEmailView.as_view(), name="resend_verification"),
    re_path(r"^verify-email/(?P<token>[^/]+)/?$", EmailVerificationView.as_view(), name="email-verify"),
    re_path(r"^profile/?$", UserProfileView.as_view(), name="user_profile"),
    re_path(r"^profile/avatar/?$", UserAvatarView.as_view(), name="user_avatar"),
    re_path(r"^account/?$", AccountDeleteView.as_view(), name="account_delete"),
    # --- Dashboard API Data Endpoints ---
    path("api/v1/database/<str:db_id>/", DatabaseDetailAPIView.as_view(), name="api_database_detail"),
    re_path(r"^api/v1/dashboard/stats/?$", UserStatsAPIView.as_view(), name="api_dashboard_stats"),
    re_path(r"^api/v1/keys/?$", APIKeyAPIView.as_view(), name="api_keys_list_create"),
    re_path(r"^api/v1/keys/(?P<key_id>[^/]+)/?$", APIKeyAPIView.as_view(), name="api_key_delete"),
    re_path(r"^password-reset/request/?$", PasswordResetRequestView.as_view(), name="password_reset_request"),
    re_path(r"^password-reset/confirm/?$", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    re_path(r"^admin/users/role/?$", AdminSetUserRoleView.as_view(), name="admin_set_user_role"),
]

urlpatterns += [
    re_path(r"^api/v2/demo/login/?$", DemoLoginView.as_view(), name="demo_login"),
    re_path(r"^api/v2/playground/start/?$", PlaygroundStartView.as_view(), name="playground_start"),
]
