from django.urls import path, re_path

# Import API data views
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
)


app_name = "core"

urlpatterns = [
    # --- Authentication API Endpoints ---
    re_path(r'^register/?$', RegistrationView.as_view(), name='register'),
    re_path(r'^login/?$', LoginView.as_view(), name='login'),
    re_path(r'^auth/token/refresh/?$', TokenRefreshView.as_view(), name='token_refresh'),
    re_path(r'^verify-email/(?P<token>[^/]+)/?$', EmailVerificationView.as_view(), name='email-verify'),
    re_path(r'^profile/?$', UserProfileView.as_view(), name='user_profile'),


    # --- Dashboard API Data Endpoints ---
    path('api/v1/database/<str:db_id>/', DatabaseDetailAPIView.as_view(), name='api_database_detail'),
    re_path(r'^api/v1/dashboard/stats/?$', UserStatsAPIView.as_view(), name='api_dashboard_stats'),
    re_path(r'^api/v1/keys/?$', APIKeyAPIView.as_view(), name='api_keys_list_create'),
    re_path(r'^api/v1/keys/(?P<key_id>[^/]+)/?$', APIKeyAPIView.as_view(), name='api_key_delete'),

    re_path(r'^password-reset/request/?$', PasswordResetRequestView.as_view(), name='password_reset_request'),
    re_path(r'^password-reset/confirm/(?P<token>[^/]+)/?$', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    re_path(r'^verify-email/resend/?$', ResendVerificationEmailView.as_view(), name='resend_verification'),
]
