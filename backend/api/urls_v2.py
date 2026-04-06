"""URL configuration for the 'api' app, updated to handle optional trailing slashes."""

from django.urls import re_path

from api.views.admin_views import (
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

from api.views.file_views import (
    FileListView,
    FileDetailView,
    FileStreamView,
    FileDownloadView,
)



app_name = "api"

urlpatterns = [
    re_path(r"^create_database/?$", CreateDatabaseView.as_view(), name="create_database"),
    re_path(r"^add_collection/?$",   AddCollectionView.as_view(),    name="add_collection"),
    re_path(r"^list_databases/?$",   ListDatabasesView.as_view(),    name="list_databases"),
    re_path(r"^list_collections/?$", ListCollectionsView.as_view(),  name="list_collections"),
    re_path(r"^get_metadata/?$",     GetMetadataView.as_view(),      name="get_metadata"),
    re_path(r"^drop_database/?$",    DropDatabaseView.as_view(),     name="drop_database"),
    re_path(r"^drop_collections/?$", DropCollectionsView.as_view(),  name="drop_collections"),
    re_path(r"^import_data/?$",      ImportDataView.as_view(),       name="import_data"),

    # CRUD operations - Handles POST, PUT, DELETE, so re_path is critical
    re_path(r"^crud/?$", DataCrudView.as_view(), name="crud"),

    # File operations
     # List and upload files
    re_path(r'^files/$', FileListView.as_view(), name='file-list'),

    # Retrieve metadata or delete a specific file
    re_path(r'^files/(?P<file_id>[a-fA-F0-9]{24})/$', FileDetailView.as_view(), name='file-detail'),

    # Stream a specific file
    re_path(r'^files/stream/(?P<file_id>[a-fA-F0-9]{24})/$', FileStreamView.as_view(), name='file-stream'),
    # Download a specific file (reads entire file into memory - not recommended for large files)
    re_path(r'^files/download/(?P<file_id>[a-fA-F0-9]{24})/$', FileDownloadView.as_view(), name='file-download'),

    # Health check - GET only
    re_path(r"^health_check/?$", HealthCheck.as_view(), name="health_check"),
]