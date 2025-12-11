"""
Service for managing database and collection creation.

This file has been updated to integrate with the custom authentication system.
Key Changes:
1.  Permission Classes: Both views now require the user to be authenticated
    (using JWT or an API Key) via `permission_classes = [IsAuthenticated]`.
2.  User Ownership: The authenticated user's ID is retrieved from `request.user.id`.
3.  Secure Service Calls: The `user_id` is passed down to the service layer
    (DatabaseService, MetadataService) to ensure all operations are scoped
    to that specific user, preventing data leaks or unauthorized access.
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.views.base import BaseAPIView
from api.serializers import AddDatabasePOSTSerializer, AddCollectionPOSTSerializer
from api.services.database_service import DatabaseService
from api.utils.validators import validate_collection_name, validate_unique_fields
from api.services.metadata_service import MetadataService


class CreateDatabaseView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    @BaseAPIView.handle_errors
    def post(self, request):
        current_user_id = request.user.id

        data = self.validate_serializer(AddDatabasePOSTSerializer, request.data)
        # This is the name the user provided, e.g., "my_project"
        user_provided_name = data["db_name"].lower() 
        cols = data["collections"]
        
        # ... validation ...
        if not cols:
            raise ValueError("At least one collection must be provided")

        # validate
        for c in cols:
            validate_collection_name(c["name"])
            validate_unique_fields(c["fields"])

        meta_svc = MetadataService()
        if meta_svc.exists_db(user_provided_name, user_id=current_user_id):
            raise ValueError("A database with this name already exists for your account.")

        db_svc = DatabaseService()
        meta, coll_info = db_svc.create_database_with_collections(
            user_provided_name,
            cols,
            user_id=current_user_id
        )

        return Response({
            "success":     True,
            "database":    {"id": str(meta["_id"]), "name": meta["displayName"]},
            "collections": coll_info
        }, status=status.HTTP_201_CREATED)


class AddCollectionView(BaseAPIView):
    """View for adding new collections to an existing database."""
    permission_classes = [IsAuthenticated]

    @BaseAPIView.handle_errors
    def post(self, request):
        current_user_id = request.user.id

        data = self.validate_serializer(AddCollectionPOSTSerializer, request.data)
        db_id = data["database_id"]
        new_cols = data["collections"]

        # validate names & fields
        for c in new_cols:
            validate_collection_name(c["name"])
            validate_unique_fields(c["fields"])

        db_svc = DatabaseService()
        coll_info = db_svc.add_collections_with_creation(
            db_id,
            new_cols,
            user_id=current_user_id
        )

        return Response({
            "success":     True,
            "collections": coll_info
        }, status=status.HTTP_201_CREATED)