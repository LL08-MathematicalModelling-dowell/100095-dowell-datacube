# api/urls.py

from django.urls import path

from api.views.admin_views import (
    ApiHomeView,
    ListDatabasesView,
    ListCollectionsView,
    DropDatabaseView,
    DropCollectionsView,
    GetMetadataView,
    ImportDataView,
    HealthCheck,
)
from api.views.database_views import (
    CreateDatabaseView,
    AddCollectionView,
)
from api.views.crud_views import DataCrudView

app_name = "api"

urlpatterns = [
    # API homepage (docs)
    path("", ApiHomeView.as_view(), name="api_home"),

    # Database management
    path("api/create_database/", CreateDatabaseView.as_view(), name="create_database"),
    path("api/add_collection/",   AddCollectionView.as_view(),    name="add_collection"),
    path("api/list_databases/",   ListDatabasesView.as_view(),    name="list_databases"),
    path("api/list_collections/", ListCollectionsView.as_view(),  name="list_collections"),
    path("api/get_metadata/",     GetMetadataView.as_view(),      name="get_metadata"),
    path("api/drop_database/",    DropDatabaseView.as_view(),     name="drop_database"),
    path("api/drop_collections/", DropCollectionsView.as_view(),  name="drop_collections"),
    path("api/import_data/",      ImportDataView.as_view(),       name="import_data"),

    # CRUD operations
    path("api/crud/", DataCrudView.as_view(), name="crud"),

    # Health check
    path("health_check/", HealthCheck.as_view(), name="health_check"),
]
