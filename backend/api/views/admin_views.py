"""Service for managing documents in a MongoDB collection."""

import os
import json

from bson import ObjectId
from django.conf import settings
from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response

from api.views.base import BaseAPIView
from api.services.metadata_service import MetadataService
from api.utils.validators import sanitize_name
from api.serializers import JSonImportSerializer, ListDatabasesPOSTSerializer


# logger = __import__('logging').getLogger('database_operations')
meta_svc = MetadataService()


class ApiHomeView(BaseAPIView):
    """Renders the API homepage with endpoint docs."""
    def get(self, request):
        """ GET /api/home"""
        from api.api_home_data import apis
        return render(request, "api_home.html", {"apis": apis})


class ListDatabasesView(BaseAPIView):
    """
    POST endpoint to list databases with paging, arbitrary Mongo filters,
    AND real–time collection counts.
    """

    @BaseAPIView.handle_errors
    def post(self, request):
        """
        POST /api/v1/database/list
        {
            "page": 1,
            "page_size": 50,
            "filter": {
                "database_name": {"$regex": "^test", "$options": "i"}
            }
        }
        List all databases with optional paging and filtering.
        The filter is a MongoDB query object that can be used to filter the databases by their metadata.
        The page and page_size parameters are used for pagination.
        The page parameter specifies the current page number, and the page_size parameter specifies the number of items per page.
        The response includes the total number of items, the current page number, and the total number of pages.
        The response also includes the list of databases, each with its name and number of collections.
        The number of collections is obtained by querying the MongoDB client for the list of collection names in each database.
        If an error occurs during the process, a 500 Internal Server Error response is returned.
        """
        # 1) validate input
        data = self.validate_serializer(ListDatabasesPOSTSerializer, request.data)
        page = data["page"]
        page_size = data["page_size"]
        filter_doc = data["filter"]

        # 2) get paged metadata docs
        total, basic_list = meta_svc.list_by_filter(filter_doc, page, page_size)

        # 3) enrich with real-time collection counts
        client = settings.MONGODB_CLIENT
        enriched = []
        for item in basic_list:
            db_name = item["database_name"]
            try:
                coll_names = client[db_name].list_collection_names()
                item["num_collections"] = len(coll_names)
            except Exception:
                item["num_collections"] = None
            enriched.append(item)

        # 4) build pagination info
        total_pages = (total + page_size - 1) // page_size

        return Response({
            "success": True,
            "data": enriched,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages
            }
        }, status=status.HTTP_200_OK)


class ListCollectionsView(BaseAPIView):
    """List all collections for a given database."""
    @BaseAPIView.handle_errors
    def get(self, request):
        db_id = request.query_params.get("database_id", "").strip()
        if not db_id:
            raise ValueError("database_id is required")

        cols = meta_svc.list_collections(db_id)
        return Response({
            "success": True,
            "collections": cols
        }, status=status.HTTP_200_OK)


class DropDatabaseView(BaseAPIView):
    """Drop an entire database (metadata + actual)."""

    @BaseAPIView.handle_errors
    def delete(self, request):
        db_id        = request.data.get("database_id", "").strip()
        confirmation = request.data.get("confirmation", "").strip()

        if not db_id or not confirmation:
            raise ValueError("database_id and confirmation are required")

        # remove metadata (returns meta doc)
        meta = meta_svc.drop_database(db_id)

        # ensure confirmation matches
        db_name = meta["database_name"]
        if confirmation.lower() != db_name.lower():
            raise ValueError("confirmation does not match database_name")

        # finally drop the actual Mongo database
        settings.MONGODB_CLIENT.drop_database(db_name)

        return Response({
            "success": True,
            "message": f"Database '{db_name}' dropped."
        }, status=status.HTTP_200_OK)


