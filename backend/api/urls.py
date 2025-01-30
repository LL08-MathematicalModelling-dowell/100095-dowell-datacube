"""
URL configuration for the API.
This module defines the URL patterns for the API endpoints, mapping each URL
to the corresponding view. The available endpoints include CRUD operations,
database and collection management, health check, and metadata retrieval.
Available endpoints:
- '' : Home page of the API.
- 'api/crud/' : Endpoint for CRUD operations.
- 'api/create_database/' : Endpoint to create a new database.
- 'api/list_collections/' : Endpoint to list all collections in a database.
- 'api/add_collection/' : Endpoint to add a new collection to a database.
- 'api/list_databases/' : Endpoint to list all databases.
- 'health_check/' : Endpoint to check the health status of the API.
- 'api/get_metadata/' : Endpoint to retrieve metadata.
- 'api/drop_database/' : Endpoint to drop a database.
- 'api/drop_collections/' : Endpoint to drop collections from a database.
Each endpoint is associated with a specific view that handles the request.
"""

from django.urls import path
from .views import (AddCollectionView, CreateDatabaseView, DataCrudView,
                    DropCollectionsView, DropDatabaseView, GetMetadataView,
                    HealthCheck, ListCollectionsView, ListDatabasesView,
                    api_home)


app_name = 'api'

urlpatterns = [
    path('', api_home, name='api_home'),
    path('api/crud/', DataCrudView.as_view(), name="crud"),
    path('api/create_database/', CreateDatabaseView.as_view(), name='create_database'),
    path('api/list_collections/', ListCollectionsView.as_view(), name='list_collections'),
    path('api/add_collection/', AddCollectionView.as_view(), name='add_collection'),
    path('api/list_databases/', ListDatabasesView.as_view(), name='list_databases'),
    path('health_check/', HealthCheck.as_view(), name='health_check'),
    path('api/get_metadata/', GetMetadataView.as_view(), name='get_metadata'),
    path('api/drop_database/', DropDatabaseView.as_view(), name='drop_database'),
    path('api/drop_collections/', DropCollectionsView.as_view(), name='drop_collections'),
]
