"""
This file contains the primary API views for database and collection management.

This file has been updated to integrate with the custom authentication system.
Key Changes:
1.  Permission Classes: All data-accessing views are now protected with
    `permission_classes = [IsAuthenticated]`, requiring a valid JWT or API Key.
    Public-facing views like the homepage and health check use `AllowAny`.
2.  User-Scoped Operations: In every protected view, the authenticated user's ID
    is retrieved from `request.user.id` and passed to the service layer.
3.  Secure Service Calls: All calls to the MetadataService (e.g., get_by_id,
    drop_database) have been replaced with their user-aware counterparts
    (e.g., get_by_id_for_user, drop_database(user_id=...)). This enforces
    ownership at every step.
4.  Refactoring for Security: `ListDatabasesView` has been changed from a POST
    to a GET request to follow REST conventions and to remove the insecure
    pattern of accepting an arbitrary filter object from the client.
"""

import os
import json
from bson import ObjectId
from django.conf import settings
from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
# ADDED: Import permissions for securing views.
from rest_framework.permissions import IsAuthenticated, AllowAny

from api.views.base import BaseAPIView
from api.services.metadata_service import MetadataService
from api.utils.validators import sanitize_name
# REMOVED: ListDatabasesPOSTSerializer is no longer used.
from api.serializers import JSonImportSerializer

# logger = __import__('logging').getLogger('database_operations')
meta_svc = MetadataService()


class ApiHomeView(BaseAPIView):
    """Renders the API homepage with endpoint docs."""
    # ADDED: Explicitly mark this view as public.
    permission_classes = [AllowAny]

    def get(self, request):
        """ GET /api/home"""
        from api.api_home_data import apis
        return render(request, "api_home.html", {"apis": apis})


class ListDatabasesView(BaseAPIView):
    """List databases owned by the authenticated user with pagination and search."""
    # ADDED: This endpoint is now protected.
    permission_classes = [IsAuthenticated]

    # REFACTORED: Changed from POST to GET to follow REST best practices for listing resources.
    @BaseAPIView.handle_errors
    def get(self, request):
        """
        GET /api/v1/database/list
        Query Params:
        - page (int, default: 1)
        - page_size (int, default: 10)
        - search (str, optional): A search term to filter databases by name.
        """
        # ADDED: Get the authenticated user's ID.
        user_id = request.user.id

        # 1) Get and validate query parameters
        try:
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 10))
        except (ValueError, TypeError):
            return Response({"error": "Page and page_size must be integers."}, status=400)
        
        search_term = request.query_params.get('search', None)

        # 2) Get paged metadata docs using the new secure, user-aware method.
        total, basic_list = meta_svc.list_databases_paginated_for_user(
            user_id=user_id,
            page=page,
            page_size=page_size,
            search_term=search_term
        )

        # 3) Enrich with real-time collection counts (this logic remains the same).
        client = settings.MONGODB_CLIENT
        enriched = []
        for item in basic_list:
            # We use item['name'] here because that's what the paginated method returns.
            db_name = item["name"]
            try:
                coll_names = client[db_name].list_collection_names()
                item["num_collections"] = len(coll_names)
            except Exception:
                item["num_collections"] = None  # Or 0, depending on desired behavior
            enriched.append(item)

        # 4) Build pagination info.
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

        return Response({
            "success": True,
            "data": enriched,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total,
                "total_pages": total_pages
            }
        }, status=status.HTTP_200_OK)


class ListCollectionsView(BaseAPIView):
    """List all collections for a given database owned by the user."""
    permission_classes = [IsAuthenticated]

    @BaseAPIView.handle_errors
    def get(self, request):
        user_id = request.user.id
        db_id = request.query_params.get("database_id", "").strip()
        if not db_id:
            raise ValueError("database_id is required")

        # CHANGED: Use the secure user-aware method to get collections.
        # This implicitly checks for ownership.
        cols = meta_svc.list_collections_for_user(db_id, user_id)
        return Response({
            "success": True,
            "collections": cols
        }, status=status.HTTP_200_OK)


class DropDatabaseView(BaseAPIView):
    """Drop an entire database owned by the user."""
    permission_classes = [IsAuthenticated]

    @BaseAPIView.handle_errors
    def delete(self, request):
        user_id = request.user.id
        db_id = request.data.get("database_id", "").strip()
        confirmation = request.data.get("confirmation", "").strip()

        if not db_id or not confirmation:
            raise ValueError("database_id and confirmation are required")

        # CHANGED: Call the secure drop_database method with the user_id.
        # This will fail if the user doesn't own the database.
        meta = meta_svc.drop_database(db_id, user_id=user_id)

        db_name = meta["database_name"]
        if confirmation.lower() != db_name.lower():
            raise ValueError("Confirmation does not match database_name")

        settings.MONGODB_CLIENT.drop_database(db_name)

        return Response({"success": True, "message": f"Database '{db_name}' dropped."}, status=status.HTTP_200_OK)


