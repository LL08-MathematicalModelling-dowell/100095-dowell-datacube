"""
CRUD operations for documents in a MongoDB collection.

This file has been updated to integrate with the custom authentication system.
Key Changes:
1.  Protected View: The entire `DataCrudView` is now protected with
    `permission_classes = [IsAuthenticated]`, making a valid token mandatory.
2.  User-Scoped Operations: In every method (GET, POST, PUT, DELETE), the
    authenticated user's ID is retrieved from `request.user.id`.
3.  Secure Service Calls: The `user_id` is passed to every corresponding
    method in the `DocumentService`. The service layer uses this ID to verify
    that the user owns the database before performing any action, preventing
    unauthorized access.
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.views.base import BaseAPIView
from api.serializers import (
    AsyncPostDocumentSerializer,
    UpdateDocumentSerializer,
    DeleteDocumentSerializer,
)
from api.utils.mongodb import safe_load_filters, jsonify_object_ids, normalize_id_filter
from api.services.document_service import DocumentService
from api.utils.decorators import run_async


class DataCrudView(BaseAPIView):
    """CRUD operations for documents in a user-owned MongoDB collection."""

    # ADDED: Protect all methods in this view (GET, POST, PUT, DELETE).
    permission_classes = [IsAuthenticated]
    doc_svc = DocumentService()

    @run_async
    @BaseAPIView.handle_errors
    async def post(self, request):
        """Create new documents in a collection owned by the user."""
        # ADDED: Get authenticated user's ID.
        user_id = request.user.id
        payload = self.validate_serializer(AsyncPostDocumentSerializer, request.data)

        try:
            # CHANGED: Pass user_id to the service layer for ownership verification.
            result = await self.doc_svc.create_docs(
                db_id=payload["database_id"],
                coll_name=payload["collection_name"],
                user_id=user_id,
                docs=payload["data"]
            )
            return Response({
                "success": True,
                "inserted_ids": [str(_id) for _id in result.inserted_ids]
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"success": False, "message": f"{e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @run_async
    @BaseAPIView.handle_errors
    async def get(self, request):
        """Read documents from a user-owned collection with paging and Mongo filters."""
        # ADDED: Get authenticated user's ID.
        user_id = request.user.id
        db_id = request.query_params.get("database_id")
        coll_name = request.query_params.get("collection_name")

        if not db_id or not coll_name:
            return Response({"success": False, "message": "Missing 'database_id' and 'collection_name' parameters."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            filt = safe_load_filters(request.query_params.get("filters", "{}"))
            page = max(int(request.query_params.get("page", 1)), 1)
            page_size = max(int(request.query_params.get("page_size", 50)), 1)
        except ValueError as e:
            return Response({"success": False, "message": f"Invalid filters or pagination parameters: {e}"}, status=400)

        try:
            # CHANGED: Pass user_id to the service layer for ownership verification.
            total, docs = await self.doc_svc.list_docs(db_id, coll_name, user_id, filt, page, page_size)

            # filter out documents with "is_deleted": true
            docs = [doc for doc in docs if not doc.get("is_deleted", False)]
            total = len(docs)
            return Response({
                "success": True,
                "data": jsonify_object_ids(docs),
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_items": total,
                    "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0
                }
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": False, "message": f"{e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @run_async
    @BaseAPIView.handle_errors
    async def put(self, request):
        """Update documents by filter in a user-owned collection."""
        # ADDED: Get authenticated user's ID.
        user_id = request.user.id
        payload = self.validate_serializer(UpdateDocumentSerializer, request.data)

        db_id = payload["database_id"]
        coll_name = payload["collection_name"]
        update_data = payload["update_data"]
        update_all_fields = payload.get("update_all_fields", False)

        try:
            raw = safe_load_filters(payload.get("filters", {}))
            filt = normalize_id_filter(raw)
        except ValueError as e:
            return Response({"success": False, "message": f"Invalid filters: {e}"}, status=400)

        if not update_data:
            return Response({"success": False, "message": "Missing 'update_data' field."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # CHANGED: Pass user_id to the service layer for ownership verification.
            result = await self.doc_svc.update_docs(db_id, coll_name, user_id, filt, update_data, update_all_fields)
            return Response({"success": True, "modified_count": result.modified_count}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": False, "message": f"{e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @run_async
    @BaseAPIView.handle_errors
    async def delete(self, request):
        """Soft or hard delete documents by filter in a user-owned collection."""
        # ADDED: Get authenticated user's ID.
        user_id = request.user.id
        payload = self.validate_serializer(DeleteDocumentSerializer, request.data)

        db_id = payload["database_id"]
        coll_name = payload["collection_name"]
        soft_delete = payload.get("soft_delete", True)

        try:
            raw = safe_load_filters(payload.get("filters", {}))
            filt = normalize_id_filter(raw)
        except ValueError as e:
            return Response({"success": False, "message": f"Invalid filters: {e}"}, status=400)

        try:
            # CHANGED: Pass user_id to the service layer for ownership verification.
            result = await self.doc_svc.delete_docs(db_id, coll_name, user_id, filt, soft_delete)
            # Unified count for soft (modified) and hard (deleted) deletes.
            count = result.modified_count if soft_delete else result.deleted_count
            return Response({"success": True, "count": count}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": False, "message": f"{e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)