from django.urls import path
from .views import (
    DataCrudView,
    CreateDatabaseView, ListCollectionsView,
    AddCollectionView, api_home,
)

app_name = 'api'

urlpatterns = [
    path('', api_home, name='api_home'),
    path('api/crud/', DataCrudView.as_view(), name="crud"),
    path('api/create_database/', CreateDatabaseView.as_view(), name='create_database'),
    path('api/list_collections/', ListCollectionsView.as_view(), name='list_collections'),
    path('api/add_collection/', AddCollectionView.as_view(), name='add_collection'),
]
