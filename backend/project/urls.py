"""URL configuration for the project."""

from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('api/v2/', include('api.presentation.urls_v2')),
    path('admin/', admin.site.urls),
    path('core/', include('core.presentation.urls')),
    path('analytics/api/v2/', include('analytics.urls')),
]
