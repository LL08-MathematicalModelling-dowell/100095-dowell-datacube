from django.urls import path
from .views import (
    DataCrudView,
    CreateDatabaseView,
    ListCollectionsView,
    AddCollectionView,
    ListDatabasesView,
    DropDatabaseView,
    api_home,
)

app_name = 'api'

urlpatterns = [
    path('', api_home, name='api_home'),
    path('api/crud/', DataCrudView.as_view(), name="crud"),
    path('api/create_database/', CreateDatabaseView.as_view(), name='create_database'),
    path('api/list_collections/', ListCollectionsView.as_view(), name='list_collections'),
    path('api/add_collection/', AddCollectionView.as_view(), name='add_collection'),
    path('api/list_databases/', ListDatabasesView.as_view(), name='list_databases'),
    # path('api/drop_database/', DropDatabaseView.as_view(), name='drop_database'),
]
