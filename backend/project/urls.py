"""URL configuration for the project."""

from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('', include('api.urls')),
    path('admin/', admin.site.urls),
    path('core/', include('core.urls')),
    path('analytics/', include('analytics.urls')),
]
