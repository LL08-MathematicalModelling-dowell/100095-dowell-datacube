from django.urls import path, re_path
from rest_framework_simplejwt.views import TokenRefreshView

# Import page rendering views
from .views.page_views import (
    DashboardOverviewPageView,
    DashboardAPIKeysPageView,
    DashboardBillingPageView,
    DashboardDatabaseDetailPageView,
)

# Import API data views
from .views.api_views import (
    UserStatsAPIView,
    APIKeyAPIView,
    DatabaseDetailAPIView,
)

# Import original auth views
from .views.auth_views import (
    RegistrationView,
    LoginView,
    UserProfileView,
    EmailVerificationView
)

app_name = "core"

urlpatterns = [
    # --- Authentication API Endpoints ---
    re_path(r'^register/?$', RegistrationView.as_view(), name='register'),
    re_path(r'^login/?$', LoginView.as_view(), name='login'),
    re_path(r'^token/refresh/?$', TokenRefreshView.as_view(), name='token_refresh'),
    re_path(r'^verify-email/(?P<token>[^/]+)/?$', EmailVerificationView.as_view(), name='email-verify'),
    re_path(r'^profile/?$', UserProfileView.as_view(), name='user_profile'),

    # This captures the database ID from the URL and passes it to the view
    path('dashboard/database/<str:db_id>/', DashboardDatabaseDetailPageView.as_view(), name='dashboard_database_detail'),

    path('api/v1/database/<str:db_id>/', DatabaseDetailAPIView.as_view(), name='api_database_detail'),

    # --- Dashboard Page Rendering URLs ---
    path('dashboard/overview/', DashboardOverviewPageView.as_view(), name='dashboard_overview'),
    path('dashboard/api-keys/', DashboardAPIKeysPageView.as_view(), name='dashboard_api_keys'),
    path('dashboard/billing/', DashboardBillingPageView.as_view(), name='dashboard_billing'),

    # --- Dashboard API Data Endpoints ---
    path('api/v1/dashboard/stats/', UserStatsAPIView.as_view(), name='api_dashboard_stats'),
    path('api/v1/keys/', APIKeyAPIView.as_view(), name='api_keys_list_create'),
    path('api/v1/keys/<str:key_id>/', APIKeyAPIView.as_view(), name='api_key_delete'),
]



# # 1. Import re_path
# from django.urls import path, re_path
# from rest_framework_simplejwt.views import TokenRefreshView
# from .views.auth_views import EmailVerificationView, RegistrationView, LoginView, StripeWebhookView, UserProfileView, APIKeyView
# from .views import dashboard_views, billing_views

# app_name = "core"

# urlpatterns = [
#     # User account management (all handle POST)
#     re_path(r'^register/?$', RegistrationView.as_view(), name='register'),
#     re_path(r'^login/?$', LoginView.as_view(), name='login'),
#     re_path(r'^token/refresh/?$', TokenRefreshView.as_view(), name='token_refresh'),
    
#     # This is GET only, but we can use re_path for consistency
#     re_path(r'^profile/?$', UserProfileView.as_view(), name='user_profile'),

#     # API Key management
#     # Handles GET and POST, so re_path is needed for the POST
#     re_path(r'^keys/?$', APIKeyView.as_view(), name='api-key-list-create'),
    
#     # Handles DELETE, so re_path is needed. This one captures the key_id.
#     # The regex (?P<key_id>[^/]+) is the equivalent of <str:key_id>
#     re_path(r'^keys/(?P<key_id>[^/]+)/?$', APIKeyView.as_view(), name='api-key-delete'),
#     re_path(r'^verify-email/(?P<token>[^/]+)/?$', EmailVerificationView.as_view(), name='email-verify'),
#     path('stripe-webhook-endpoint-9a7b3c/', StripeWebhookView.as_view(), name='stripe-webhook'),


#     # --- Dashboard ---
#     path('dashboard/', dashboard_views.DashboardOverviewView.as_view(), name='dashboard_overview'),
#     path('dashboard/keys/', dashboard_views.DashboardAPIKeysView.as_view(), name='dashboard_api_keys'),
#     path('dashboard/keys/<str:key_id>/', dashboard_views.DashboardAPIKeysView.as_view(), name='dashboard_api_key_delete'),
#     path('dashboard/billing/', dashboard_views.DashboardBillingView.as_view(), name='dashboard_billing'),

#     # --- Billing API ---
#     path('billing/create-checkout-session/', billing_views.CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
#     path('billing/create-portal-session/', billing_views.CreateBillingPortalSessionView.as_view(), name='create-portal-session'),
# ]