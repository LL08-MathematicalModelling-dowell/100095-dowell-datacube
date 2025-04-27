"""Service for managing documents in a MongoDB collection."""


from rest_framework import status
from rest_framework.response import Response

from api.views.base import BaseAPIView
from api.serializers import (
    DeleteDocumentSerializer, 
    UpdateDocumentSerializer,
    AsyncPostDocumentSerializer,
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
        """
        Create new documents.
        Body JSON:
        {
           "database_id": "...",
           "collection_name": "...",
           "data": [ {...}, {...}, ... ]
        }
        """
        payload = self.validate_serializer(AsyncPostDocumentSerializer, request.data)
        result  = await self.doc_svc.create_docs(
            payload["database_id"],
            payload["collection_name"],
            payload["data"]
        )
        return Response({
            "success": True,
            "inserted_ids": [str(_id) for _id in result.inserted_ids]
        }, status=status.HTTP_201_CREATED)


    @run_async
    @BaseAPIView.handle_errors
    async def get(self, request):
        """
        Read documents with paging & arbitrary Mongo filters:
        GET /api/crud/?database_id=...&collection_name=...&filters={...}&page=1&page_size=50
        """
        params     = request.query_params
        db_id      = params["database_id"]
        coll_name  = params["collection_name"]
        filt       = safe_load_filters(params.get("filters", "{}"))
        page       = int(params.get("page", 1))
        page_size  = int(params.get("page_size", 50))

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


    @run_async
    @BaseAPIView.handle_errors
    async def put(self, request):
        """
        Update documents by filter:
        PUT /api/crud/
        {
           "database_id": "...",
           "collection_name": "...",
           "filters": { ... },
           "update_data": { ... }
        }
        """
        # body        = request.data
        # validate the request body using the serializer
        body        = self.validate_serializer(UpdateDocumentSerializer, request.data)
        db_id       = body["database_id"]
        coll_name   = body["collection_name"]
        filt        = safe_load_filters(body.get("filters", "{}"))
        update_data = body.get("update_data", {})

        result = await self.doc_svc.update_docs(db_id, coll_name, filt, update_data)
        return Response({
            "success": True,
            "modified_count": result.modified_count
        }, status=status.HTTP_200_OK)


    @run_async
    @BaseAPIView.handle_errors
    async def delete(self, request):
        """
        Delete (or soft‐delete) documents by filter:
        DELETE /api/crud/
        {
           "database_id": "...",
           "collection_name": "...",
           "filters": { ... },
           "soft_delete": true|false
        }
        """
        # validate the request body using the serializer
        body        = self.validate_serializer(DeleteDocumentSerializer, request.data)
        db_id       = body["database_id"]
        coll_name   = body["collection_name"]
        filt        = safe_load_filters(body.get("filters", "{}"))
        soft_delete = body.get("soft_delete", True)

        result = await self.doc_svc.delete_docs(db_id, coll_name, filt, soft_delete)
        # may be delete_many or update_many
        count = getattr(result, "deleted_count", None) or getattr(result, "modified_count", 0)

        return Response({
            "success": True,
            "count": count
        }, status=status.HTTP_200_OK)

