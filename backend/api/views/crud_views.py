"""
Modernized CRUD operations for MongoDB documents.
Optimized for Django 6.0+ and DRF 3.15+ standards.
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.views.base import BaseAPIView
from api.serializers import (
    AsyncPostDocumentSerializer,
    UpdateDocumentSerializer,
    DeleteDocumentSerializer,
    DocumentQuerySerializer,
)
from api.utils.mongodb import (
    safe_load_filters, 
    jsonify_object_ids, 
    normalize_id_filter
)
from api.services.document_service import DocumentService


class DataCrudView(BaseAPIView):
    """
    CRUD operations for documents in a user-owned MongoDB collection.
    
    This view leverages the handle_errors decorator to eliminate repetitive 
    try-except blocks, maintaining a clean 'happy path' logic.
    """
    permission_classes = [IsAuthenticated]
    
    @property
    def doc_svc(self):
        """
        Instantiates the service with the current request's user_id.
        This is called only when a request is made.
        """
        return DocumentService(user_id=str(self.request.user.pk))

    @BaseAPIView.handle_errors
    async def post(self, request):
        """Create new documents with automatic ownership verification."""
        payload = self.validate_serializer(AsyncPostDocumentSerializer, request.data)

        result = await self.doc_svc.create_docs(
            db_id=payload["database_id"],
            coll_name=payload["collection_name"],
            docs=payload["documents"]
        )

        return Response({
            "success": True,
            "inserted_ids": [str(_id) for _id in result.inserted_ids] if result else []
        }, status=status.HTTP_201_CREATED)

    @BaseAPIView.handle_errors
    async def get(self, request):
        """Read documents with structured query validation and paging."""
        user_id = request.user.id
        
        # 1. Validate query params using a serializer instead of manual get() calls
        params = self.validate_serializer(DocumentQuerySerializer, request.query_params)
        
        db_id = params["database_id"]
        coll_name = params["collection_name"]
        page = params.get("page", 1)
        page_size = params.get("page_size", 50)
        
        # 2. Process filters safely
        filt = safe_load_filters(params.get("filters", "{}"))

            
        # 3. Service call
        total, docs = await self.doc_svc.list_docs(
            db_id, coll_name, filt, page, page_size
        )
        
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

    @BaseAPIView.handle_errors
    async def put(self, request):
        """Update documents using normalized ID filtering."""
        payload = self.validate_serializer(UpdateDocumentSerializer, request.data)

        raw_filters = safe_load_filters(payload.get("filters", {}))
        filt = normalize_id_filter(raw_filters)

        result = await self.doc_svc.update_docs(
            db_id=payload["database_id"],
            coll_name=payload["collection_name"],
            filt=filt,
            update_data=payload["update_data"],
            bulk=payload.get("update_all_fields", False)
        )

        return Response({
            "success": True, 
            "modified_count": result.modified_count
        }, status=status.HTTP_200_OK)

    @BaseAPIView.handle_errors
    async def delete(self, request):
        """Handle soft or hard deletions with unified response count."""
        user_id = request.user.id
        payload = self.validate_serializer(DeleteDocumentSerializer, request.data)

        raw_filters = safe_load_filters(payload.get("filters", {}))
        filt = normalize_id_filter(raw_filters)
        soft_delete = payload.get("soft_delete", True)

        result = await self.doc_svc.delete_docs(
            db_id=payload["database_id"],
            coll_name=payload["collection_name"],
            filt=filt,
            soft=soft_delete
        )

        return Response({
            "success": True, 
            "count": result.modified_count if soft_delete else result.deleted_count
        }, status=status.HTTP_200_OK)