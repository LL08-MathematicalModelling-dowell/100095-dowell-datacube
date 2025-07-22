"""URL configuration for the project."""

from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('api.urls')),
    path('api/auth/', include('core.urls')),
]
