"""
This file contains the primary API views for database and collection management.
"""

import os
import json
import time
from datetime import datetime
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from api.views.base import BaseAPIView
from api.services.metadata_service import MetadataService
from api.utils.validators import sanitize_name
from api.utils.mongodb import jsonify_object_ids
from api.serializers import (
    DatabaseDropSerializer,
    CollectionDropSerializer,
    JsonImportSerializer,
    ListQuerySerializer,
)

# Analytics tasks
from analytics.tasks import (
    log_db_operation_task,
    log_mongo_detail_task,
    log_slow_query_task,
)


class ListDatabasesView(BaseAPIView):
    """List databases owned by the authenticated user."""
    permission_classes = [IsAuthenticated]

    @property
    def metadata_svc(self):
        return MetadataService(user_id=str(self.request.user.pk))

    @BaseAPIView.handle_errors
    async def get(self, request):

        start_time = time.perf_counter()
        params = self.validate_serializer(ListQuerySerializer, request.query_params)
        
        total, db_list = await self.metadata_svc.list_databases_paginated(
            page=params['page'],
            page_size=params['page_size'],
            search_term=request.query_params.get('search')
        )

        # Analytics
        duration_ms = (time.perf_counter() - start_time) * 1000
        user_id = str(request.user.pk)
        db_op_data = {
            "user_id": user_id,
            "db_id": None,
            "collection": "system",
            "operation_type": "database_listing",
            "document_count": total,
            "query_complexity": "simple",
        }
        log_db_operation_task.delay(db_op_data) # type: ignore
        
        detail_data = {
            "user_id": user_id,
            "returned_documents": total,
        }
        log_mongo_detail_task.delay(detail_data) # type: ignore
        
        if duration_ms > 1000:
            slow_data = {
                "user_id": user_id,
                "query_details": {"method": "GET", "path": request.path, "params": dict(request.GET.items())},
                "duration_ms": round(duration_ms, 2),
                "threshold_ms": 1000,
                "collection": "system",
                "db_id": None,
            }
            log_slow_query_task.delay(slow_data) # type: ignore

        return Response({
            "success": True,
            "data": db_list,
            "pagination": {
                "page": params['page'],
                "total_items": total,
                "total_pages": (total + params['page_size'] - 1) // params['page_size']
            }
        }, status=status.HTTP_200_OK)


class ListCollectionsView(BaseAPIView):
    """List collections for a specific database."""
    permission_classes = [IsAuthenticated]

    @property
    def metadata_svc(self):
        return MetadataService(user_id=str(self.request.user.pk))

    @BaseAPIView.handle_errors
    async def get(self, request):
        start_time = time.perf_counter()
        db_id = request.query_params.get("database_id", "").strip()
        if not db_id:
            return Response({"error": "database_id is required"}, status=400)

        cols = await self.metadata_svc.list_collections_with_live_counts(db_id)
        
        # Analytics
        user_id = str(request.user.pk)
        duration_ms = (time.perf_counter() - start_time) * 1000
        db_op_data = {
            "user_id": user_id,
            "db_id": db_id,
            "collection": "system",
            "operation_type": "collection_listing",
            "document_count": len(cols),
            "query_complexity": "simple",
        }
        log_db_operation_task.delay(db_op_data) # type: ignore
        
        detail_data = {"user_id": user_id, "returned_documents": len(cols)}
        log_mongo_detail_task.delay(detail_data) # type: ignore
        
        if duration_ms > 1000:
            slow_data = {
                "user_id": user_id,
                "query_details": {"method": "GET", "path": request.path, "db_id": db_id},
                "duration_ms": round(duration_ms, 2),
                "threshold_ms": 1000,
                "collection": "system",
                "db_id": db_id,
            }
            log_slow_query_task.delay(slow_data) # type: ignore

        return Response({"success": True, "collections": cols}, status=200)