class DropCollectionsView(BaseAPIView):
    """Drop one or more collections from a database."""

    @BaseAPIView.handle_errors
    def delete(self, request):
        db_id   = request.data.get("database_id", "").strip()
        names   = request.data.get("collection_names", [])
        if not db_id or not names:
            raise ValueError("database_id and collection_names are required")

        # update metadata
        dropped_meta = meta_svc.drop_collections(db_id, names)

        # drop actual collections
        meta = meta_svc.get_by_id(db_id)
        db  = settings.MONGODB_CLIENT[meta["database_name"]]
        for n in dropped_meta:
            db[n].drop()

        return Response({
            "success": True,
            "dropped_collections": dropped_meta
        }, status=status.HTTP_200_OK)


class GetMetadataView(BaseAPIView):
    """Fetch a database’s metadata document via its ID."""

    @BaseAPIView.handle_errors
    def get(self, request):
        db_id = request.query_params.get("database_id", "").strip()
        if not db_id:
            raise ValueError("database_id is required")

        meta = meta_svc.get_by_id(db_id)
        if not meta:
            return Response(
                {"success": False, "message": "Not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # recursively convert ObjectId→str
        def conv(x):
            if isinstance(x, dict):
                return {k: conv(v) for k,v in x.items()}
            if isinstance(x, list):
                return [conv(v) for v in x]
            if isinstance(x, ObjectId):
                return str(x)
            return x

        return Response({"success": True, "data": conv(meta)},
                        status=status.HTTP_200_OK)


class ImportDataView(BaseAPIView):
    """
    Import a JSON payload or file into a collection.
    If collection_name omitted → sanitize(file name).
    If the collection does not exist, extract top‐level fields
    from the data, create it, and update metadata.
    """

    @BaseAPIView.handle_errors
    def post(self, request):
        """
        POST /api/v1/database/import
        {
            "database_id": "...",
            "collection_name": "...",
            "json_file": "data.json"
        }
        Import JSON data into a MongoDB collection.
        The database_id and collection_name must exist in the metadata.
        The json_file can be a file path or a file-like object.
        The collection_name is optional. If not provided, it will be derived from the file name.
        The JSON data must be a valid JSON array or object. If it is an object, it will be wrapped in an array.
        The JSON data will be inserted into the specified collection in the database.
        If the collection does not exist, it will be created and the metadata will be updated.
        The response will include the success status, the collection name, and the number of inserted documents.
        If an error occurs during the process, a 500 Internal Server Error response is returned.
        """
        # 1) validate input
        data = self.validate_serializer(JSonImportSerializer, request.data)
        db_id   = data["database_id"]
        coll    = data.get("collection_name")
        json_in = data["json_file"]

        # 2) derive collection name if missing
        if not coll:
            filename = os.path.basename(getattr(json_in, "name", "data.json"))
            coll = sanitize_name(os.path.splitext(filename)[0])

        # 3) fetch metadata & ensure DB exists
        meta = meta_svc.get_by_id(db_id)
        if not meta:
            raise ValueError(f"Database '{db_id}' not found")
        db_name = meta["database_name"]
        db      = settings.MONGODB_CLIENT[db_name]

        # 4) load JSON payload
        raw = json_in.read() if hasattr(json_in, "read") else open(json_in).read()
        docs = json.loads(raw)
        if not isinstance(docs, list):
            docs = [docs]

        # 5) if collection missing ⇒ create & update metadata
        if coll not in db.list_collection_names():
            # a) create the collection
            db.create_collection(coll)

            # b) extract top‐level field names
            field_names = set().union(*(d.keys() for d in docs))  # union of all doc keys
            fields = [{"name": name, "type": "string"} for name in sorted(field_names)]

            # c) update metadata
            meta_svc.add_collections(db_id, [{
                "name": coll,
                "fields": fields
            }])

        # 6) insert the documents
        result = db[coll].insert_many(docs)

        return Response({
            "success": True,
            "collection": coll,
            "inserted_count": len(result.inserted_ids)
        }, status=status.HTTP_200_OK)


class HealthCheck(BaseAPIView):
    """Simple liveness endpoint."""
    def get(self, request):
        return Response({
            "success": True,
            "message": "Server is up"
        }, status=status.HTTP_200_OK)
    
