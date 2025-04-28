"""Service for managing documents in a MongoDB collection."""

from rest_framework import status
from rest_framework.response import Response
from api.views.base import BaseAPIView
from api.services.metadata_service import MetadataService
from api.services.collection_service import CollectionService
from api.utils.decorators import run_async
from api.serializers import AddDatabasePOSTSerializer, AddCollectionPOSTSerializer
from api.utils.validators import validate_collection_name, validate_unique_fields


class CreateDatabaseView(BaseAPIView):
    """Create a new database with collections."""
    @BaseAPIView.handle_errors
    def post(self, request):
        """
        POST /api/v1/database
        {
            "db_name": "my_database",
            "collections": [
                {
                    "name": "my_collection",
                    "fields": [
                        {"name": "field1", "type": "string"},
                        {"name": "field2", "type": "int"}
                    ]
                }
            ]
        }

        Create a new database with the specified name and collections.
        The database name must be unique and the collections must have unique field names.
        The collections can be empty, but at least one collection must be provided.
        """
        data = self.validate_serializer(AddDatabasePOSTSerializer, request.data)
        name = data["db_name"].lower()
        cols = data["collections"]
        if not cols:
            raise ValueError("At least one collection")

        meta_svc = MetadataService()
        if meta_svc.exists_db(name):
            raise ValueError("Already exists")

        # validate
        for c in cols:
            validate_collection_name(c["name"])
            validate_unique_fields(c["fields"])

        # create meta + coll in one transaction
        meta = meta_svc.create_db_meta(name, cols)
        coll_svc = CollectionService(name)
        coll_meta = coll_svc.create(cols)

        return Response({
            "success": True, "database": {"name": name, "id": str(meta["_id"])},
            "collections": coll_meta
        }, status=status.HTTP_201_CREATED)


class AddCollectionView(BaseAPIView):
    """Add collections to an existing database."""
    @BaseAPIView.handle_errors
    def post(self, request):
        """
        POST /api/v1/database/collections
        {
            "database_id": "60d5f484f1c2b8a0b8c8e4d3",
            "collections": [
                {
                    "name": "new_collection",
                    "fields": [
                        {"name": "field1", "type": "string"},
                        {"name": "field2", "type": "int"}
                    ]
                }
            ]
        }

        Add new collections to an existing database.
        The database ID must be valid and the collections must have unique field names.
        The collections can be empty, but at least one collection must be provided.
        """
        data = self.validate_serializer(AddCollectionPOSTSerializer, request.data)
        db_id = data["database_id"]
        new_cols = data["collections"]

        meta_svc = MetadataService()
        meta = meta_svc.get_by_id(db_id)
        if not meta:
            raise ValueError("DB not found")

        existing = {c["name"] for c in meta["collections"]}
        dup = [c["name"] for c in new_cols if c["name"] in existing]
        if dup:
            raise ValueError(f"Duplicate: {', '.join(dup)}")

        for c in new_cols:
            validate_collection_name(c["name"])
            validate_unique_fields(c["fields"])

        # update metadata + create in db
        meta_svc.add_collections(db_id, new_cols)
        coll_meta = CollectionService(meta["database_name"]).create(new_cols)

        return Response({
            "success": True,
            "collections": coll_meta
        }, status=status.HTTP_201_CREATED)
    