class DropDatabaseView(BaseAPIView):
    """Drop a user-owned database."""
    permission_classes = [IsAuthenticated]

    @property
    def metadata_svc(self):
        return MetadataService(user_id=str(self.request.user.pk))

    @BaseAPIView.handle_errors
    async def delete(self, request):
        start_time = time.perf_counter()
        payload = self.validate_serializer(DatabaseDropSerializer, request.data)
        db_id = payload["database_id"]

        meta = await self.metadata_svc.get_db(db_id)
        if not meta:
            return Response({"error": "Unauthorized or not found"}, status=403)

        if payload["confirmation"].lower() != meta["displayName"].lower():
            return Response({"error": "Confirmation mismatch"}, status=400)
        
        await self.metadata_svc.drop_database(db_id)
        await settings.MONGODB_CLIENT.drop_database(meta["dbName"])

        # Analytics
        user_id = str(request.user.pk)
        duration_ms = (time.perf_counter() - start_time) * 1000
        db_op_data = {
            "user_id": user_id,
            "db_id": db_id,
            "collection": "system",
            "operation_type": "database_deletion",
            "document_count": 1,  # one database dropped
            "query_complexity": "simple",
        }
        log_db_operation_task.delay(db_op_data) # type: ignore
        
        detail_data = {"user_id": user_id, "deleted_count": 1}
        log_mongo_detail_task.delay(detail_data) # type: ignore
        
        if duration_ms > 2000:
            slow_data = {
                "user_id": user_id,
                "query_details": {"method": "DELETE", "path": request.path, "db_id": db_id},
                "duration_ms": round(duration_ms, 2),
                "threshold_ms": 2000,
                "collection": "system",
                "db_id": db_id,
            }
            log_slow_query_task.delay(slow_data) # type: ignore

        return Response({"success": True, "message": "Dropped."}, status=200)


class DropCollectionsView(BaseAPIView):
    """Drop collections from a user-owned database."""
    permission_classes = [IsAuthenticated]

    @property
    def metadata_svc(self):
        return MetadataService(user_id=str(self.request.user.pk))

    @BaseAPIView.handle_errors
    async def delete(self, request):
        start_time = time.perf_counter()
        payload = self.validate_serializer(CollectionDropSerializer, request.data)
        db_id = payload["database_id"]

        meta = await self.metadata_svc.get_db(db_id)
        if not meta:
            return Response({"error": "Forbidden"}, status=403)

        dropped_names = await self.metadata_svc.drop_collections(db_id, payload["collection_names"])
     
        # Analytics
        user_id = str(request.user.pk)
        duration_ms = (time.perf_counter() - start_time) * 1000
        for coll_name in dropped_names:
            db_op_data = {
                "user_id": user_id,
                "db_id": db_id,
                "collection": coll_name,
                "operation_type": "collection_deletion",
                "document_count": 1,
                "query_complexity": "simple",
            }
            log_db_operation_task.delay(db_op_data) # type: ignore
        
        detail_data = {"user_id": user_id, "deleted_count": len(dropped_names)}
        log_mongo_detail_task.delay(detail_data) # type: ignore
        
        if duration_ms > 1500:
            slow_data = {
                "user_id": user_id,
                "query_details": {"method": "DELETE", "path": request.path, "db_id": db_id, "collections": dropped_names},
                "duration_ms": round(duration_ms, 2),
                "threshold_ms": 1500,
                "collection": "system",
                "db_id": db_id,
            }
            log_slow_query_task.delay(slow_data) # type: ignore

        return Response({"success": True, "dropped": dropped_names}, status=200)


