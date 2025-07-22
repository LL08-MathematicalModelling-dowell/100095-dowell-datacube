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
# ADDED: Import IsAuthenticated for view protection.
from rest_framework.permissions import IsAuthenticated

from api.views.base import BaseAPIView
from api.serializers import AddDatabasePOSTSerializer, AddCollectionPOSTSerializer
from api.services.database_service import DatabaseService
from api.utils.validators import validate_collection_name, validate_unique_fields
from api.services.metadata_service import MetadataService


class CreateDatabaseView(BaseAPIView):
    # ADDED: This endpoint is now protected. A valid token is required.
    permission_classes = [IsAuthenticated]

    @BaseAPIView.handle_errors
    def post(self, request):
        # ADDED: Get the authenticated user's ID from the request object.
        current_user_id = request.user.id

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
        # CHANGED: Check if the DB exists *for this specific user*.
        if meta_svc.exists_db(name, user_id=current_user_id):
            # CHANGED: More specific error message for a better user experience.
            raise ValueError("A database with this name already exists for your account.")

        db_svc = DatabaseService()
        # CHANGED: Pass the user ID to the service layer for ownership assignment.
        meta, coll_info = db_svc.create_database_with_collections(
            name,
            cols,
            user_id=current_user_id
        )

        return Response({
            "success":     True,
            "database":    {"id": str(meta["_id"]), "name": meta["database_name"]},
            "collections": coll_info
        }, status=status.HTTP_201_CREATED)


class AddCollectionView(BaseAPIView):
    # ADDED: This endpoint is now protected. A valid token is required.
    permission_classes = [IsAuthenticated]

    @BaseAPIView.handle_errors
    def post(self, request):
        # ADDED: Get the authenticated user's ID.
        current_user_id = request.user.id

        data    = self.validate_serializer(AddCollectionPOSTSerializer, request.data)
        db_id   = data["database_id"]
        new_cols= data["collections"]

        # validate names & fields
        for c in new_cols:
            validate_collection_name(c["name"])
            validate_unique_fields(c["fields"])

        db_svc = DatabaseService()
        # CHANGED: Pass the user ID to verify ownership before adding collections.
        coll_info = db_svc.add_collections_with_creation(
            db_id,
            new_cols,
            user_id=current_user_id
        )

        return Response({
            "success":     True,
            "collections": coll_info
        }, status=status.HTTP_201_CREATED)