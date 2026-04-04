"""
Modernized CRUD operations for MongoDB documents with Integrated Analytics.
Optimized for Django 6.0+ and DRF 3.15+ standards.
"""

import time
from api.services.metadata_service import MetadataService
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

# Analytics tasks
from analytics.tasks import (
    log_db_operation_task,
    log_mongo_detail_task,
    log_slow_query_task,
)


class DataCrudView(BaseAPIView):
    """
    CRUD operations for documents in a user-owned MongoDB collection.
    Includes automated telemetry and quota enforcement.
    """
    permission_classes = [IsAuthenticated]
    
    @property
    def doc_svc(self):
        return DocumentService(user_id=str(self.request.user.pk))
    
    @property
    def metadata_svc(self):
        """
        Stateful service injection: Instantiates the service with the 
        active user's ID for every request.
        """
        return MetadataService(user_id=str(self.request.user.pk))

    def _capture_mongo_analytics(
            self, request, db_id, collection, 
            operation_type, document_count, 
            result=None, start_time=None
        ):
        """
        Helper to send MongoDB-specific analytics asynchronously.
        """
        user_id = str(request.user.pk)
        
        # 1. Database context log
        db_data = {
            "user_id": user_id,
            "db_id": db_id,
            "collection": collection,
            "operation_type": operation_type,
            "document_count": document_count,
            "query_complexity": "simple",  # Can be enhanced based on query depth
        }
        log_db_operation_task.delay(db_data) # type: ignore
        
        # 2. Detailed counts (if result object available)
        if result:
            detail_data = {
                "user_id": user_id,
                "inserted_count": len(result.inserted_ids) if hasattr(result, 'inserted_ids') else None,
                "modified_count": result.modified_count if hasattr(result, 'modified_count') else None,
                "deleted_count": result.deleted_count if hasattr(result, 'deleted_count') else None,
                "returned_documents": document_count if operation_type == 'document_query' else None,
            }
            # Only send if any count is present
            if any(v is not None for v in detail_data.values()):
                log_mongo_detail_task.delay(detail_data) # type: ignore
        
        # 3. Slow query detection (if start_time provided)
        if start_time:
            duration_ms = (time.perf_counter() - start_time) * 1000
            # Dynamic threshold based on operation type
            threshold = 1000
            if operation_type == 'document_query':
                threshold = 500
            elif operation_type in ['bulk_insert', 'data_import']:
                threshold = 5000
            elif operation_type in ['document_update', 'document_deletion']:
                threshold = 1000
            
            if duration_ms > threshold:
                slow_data = {
                    "user_id": user_id,
                    "query_details": {
                        "method": request.method,
                        "path": request.path,
                        "params": dict(request.GET.items()),
                        "operation": operation_type,
                        "collection": collection,
                    },
                    "duration_ms": round(duration_ms, 2),
                    "threshold_ms": threshold,
                    "collection": collection,
                    "db_id": db_id,
                }
                log_slow_query_task.delay(slow_data) # type: ignore

    @BaseAPIView.handle_errors
    async def post(self, request):
        """Create new documents with automatic ownership and quota verification."""
        op_start = time.perf_counter()
        payload = self.validate_serializer(AsyncPostDocumentSerializer, request.data)
        
        # Check quota
        if await self.metadata_svc.check_quota_is_exceeded():
            return Response({"success": False, "message": "Storage quota exceeded."}, status=403)

        db_id = payload["database_id"]
        coll_name = payload["collection_name"]
        docs = payload["documents"]
        doc_count = len(docs)
        
        result = await self.doc_svc.create_docs(
            db_id=db_id,
            coll_name=coll_name,
            docs=docs
        )

        # Capture analytics
        self._capture_mongo_analytics(
            request, db_id, coll_name,
            operation_type="bulk_insert" if doc_count > 1 else "single_insert",
            document_count=doc_count,
            result=result,
            start_time=op_start
        )

        return Response({
            "success": True,
            "inserted_ids": [str(_id) for _id in result.inserted_ids] if result else []
        }, status=status.HTTP_201_CREATED)

    @BaseAPIView.handle_errors
    async def get(self, request):
        """Read documents with structured query validation and paging."""
        op_start = time.perf_counter()
        params = self.validate_serializer(DocumentQuerySerializer, request.query_params)
        
        db_id = params["database_id"]
        coll_name = params["collection_name"]
        page = params.get("page", 1)
        page_size = params.get("page_size", 50)
        
        filt = safe_load_filters(params.get("filters", "{}"))

        total, docs = await self.doc_svc.list_docs(
            db_id, coll_name, filt, page, page_size
        )
        
        # Capture analytics
        self._capture_mongo_analytics(
            request, db_id, coll_name,
            operation_type="document_query",
            document_count=len(docs),
            result=None,  # No result object for queries
            start_time=op_start
        )
        # Also log returned document count via mongo_detail
        detail_data = {
            "user_id": str(request.user.pk),
            "returned_documents": len(docs),
        }
        log_mongo_detail_task.delay(detail_data) # type: ignore

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
        op_start = time.perf_counter()
        payload = self.validate_serializer(UpdateDocumentSerializer, request.data)

        raw_filters = safe_load_filters(payload.get("filters", {}))
        filt = normalize_id_filter(raw_filters)
        db_id = payload["database_id"]
        coll_name = payload["collection_name"]

        result = await self.doc_svc.update_docs(
            db_id=db_id,
            coll_name=coll_name,
            filt=filt,
            update_data=payload["update_data"],
            bulk=payload.get("update_all_fields", False)
        )

        # Count how many documents were updated (estimate from filter complexity)
        # We don't know exact count before update, but we can pass 0 or use result.modified_count
        doc_count = result.modified_count  # This is the number of documents modified

        self._capture_mongo_analytics(
            request, db_id, coll_name,
            operation_type="document_update",
            document_count=doc_count,
            result=result,
            start_time=op_start
        )

        return Response({
            "success": True, 
            "modified_count": result.modified_count
        }, status=status.HTTP_200_OK)

    @BaseAPIView.handle_errors
    async def delete(self, request):
        """Handle soft or hard deletions with unified response count."""
        op_start = time.perf_counter()
        payload = self.validate_serializer(DeleteDocumentSerializer, request.data)

        raw_filters = safe_load_filters(payload.get("filters", {}))
        filt = normalize_id_filter(raw_filters)
        soft_delete = payload.get("soft_delete", True)
        db_id = payload["database_id"]
        coll_name = payload["collection_name"]

        result = await self.doc_svc.delete_docs(
            db_id=db_id,
            coll_name=coll_name,
            filt=filt,
            soft=soft_delete
        )

        affected_count = result.modified_count if soft_delete else result.deleted_count
        self._capture_mongo_analytics(
            request, db_id, coll_name,
            operation_type="document_deletion",
            document_count=affected_count,
            result=result,
            start_time=op_start
        )

        return Response({
            "success": True, 
            "count": affected_count
        }, status=status.HTTP_200_OK)






