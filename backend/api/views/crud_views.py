"""CRUD operations for documents in a MongoDB collection."""

from rest_framework import status
from rest_framework.response import Response
from api.views.base import BaseAPIView
from api.serializers import (
    AsyncPostDocumentSerializer,
    UpdateDocumentSerializer,
    DeleteDocumentSerializer,
)
from api.utils.mongodb import safe_load_filters, jsonify_object_ids
from api.services.document_service import DocumentService
from api.utils.decorators import run_async


class DataCrudView(BaseAPIView):
    """CRUD operations for documents in a MongoDB collection."""

    doc_svc = DocumentService()

    @run_async
    @BaseAPIView.handle_errors
    async def post(self, request):
        """Create new documents."""
        payload = self.validate_serializer(AsyncPostDocumentSerializer, request.data)
        try:
            result = await self.doc_svc.create_docs(
                payload["database_id"],
                payload["collection_name"],
                payload["data"]
            )
            return Response({
                "success": True,
                "inserted_ids": [str(_id) for _id in result.inserted_ids]
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                "success": False,
                "message": f"Failed to create documents: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @run_async
    @BaseAPIView.handle_errors
    async def get(self, request):
        """Read documents with paging and Mongo filters."""
        db_id = request.query_params.get("database_id")
        coll_name = request.query_params.get("collection_name")

        if not db_id or not coll_name:
            return Response(
                {"success": False, "message": "Missing required parameters: 'database_id' and/or 'collection_name'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            filt = safe_load_filters(request.query_params.get("filters", "{}"))
        except ValueError as e:
            return Response({"success": False, "message": f"Invalid filters: {str(e)}"}, status=400)

        try:
            page = max(int(request.query_params.get("page", 1)), 1)
            page_size = max(int(request.query_params.get("page_size", 50)), 1)
        except ValueError:
            return Response({
                "success": False,
                "message": "Invalid pagination parameters. 'page' and 'page_size' must be integers."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            total, docs = await self.doc_svc.list_docs(db_id, coll_name, filt, page, page_size)
            return Response({
                "success": True,
                "data": jsonify_object_ids(docs),
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size
                }
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "message": f"Failed to fetch documents: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @run_async
    @BaseAPIView.handle_errors
    async def put(self, request):
        """Update documents by filter."""
        payload = self.validate_serializer(UpdateDocumentSerializer, request.data)

        db_id = payload.get("database_id")
        coll_name = payload.get("collection_name")
        update_data = payload.get("update_data")
        try:
            filt = safe_load_filters(payload.get("filters", {}))
        except ValueError as e:
            return Response({"success": False, "message": f"Invalid filters: {str(e)}"}, status=400)

        if not update_data:
            return Response(
                {"success": False, "message": "Missing 'update_data' field."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = await self.doc_svc.update_docs(db_id, coll_name, filt, update_data)
            return Response({
                "success": True,
                "modified_count": result.modified_count
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "message": f"Failed to update documents: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @run_async
    @BaseAPIView.handle_errors
    async def delete(self, request):
        """Soft or hard delete documents by filter."""
        payload = self.validate_serializer(DeleteDocumentSerializer, request.data)

        db_id = payload.get("database_id")
        coll_name = payload.get("collection_name")
        soft_delete = payload.get("soft_delete", True)

        try:
            filt = safe_load_filters(payload.get("filters", {}))
        except ValueError as e:
            return Response({"success": False, "message": f"Invalid filters: {str(e)}"}, status=400)

        try:
            result = await self.doc_svc.delete_docs(db_id, coll_name, filt, soft_delete)
            count = getattr(result, "deleted_count", None) or getattr(result, "modified_count", 0)
            return Response({
                "success": True,
                "count": count
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "message": f"Failed to delete documents: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
