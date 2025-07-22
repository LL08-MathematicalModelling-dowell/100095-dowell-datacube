"""Service for managing documents in a MongoDB collection."""


from rest_framework import status
from rest_framework.response import Response

from api.views.base import BaseAPIView
from api.serializers import AddDatabasePOSTSerializer, AddCollectionPOSTSerializer
from api.services.database_service import DatabaseService
from api.utils.validators import validate_collection_name, validate_unique_fields
from api.services.metadata_service import MetadataService


class CreateDatabaseView(BaseAPIView):
    @BaseAPIView.handle_errors
    def post(self, request):
        data = self.validate_serializer(AddDatabasePOSTSerializer, request.data)
        name = data["db_name"].lower()
        cols = data["collections"]
        if not cols:
            raise ValueError("At least one collection must be provided")

        # validate
        for c in cols:
            validate_collection_name(c["name"])
            validate_unique_fields(c["fields"])

        meta_svc = MetadataService()
        if meta_svc.exists_db(name):
            raise ValueError("Database already exists")

        db_svc = DatabaseService()
        meta, coll_info = db_svc.create_database_with_collections(name, cols)

        return Response({
            "success":     True,
            "database":    {"id": str(meta["_id"]), "name": meta["database_name"]},
            "collections": coll_info
        }, status=status.HTTP_201_CREATED)


class AddCollectionView(BaseAPIView):
    @BaseAPIView.handle_errors
    def post(self, request):
        data    = self.validate_serializer(AddCollectionPOSTSerializer, request.data)
        db_id   = data["database_id"]
        new_cols= data["collections"]

        # validate names & fields
        for c in new_cols:
            validate_collection_name(c["name"])
            validate_unique_fields(c["fields"])

        db_svc    = DatabaseService()
        coll_info = db_svc.add_collections_with_creation(db_id, new_cols)

        return Response({
            "success":     True,
            "collections": coll_info
        }, status=status.HTTP_201_CREATED)

