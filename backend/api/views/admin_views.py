"""
This file contains the primary API views for database and collection management.
"""

import os
import json
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


class ListDatabasesView(BaseAPIView):
    """List databases owned by the authenticated user."""
    permission_classes = [IsAuthenticated]

    @property
    def metadata_svc(self):
        """
        Stateful service injection: Instantiates the service with the 
        active user's ID for every request.
        """
        return MetadataService(user_id=str(self.request.user.pk))

    @BaseAPIView.handle_errors
    async def get(self, request):
        params = self.validate_serializer(ListQuerySerializer, request.query_params)
        
        total, db_list = await self.metadata_svc.list_databases_paginated(
            page=params['page'],
            page_size=params['page_size'],
            search_term=request.query_params.get('search')
        )

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
        db_id = request.query_params.get("database_id", "").strip()
        if not db_id:
            return Response({"error": "database_id is required"}, status=400)

        # Service already knows the user_id from __init__
        cols = await self.metadata_svc.list_collections_with_live_counts(db_id)
        
        return Response({"success": True, "collections": cols}, status=200)


class DropDatabaseView(BaseAPIView):
    """Drop a user-owned database."""
    permission_classes = [IsAuthenticated]

    @property
    def metadata_svc(self):
        return MetadataService(user_id=str(self.request.user.pk))

    @BaseAPIView.handle_errors
    async def delete(self, request):
        payload = self.validate_serializer(DatabaseDropSerializer, request.data)
        db_id = payload["database_id"]

        # 1. Fetch metadata (ownership verified by user_id in service state)
        meta = await self.metadata_svc.get_db(db_id)
        if not meta:
            return Response({"error": "Unauthorized or not found"}, status=403)

        # 2. Confirmation Check
        if payload["confirmation"].lower() != meta["displayName"].lower():
            return Response({"error": "Confirmation mismatch"}, status=400)
        
        # 3. Drop calls
        await self.metadata_svc.drop_database(db_id)
        await settings.MONGODB_CLIENT.drop_database(meta["dbName"])

        return Response({"success": True, "message": "Dropped."}, status=200)


class DropCollectionsView(BaseAPIView):
    """Drop collections from a user-owned database."""
    permission_classes = [IsAuthenticated]

    @property
    def metadata_svc(self):
        return MetadataService(user_id=str(self.request.user.pk))

    @BaseAPIView.handle_errors
    async def delete(self, request):
        payload = self.validate_serializer(CollectionDropSerializer, request.data)
        db_id = payload["database_id"]

        meta = await self.metadata_svc.get_db(db_id)
        if not meta:
            return Response({"error": "Forbidden"}, status=403)

        # Perform the drop
        dropped_names = await self.metadata_svc.drop_collections(db_id, payload["collection_names"])

        db = await settings.MONGODB_CLIENT[meta["dbName"]]
        for name in dropped_names:
            await db.drop_collection(name)

        return Response({"success": True, "dropped": dropped_names}, status=200)


class GetMetadataView(BaseAPIView):
    """Fetch metadata for a database owned by the authenticated user."""
    permission_classes = [IsAuthenticated]

    @property
    def metadata_svc(self):
        # Injects user_id into service state for secure lookups
        return MetadataService(user_id=str(self.request.user.pk))

    @BaseAPIView.handle_errors
    async def get(self, request):
        """GET /api/v1/database/metadata"""
        db_id = request.query_params.get("database_id", "").strip()
        if not db_id:
            return Response({"error": "database_id is required"}, status=400)

        meta = await self.metadata_svc.get_db(db_id)
        if not meta:
            return Response({
                "success": False, 
                "message": "Database not found or access denied"
            }, status=status.HTTP_404_NOT_FOUND)

        # Using the centralized utility to handle ObjectId serialization
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
        """POST /api/v1/database/import"""
        # 1. Validate payload via Serializer
        data = self.validate_serializer(JsonImportSerializer, request.data)
        db_id = data["database_id"]
        coll_name = data.get("collection_name")
        json_file = data["json_file"]

        # 2. Securely resolve database metadata
        meta = await self.metadata_svc.get_db(db_id)
        if not meta:
            return Response({"error": "Unauthorized database access."}, status=403)
        
        internal_db_name = meta["dbName"]
        db = await settings.MONGODB_CLIENT[internal_db_name]

        # 3. Handle Collection Naming logic
        if not coll_name:
            filename = os.path.basename(getattr(json_file, "name", "data.json"))
            coll_name = sanitize_name(os.path.splitext(filename)[0])

        # 4. Async File Processing
        # In 2025, we use await to read from the uploaded file buffer
        raw_content = json_file.read()
        if hasattr(raw_content, 'decode'):
            raw_content = raw_content.decode('utf-8')
        
        docs = json.loads(raw_content)
        if not isinstance(docs, list):
            docs = [docs]
        
        if not docs:
            return Response({"success": True, "message": "Import payload was empty."}, status=200)

        # 5. Metadata Sync for New Collections
        existing_collections = db.list_collection_names()
        if coll_name not in existing_collections:
            # Infer schema for metadata indexing
            field_names = set().union(*(d.keys() for d in docs))
            fields = [{"name": name, "type": "string"} for name in sorted(field_names)]

            # Service handles the update to the metadata catalog
            await self.metadata_svc.add_collections(
                db_id=db_id,
                new_collections=[{"name": coll_name, "fields": fields}]
            )

        # 6. Bulk Insert
        result = db[coll_name].insert_many(docs)

        return Response({
            "success": True,
            "collection": coll_name,
            "inserted_count": len(result.inserted_ids)
        }, status=status.HTTP_201_CREATED)


class HealthCheck(BaseAPIView):
    """Public health check endpoint for load balancers."""
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            "success": True,
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }, status=status.HTTP_200_OK)
