"""
Service for managing database and collection creation.
"""

import time
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.views.base import BaseAPIView
from api.serializers import AddDatabasePOSTSerializer, AddCollectionPOSTSerializer
from api.services.database_service import DatabaseService
from api.services.metadata_service import MetadataService

# Analytics tasks
from analytics.tasks import log_db_operation_task, log_mongo_detail_task, log_slow_query_task


class CreateDatabaseView(BaseAPIView):
    """
    Handles the creation of a new virtual database and its initial collections.
    """
    permission_classes = [IsAuthenticated]

    @property
    def db_svc(self):
        return DatabaseService(user_id=str(self.request.user.pk))

    @property
    def meta_svc(self):
        return MetadataService(user_id=str(self.request.user.pk))

    @BaseAPIView.handle_errors
    async def post(self, request):
        start_time = time.perf_counter()
        
        # 1. Input Validation
        data = self.validate_serializer(AddDatabasePOSTSerializer, request.data)
        if not data:
            return Response(
                {"success": False, "error": "Invalid input data"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_provided_name = data.get("db_name", "").lower().strip()
        if not user_provided_name:
            return Response(
                {"success": False, "error": "Database name is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 2. Initialize Scoped Services
        meta_svc = self.meta_svc
        db_svc = self.db_svc
        
        # 3. Business Logic: Check for naming collisions
        if await meta_svc.exists_db(user_provided_name):
            return Response(
                {"success": False, "error": f"Database '{user_provided_name}' already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. Execution: Create the database and physical collections
        collections = data.get("collections", [])
        if not collections:
            return Response(
                {"success": False, "error": "At least one collection is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        meta, coll_info = await db_svc.create_database_with_collections(
            user_provided_name=user_provided_name,
            collections=collections
        )

        # --- Analytics Capture ---
        user_id = str(request.user.pk)
        db_id = str(meta["_id"])
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        # 1. Database operation log
        db_op_data = {
            "user_id": user_id,
            "db_id": db_id,
            "collection": "system",  # No specific collection
            "operation_type": "database_creation",
            "document_count": 0,
            "query_complexity": "simple",
        }
        log_db_operation_task.delay(db_op_data) # type: ignore
        
        # 2. Collection creation details (optional)
        for coll_name in coll_info:
            coll_op_data = {
                "user_id": user_id,
                "db_id": db_id,
                "collection": coll_name,
                "operation_type": "collection_creation",
                "document_count": 0,
                "query_complexity": "simple",
            }
            log_db_operation_task.delay(coll_op_data) # type: ignore
        
        # 3. Mongo detail: number of collections created
        detail_data = {
            "user_id": user_id,
            "modified_count": len(coll_info),  # collections created
        }
        log_mongo_detail_task.delay(detail_data) # type: ignore
        
        # 4. Slow query detection (threshold 2000ms for DB creation)
        if duration_ms > 2000:
            slow_data = {
                "user_id": user_id,
                "query_details": {
                    "method": "POST",
                    "path": request.path,
                    "db_name": user_provided_name,
                    "collection_count": len(collections),
                },
                "duration_ms": round(duration_ms, 2),
                "threshold_ms": 2000,
                "collection": "system",
                "db_id": db_id,
            }
            log_slow_query_task.delay(slow_data) # type: ignore

        return Response({
            "success": True,
            "database": {
                "id": db_id, 
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
        return DatabaseService(user_id=str(self.request.user.pk))

    @BaseAPIView.handle_errors
    async def post(self, request):
        start_time = time.perf_counter()
        
        # 1. Input Validation
        data = self.validate_serializer(AddCollectionPOSTSerializer, request.data)
        if data is None or not data:
            return Response(
                {"success": False, "error": "Invalid input data"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Execution
        try:
            coll_info = await self.db_svc.add_collections_with_creation(
                database_id=data.get("database_id"), # type: ignore
                new_cols=data.get("collections") # type: ignore
            )
            
            # --- Analytics Capture ---
            user_id = str(request.user.pk)
            db_id = data.get("database_id")
            duration_ms = (time.perf_counter() - start_time) * 1000
            collections_created = len(coll_info)
            
            # 1. Log each collection creation
            for coll_name in coll_info:
                coll_op_data = {
                    "user_id": user_id,
                    "db_id": db_id,
                    "collection": coll_name,
                    "operation_type": "collection_creation",
                    "document_count": 0,
                    "query_complexity": "simple",
                }
                log_db_operation_task.delay(coll_op_data) # type: ignore
            
            # 2. Mongo detail: number of collections added
            if collections_created > 0:
                detail_data = {
                    "user_id": user_id,
                    "modified_count": collections_created,
                }
                log_mongo_detail_task.delay(detail_data) # type: ignore
            
            # 3. Slow query detection (threshold 1000ms for adding collections)
            if duration_ms > 1000:
                slow_data = {
                    "user_id": user_id,
                    "query_details": {
                        "method": "POST",
                        "path": request.path,
                        "db_id": db_id,
                        "collection_names": coll_info,
                    },
                    "duration_ms": round(duration_ms, 2),
                    "threshold_ms": 1000,
                    "collection": "system",
                    "db_id": db_id,
                }
                log_slow_query_task.delay(slow_data)  # type: ignore
            
            return Response({
                "success": True,
                "collections": coll_info
            }, status=status.HTTP_201_CREATED)
            
        except PermissionError as e:
            return Response({"success": False, "error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as e:
            return Response({"success": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