# """
# Modernized CRUD operations for MongoDB documents with Integrated Analytics.
# Optimized for Django 6.0+ and DRF 3.15+ standards.
# """

# from api.services.metadata_service import MetadataService
# from rest_framework import status
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated

# from api.views.base import BaseAPIView
# from api.serializers import (
#     AsyncPostDocumentSerializer,
#     UpdateDocumentSerializer,
#     DeleteDocumentSerializer,
#     DocumentQuerySerializer,
# )
# from api.utils.mongodb import (
#     safe_load_filters, 
#     jsonify_object_ids, 
#     normalize_id_filter
# )
# from api.services.document_service import DocumentService



# class DataCrudView(BaseAPIView):
#     """
#     CRUD operations for documents in a user-owned MongoDB collection.
#     Includes automated telemetry and quota enforcement.
#     """
#     permission_classes = [IsAuthenticated]
    
#     @property
#     def doc_svc(self):
#         return DocumentService(user_id=str(self.request.user.pk))
    
#     @property
#     def metadata_svc(self):
#         """
#         Stateful service injection: Instantiates the service with the 
#         active user's ID for every request.
#         """
#         return MetadataService(user_id=str(self.request.user.pk))

#     @BaseAPIView.handle_errors
#     async def post(self, request):
#         """Create new documents with automatic ownership and quota verification."""
#         payload = self.validate_serializer(AsyncPostDocumentSerializer, request.data)
        
#         # 1. Decision Gate: Check Quota before heavy lifting
#         # (Assuming check_quota_is_exceeded is implemented in MetadataService)
#         if await self.metadata_svc.check_quota_is_exceeded():
#             return Response({"success": False, "message": "Storage quota exceeded."}, status=403)

#         result = await self.doc_svc.create_docs(
#             db_id=payload["database_id"],
#             coll_name=payload["collection_name"],
#             docs=payload["documents"]
#         )

#         return Response({
#             "success": True,
#             "inserted_ids": [str(_id) for _id in result.inserted_ids] if result else []
#         }, status=status.HTTP_201_CREATED)

#     @BaseAPIView.handle_errors
#     async def get(self, request):
#         """Read documents with structured query validation and paging."""
#         params = self.validate_serializer(DocumentQuerySerializer, request.query_params)
        
#         db_id = params["database_id"]
#         coll_name = params["collection_name"]
#         page = params.get("page", 1)
#         page_size = params.get("page_size", 50)
        
#         filt = safe_load_filters(params.get("filters", "{}"))

#         total, docs = await self.doc_svc.list_docs(
#             db_id, coll_name, filt, page, page_size
#         )
        
#         return Response({
#             "success": True,
#             "data": jsonify_object_ids(docs),
#             "pagination": {
#                 "page": page,
#                 "page_size": page_size,
#                 "total_items": total,
#                 "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0
#             }
#         }, status=status.HTTP_200_OK)

#     @BaseAPIView.handle_errors
#     async def put(self, request):
#         """Update documents using normalized ID filtering."""
#         payload = self.validate_serializer(UpdateDocumentSerializer, request.data)

#         raw_filters = safe_load_filters(payload.get("filters", {}))
#         filt = normalize_id_filter(raw_filters)

#         result = await self.doc_svc.update_docs(
#             db_id=payload["database_id"],
#             coll_name=payload["collection_name"],
#             filt=filt,
#             update_data=payload["update_data"],
#             bulk=payload.get("update_all_fields", False)
#         )

#         return Response({
#             "success": True, 
#             "modified_count": result.modified_count
#         }, status=status.HTTP_200_OK)

#     @BaseAPIView.handle_errors
#     async def delete(self, request):
#         """Handle soft or hard deletions with unified response count."""
#         payload = self.validate_serializer(DeleteDocumentSerializer, request.data)

#         raw_filters = safe_load_filters(payload.get("filters", {}))
#         filt = normalize_id_filter(raw_filters)
#         soft_delete = payload.get("soft_delete", True)

#         result = await self.doc_svc.delete_docs(
#             db_id=payload["database_id"],
#             coll_name=payload["collection_name"],
#             filt=filt,
#             soft=soft_delete
#         )

#         return Response({
#             "success": True, 
#             "count": result.modified_count if soft_delete else result.deleted_count
#         }, status=status.HTTP_200_OK)