class GetMetadataView(BaseAPIView):
    """Fetch metadata for a database owned by the authenticated user."""
    permission_classes = [IsAuthenticated]

    @property
    def metadata_svc(self):
        return MetadataService(user_id=str(self.request.user.pk))

    @BaseAPIView.handle_errors
    async def get(self, request):
        start_time = time.perf_counter()
        db_id = request.query_params.get("database_id", "").strip()
        if not db_id:
            return Response({"error": "database_id is required"}, status=400)

        meta = await self.metadata_svc.get_db(db_id)
        if not meta:
            return Response({
                "success": False, 
                "message": "Database not found or access denied"
            }, status=status.HTTP_404_NOT_FOUND)

        # Analytics
        user_id = str(request.user.pk)
        duration_ms = (time.perf_counter() - start_time) * 1000
        db_op_data = {
            "user_id": user_id,
            "db_id": db_id,
            "collection": "system",
            "operation_type": "metadata_retrieval",
            "document_count": 1,
            "query_complexity": "simple",
        }
        log_db_operation_task.delay(db_op_data) # type: ignore
        
        if duration_ms > 500:
            slow_data = {
                "user_id": user_id,
                "query_details": {"method": "GET", "path": request.path, "db_id": db_id},
                "duration_ms": round(duration_ms, 2),
                "threshold_ms": 500,
                "collection": "system",
                "db_id": db_id,
            }
            log_slow_query_task.delay(slow_data) # type: ignore

        return Response({
            "success": True, 
            "data": jsonify_object_ids(meta)
        }, status=status.HTTP_200_OK)


class ImportDataView(BaseAPIView):
    """Import JSON payload into a user-owned MongoDB collection."""
    permission_classes = [IsAuthenticated]

    @property
    def metadata_svc(self):
        return MetadataService(user_id=str(self.request.user.pk))

    @BaseAPIView.handle_errors
    async def post(self, request):
        start_time = time.perf_counter()
        data = self.validate_serializer(JsonImportSerializer, request.data)
        db_id = data["database_id"]
        coll_name = data.get("collection_name")
        json_file = data["json_file"]

        meta = await self.metadata_svc.get_db(db_id)
        if not meta:
            return Response({"error": "Unauthorized database access."}, status=403)
        
        internal_db_name = meta["dbName"]
        db = settings.MONGODB_CLIENT[internal_db_name]

        if not coll_name:
            filename = os.path.basename(getattr(json_file, "name", "data.json"))
            coll_name = sanitize_name(os.path.splitext(filename)[0])

        raw_content = json_file.read()
        if hasattr(raw_content, 'decode'):
            raw_content = raw_content.decode('utf-8')
        docs = json.loads(raw_content)
        if not isinstance(docs, list):
            docs = [docs]
        
        if not docs:
            return Response({"success": True, "message": "Import payload was empty."}, status=200)

        existing_collections = await db.list_collection_names()
        if coll_name not in existing_collections:
            field_names = set().union(*(d.keys() for d in docs))
            fields = [{"name": name, "type": "string"} for name in sorted(field_names)]
            await self.metadata_svc.add_collections(
                db_id=db_id,
                new_collections=[{"name": coll_name, "fields": fields}]
            )

        result = await db[coll_name].insert_many(docs)
        inserted_count = len(result.inserted_ids)

        # Analytics
        user_id = str(request.user.pk)
        duration_ms = (time.perf_counter() - start_time) * 1000
        db_op_data = {
            "user_id": user_id,
            "db_id": db_id,
            "collection": coll_name,
            "operation_type": "data_import",
            "document_count": inserted_count,
            "query_complexity": "simple",
        }
        log_db_operation_task.delay(db_op_data) # type: ignore
        
        detail_data = {"user_id": user_id, "inserted_count": inserted_count}
        log_mongo_detail_task.delay(detail_data) # type: ignore
        
        if duration_ms > 5000:
            slow_data = {
                "user_id": user_id,
                "query_details": {"method": "POST", "path": request.path, "db_id": db_id, "collection": coll_name, "doc_count": inserted_count},
                "duration_ms": round(duration_ms, 2),
                "threshold_ms": 5000,
                "collection": coll_name,
                "db_id": db_id,
            }
            log_slow_query_task.delay(slow_data) # type: ignore

        return Response({
            "success": True,
            "collection": coll_name,
            "inserted_count": inserted_count
        }, status=status.HTTP_201_CREATED)


class HealthCheck(BaseAPIView):
    """Public health check endpoint for load balancers."""
    permission_classes = [AllowAny]

    def get(self, request):
        # No analytics for health check (low value)

        return Response({
            "success": True,
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }, status=status.HTTP_200_OK)