class DropCollectionsView(BaseAPIView):
    """Drop one or more collections from a database owned by the user."""
    permission_classes = [IsAuthenticated]

    @BaseAPIView.handle_errors
    def delete(self, request):
        user_id = request.user.id
        db_id = request.data.get("database_id", "").strip()
        names = request.data.get("collection_names", [])
        if not db_id or not names:
            raise ValueError("database_id and collection_names are required")

        # CHANGED: First, get the database name securely.
        meta = meta_svc.get_by_id_for_user(db_id, user_id)
        if not meta:
            raise PermissionError(f"Database '{db_id}' not found or access denied.")
        db_name = meta["database_name"]

        # CHANGED: Call the secure method to update metadata.
        dropped_meta = meta_svc.drop_collections(db_id, user_id, names)

        # Drop actual collections.
        db = settings.MONGODB_CLIENT[db_name]
        for n in dropped_meta:
            db.drop_collection(n)

        return Response({"success": True, "dropped_collections": dropped_meta}, status=status.HTTP_200_OK)


class GetMetadataView(BaseAPIView):
    """Fetch metadata for a database owned by the user."""
    permission_classes = [IsAuthenticated]

    @BaseAPIView.handle_errors
    def get(self, request):
        user_id = request.user.id
        db_id = request.query_params.get("database_id", "").strip()
        if not db_id:
            raise ValueError("database_id is required")

        # CHANGED: Use the secure method to get metadata.
        meta = meta_svc.get_by_id_for_user(db_id, user_id)
        if not meta:
            return Response({"success": False, "message": "Not found or access denied"}, status=status.HTTP_404_NOT_FOUND)

        def conv(x):
            if isinstance(x, dict): return {k: conv(v) for k, v in x.items()}
            if isinstance(x, list): return [conv(v) for v in x]
            if isinstance(x, ObjectId): return str(x)
            return x

        return Response({"success": True, "data": conv(meta)}, status=status.HTTP_200_OK)


class ImportDataView(BaseAPIView):
    """Import a JSON payload into a collection within a user-owned database."""
    permission_classes = [IsAuthenticated]

    @BaseAPIView.handle_errors
    def post(self, request):
        # ADDED: Get the authenticated user's ID for all operations.
        user_id = request.user.id

        # 1) validate input
        data = self.validate_serializer(JSonImportSerializer, request.data)
        db_id = data["database_id"]
        coll_name = data.get("collection_name")
        json_in = data["json_file"]

        # 2) derive collection name if missing
        if not coll_name:
            filename = os.path.basename(getattr(json_in, "name", "data.json"))
            coll_name = sanitize_name(os.path.splitext(filename)[0])

        # 3) fetch metadata & ensure user owns the DB
        # CHANGED: Use the secure user-aware method.
        meta = meta_svc.get_by_id_for_user(db_id, user_id)
        if not meta:
            raise PermissionError(f"Database '{db_id}' not found or access denied.")
        db_name = meta["database_name"]
        db = settings.MONGODB_CLIENT[db_name]

        # 4) load JSON payload
        raw = json_in.read() if hasattr(json_in, "read") else open(json_in).read()
        docs = json.loads(raw)
        if not isinstance(docs, list):
            docs = [docs]
        
        if not docs:
            return Response({"success": True, "message": "No documents to import."}, status=status.HTTP_200_OK)

        # 5) if collection is new, create it and update metadata
        if coll_name not in db.list_collection_names():
            # a) create the collection
            db.create_collection(coll_name)

            # b) extract top‐level field names from data
            field_names = set().union(*(d.keys() for d in docs))  # union of all doc keys
            fields = [{"name": name, "type": "string"} for name in sorted(field_names)]

            # c) update metadata securely
            # CHANGED: Pass user_id to the secure add_collections method.
            meta_svc.add_collections(
                db_id,
                user_id,
                [{ "name": coll_name, "fields": fields }]
            )

        # 6) insert the documents
        # This operation is implicitly secure because `db` was obtained via a user-owned `meta` doc.
        result = db[coll_name].insert_many(docs)

        return Response({
            "success": True,
            "collection": coll_name,
            "inserted_count": len(result.inserted_ids)
        }, status=status.HTTP_201_CREATED)


class HealthCheck(BaseAPIView):
    """Simple liveness endpoint, public access."""
    # ADDED: Explicitly mark this view as public.
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            "success": True,
            "message": "Server is up"
        }, status=status.HTTP_200_OK)