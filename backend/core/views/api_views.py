from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from core.utils.managers import user_manager
from core.utils.authentication import api_key_manager
from api.services.metadata_service import MetadataService
from bson import ObjectId # Import ObjectId to check its type
from datetime import datetime # Import datetime to check its type

# --- A Reusable Helper Function for JSON Conversion ---
def serialize_mongo_document(doc):
    """
    Recursively converts ObjectId and datetime objects in a document to strings.
    """
    if isinstance(doc, list):
        return [serialize_mongo_document(item) for item in doc]
    if isinstance(doc, dict):
        # Create a new dict to avoid modifying the original during iteration
        serialized_doc = {}
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                serialized_doc[key] = str(value)
            elif isinstance(value, datetime):
                serialized_doc[key] = value.isoformat()
            elif isinstance(value, (dict, list)):
                serialized_doc[key] = serialize_mongo_document(value)
            else:
                serialized_doc[key] = value
        return serialized_doc
    return doc


class UserStatsAPIView(APIView):
    """
    Provides statistics and data for the dashboard overview.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user_id = request.user.id
        user_doc = user_manager.get_user_by_id(user_id)
        if not user_doc:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        meta_svc = MetadataService()
        databases = meta_svc.list_databases_for_user(user_id)
        
        # **FIX:** Use the helper function to ensure all data is serializable
        response_data = {
            "usage": user_doc.get("usage", {}),
            "databases": serialize_mongo_document(databases)
        }
        return Response(response_data)


class APIKeyAPIView(APIView):
    """
    Handles JSON requests for listing, creating, and revoking API keys.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Returns a JSON list of the user's API keys."""
        user_id = request.user.id
        keys = api_key_manager.get_keys_for_user(user_id)
        
        # **FIX:** Use the helper function to serialize the list of key documents
        serialized_keys = serialize_mongo_document(keys)

        return Response(serialized_keys)

    # ... (post and delete methods remain the same as they don't return complex documents) ...
    def post(self, request, *args, **kwargs):
        """Creates a new API key."""
        key_name = request.data.get('name')
        if not key_name or not key_name.strip():
            return Response({"error": "A non-empty 'name' for the key is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        new_key = api_key_manager.generate_key(request.user.id, key_name.strip())
        
        return Response({
            "key": new_key,
            "name": key_name.strip()
        }, status=status.HTTP_201_CREATED)

    def delete(self, request, key_id, *args, **kwargs):
        """Revokes an API key."""
        was_deleted = api_key_manager.revoke_key(key_id, request.user.id)
        if was_deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"error": "Key not found or permission denied."}, status=status.HTTP_404_NOT_FOUND)
        

class DatabaseDetailAPIView(APIView):
    """
    Provides detailed information and aggregated stats for a single database as JSON.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, db_id, *args, **kwargs):
        user_id = request.user.id
        meta_svc = MetadataService()

        database_meta = meta_svc.get_by_id_for_user(db_id, user_id)
        if not database_meta:
            return Response({"error": "Database not found or permission denied."}, status=status.HTTP_404_NOT_FOUND)

        # This list contains actual collections with document counts
        live_collections = meta_svc.list_collections_for_user(db_id, user_id)

        # 1. Get the schema definitions from the metadata
        schema_collections = {c['name']: c for c in database_meta.get('collections', [])}

        # 2. Enrich the live_collections list with the field count from the schema
        for collection in live_collections:
            schema = schema_collections.get(collection['name'])
            collection['field_count'] = len(schema['fields']) if schema else 0

        # 3. Calculate top-level stats
        stats = {
            "collection_count": len(live_collections),
            "total_fields": sum(c.get('field_count', 0) for c in live_collections)
        }
        
        # exclude the collections field from the database_meta dictionary
        database_data = serialize_mongo_document(database_meta)
        database_info = {
            "_id": database_data.get("_id"),
            "user_id": database_data.get("user_id"),
            "displayName": database_data.get("displayName"),
            "dbName": database_data.get("dbName")
        }
        
        response_data = {
            'database': database_info,
            'collections': serialize_mongo_document(live_collections),
            'stats': stats # Add the new stats object to the response
        }
        
        return Response(response_data)