"""URL configuration for the project."""

from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('api/', include('api.urls')),
    path('api/v2/', include('api.urls_v2')),
    path('admin/', admin.site.urls),
    path('core/', include('core.urls')),
    path('analytics/api/v2/', include('analytics.urls')),
]
