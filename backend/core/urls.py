# 1. Import re_path
from django.urls import path, re_path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegistrationView, LoginView, UserProfileView, APIKeyView


urlpatterns = [
    # User account management (all handle POST)
    re_path(r'^register/?$', RegistrationView.as_view(), name='register'),
    re_path(r'^login/?$', LoginView.as_view(), name='login'),
    re_path(r'^token/refresh/?$', TokenRefreshView.as_view(), name='token_refresh'),
    
    # This is GET only, but we can use re_path for consistency
    re_path(r'^profile/?$', UserProfileView.as_view(), name='user_profile'),

    # API Key management
    # Handles GET and POST, so re_path is needed for the POST
    re_path(r'^keys/?$', APIKeyView.as_view(), name='api-key-list-create'),
    
    # Handles DELETE, so re_path is needed. This one captures the key_id.
    # The regex (?P<key_id>[^/]+) is the equivalent of <str:key_id>
    re_path(r'^keys/(?P<key_id>[^/]+)/?$', APIKeyView.as_view(), name='api-key-delete'),
]