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
from api.services.metadata_service import MetadataService


class CreateDatabaseView(BaseAPIView):
    """
    Handles the creation of a new virtual database and its initial collections.
    """
    permission_classes = [IsAuthenticated]

    @property
    def db_svc(self):
        """
        Instantiates the service with the current request's user_id.
        This is called only when a request is made.
        """
        return DatabaseService(user_id=str(self.request.user.pk))

    @property
    def meta_svc(self):
        """
        Instantiates MetadataService with the current request's user_id.
        """
        return MetadataService(user_id=str(self.request.user.pk))

    @BaseAPIView.handle_errors
    def post(self, request):
        # 1. Input Validation
        data = self.validate_serializer(AddDatabasePOSTSerializer, request.data)
        if not data:
            return Response(
                {"success": False, "error": "Invalid input data"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_provided_name = data.get("db_name", "").lower().strip() # type: ignore
        if not user_provided_name:
            return Response(
                {"success": False, "error": "Database name is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 2. Initialize Scoped Services
        meta_svc = self.meta_svc
        db_svc = self.db_svc
        
        # 3. Business Logic: Check for naming collisions
        if meta_svc.exists_db(user_provided_name):
            return Response(
                {"success": False, "error": f"Database '{user_provided_name}' already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. Execution: Create the database and physical collections
        collections = data.get("collections", []) # type: ignore
        if not collections:
            return Response(
                {"success": False, "error": "At least one collection is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        meta, coll_info = db_svc.create_database_with_collections(
            user_provided_name=user_provided_name,
            collections=collections
        )

        return Response({
            "success": True,
            "database": {
                "id": str(meta["_id"]), 
                "name": meta["displayName"]
            },
            "collections": coll_info
        }, status=status.HTTP_201_CREATED)


class AddCollectionView(BaseAPIView):
    """
    View for adding new collections to an existing database.
    Ensures the user owns the target database before provisioning.
    """
    permission_classes = [IsAuthenticated]

    @property
    def db_svc(self):
        """
        Instantiates the service with the current request's user_id.
        This is called only when a request is made.
        """
        return DatabaseService(user_id=str(self.request.user.pk))

    @BaseAPIView.handle_errors
    def post(self, request):
        # 1. Input Validation
        data = self.validate_serializer(AddCollectionPOSTSerializer, request.data)
        if data is None or not data:
            return Response(
                {"success": False, "error": "Invalid input data"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Execution
        try:
            coll_info = self.db_svc.add_collections_with_creation(
                database_id=data.get("database_id"), # type: ignore
                new_cols=data.get("collections") # type: ignore
            )
            
            return Response({
                "success": True,
                "collections": coll_info
            }, status=status.HTTP_201_CREATED)
            
        except PermissionError as e:
            return Response({"success": False, "error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as e:
            return Response({"success": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)