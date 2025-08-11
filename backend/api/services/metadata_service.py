"""
# metadata_service.py
# Service for managing metadata documents in a MongoDB collection.
"""

from bson import ObjectId
from django.conf import settings
from pymongo import ReturnDocument
# from api.utils.decorators import with_transaction


class MetadataService:
    """Service for managing metadata documents in a MongoDB collection."""
    def __init__(self):
        self._coll = settings.METADATA_COLLECTION

    def get_by_id_for_user(self, db_id: str, user_id: str) -> dict | None:
        """Gets a database by its ID, ensuring it belongs to the user."""
        return self._coll.find_one({
            "_id": ObjectId(db_id),
            "user_id": ObjectId(user_id)
        })

    def exists_db(self, user_provided_name: str, user_id: str, *, session=None) -> bool:
        """Checks if a database with that display name exists for a specific user."""
        return bool(self._coll.find_one({
            "displayName": user_provided_name, # <-- Check against the display name
            "user_id": ObjectId(user_id)
        }, session=session))

    def exists_db_by_internal_name(self, internal_name: str, user_id: str, *, session=None) -> bool:
        """Checks if a database with that INTERNAL name exists for a specific user."""
        return bool(self._coll.find_one({
            "dbName": internal_name, # <-- QUERIES THE CORRECT FIELD
            "user_id": ObjectId(user_id)
        }, session=session))

    # This method is for listing, so we should return the user-friendly name
    def list_databases_for_user(self, user_id: str) -> list[dict]:
        user_filter = {"user_id": ObjectId(user_id)}
        # Fetch both the id and the user-friendly name
        projection = {"_id": 1, "displayName": 1}
        docs = list(self._coll.find(user_filter, projection))
        # Use the displayName for the 'name' field in the response
        return [{"id": str(d["_id"]), "name": d["displayName"]} for d in docs]


    def create_db_meta(
        self,
        user_provided_name: str,
        internal_db_name: str, # <-- Added internal name
        collections: list[dict],
        user_id: str,
        *,
        session=None
    ) -> dict:
        """
        Inserts a new metadata document, storing both the user-friendly name
        and the unique internal name.
        """
        meta = {
            "user_id": ObjectId(user_id),
            "displayName": user_provided_name, # <-- User-friendly name for display
            "dbName": internal_db_name,       # <-- Unique internal name for operations
            "collections": [
                {
                    "name": coll["name"],
                    "fields": [
                        {"name": f["name"], "type": f.get("type", "string")}
                        for f in coll["fields"]
                    ]
                }
                for coll in collections
            ],
            # ... other fields
        }
        result = self._coll.insert_one(meta, session=session)
        meta["_id"] = result.inserted_id
        return meta

    # @with_transaction
    def add_collections(
        self, database_id: str, user_id: str, new_collections: list[dict], *, session=None
    ) -> list[dict]:
        """
        Append new collections, ensuring the database belongs to the user.
        """
        # ... (same logic for creating `docs` from new_collections) ...
        docs = [
            {
                "name": coll["name"],
                "fields": [
                    {"name": f["name"], "type": f.get("type", "string")}
                    for f in coll["fields"]
                ]
            }
            for coll in new_collections
        ]

        # Filter by both _id and user_id to ensure ownership
        filter_doc = {"_id": ObjectId(database_id), "user_id": ObjectId(user_id)}

        updated = self._coll.find_one_and_update(
            filter_doc,
            {"$addToSet": {"collections": {"$each": docs}}},
            # ... other update operations ...
            return_document=ReturnDocument.AFTER,
            session=session
        )
        if not updated:
            raise ValueError(f"Database '{database_id}' not found or access denied.")
        return docs

    # @with_transaction
    def drop_database(self, db_id: str, user_id: str, *, session=None) -> dict:
        """
        Deletes a database's metadata, ensuring it belongs to the specified user.
        """
        filter_doc = {
            "_id": ObjectId(db_id),
            "user_id": ObjectId(user_id)
        }
        meta = self._coll.find_one_and_delete(filter_doc, session=session)

        if not meta:
            raise ValueError(f"Database '{db_id}' not found or you do not have permission to delete it.")
        
        # Drop the actual database from MongoDB here.
        settings.MONGODB_CLIENT.drop_database(meta['displayName'])
        
        return meta

    # @with_transaction
    def drop_collections(self, db_id: str, user_id: str, names: list[str], *, session=None) -> list[str]:
        """
        Removes collections from a database's metadata, ensuring the database belongs to the user.
        """
        meta = self.get_by_id_for_user(db_id, user_id)
        if not meta:
            raise ValueError(f"Database '{db_id}' not found or you do not have permission to access it.")

        existing = {c["name"] for c in meta.get("collections", [])}
        invalid  = set(names) - existing
        if invalid:
            raise ValueError(f"Collections not in metadata: {', '.join(invalid)}")

        self._coll.update_one(
            {"_id": ObjectId(db_id), "user_id": ObjectId(user_id)},
            {"$pull": {"collections": {"name": {"$in": names}}}},
            session=session
        )

        # Drop the actual collections from the database.
        db = settings.MONGODB_CLIENT[meta['displayName']]
        for name in names:
            db.drop_collection(name)
 
        return names

    def list_databases_paginated_for_user(
        self, user_id: str, page: int, page_size: int, search_term: str = None
    ) -> tuple[int, list[dict]]:
        """
        Lists databases for a specific user with pagination and optional search.

        This method is now enriched to include the live collection count for each
        database, making it suitable for direct use by the dashboard UI.
        """
        # --- Step 1: Build the filter for the metadata query ---
        filter_doc = {"user_id": ObjectId(user_id)}
        if search_term:
            # Searching is performed on the user-friendly displayName
            filter_doc["displayName"] = {"$regex": search_term, "$options": "i"}

        # --- Step 2: Get the total count for pagination ---
        total = self._coll.count_documents(filter_doc)
        skip = (page - 1) * page_size

        # --- Step 3: Fetch the paginated metadata documents ---
        # IMPORTANT: We must include 'dbName' in the projection to connect to the live DB.
        projection = {"_id": 1, "displayName": 1, "dbName": 1}
        cursor = (
            self._coll
                .find(filter_doc, projection)
                .sort("displayName", 1)
                .skip(skip)
                .limit(page_size)
        )

        # --- Step 4: Enrich the results with live data ---
        results = []
        client = settings.MONGODB_CLIENT
        for doc in cursor:
            internal_db_name = doc.get("dbName")
            num_collections = 0 # Default to 0

            if internal_db_name:
                try:
                    # Connect to the actual database and count its collections
                    db = client[internal_db_name]
                    num_collections = len(db.list_collection_names())
                except Exception as e:
                    # If the DB connection fails for any reason, log it and default to 0
                    print(f"Warning: Could not list collections for {internal_db_name}. Error: {e}")
                    num_collections = 0
            
            results.append({
                "id": str(doc["_id"]),
                "name": doc["displayName"], # 'name' is the user-friendly key for the API response
                "num_collections": num_collections
            })

        return total, results

    def get_collections_for_user(self, db_id: str, user_id: str) -> list[dict]:
        """
        Retrieves collections for a specific database, ensuring it belongs to the user.
        """
        meta = self.get_by_id_for_user(db_id, user_id)
        if not meta:
            raise ValueError(f"Database '{db_id}' not found or you do not have permission to access it.")

        return meta.get("collections", [])

    def list_collections_for_user(self, db_id: str, user_id: str, *, session=None) -> list[dict]:
        """
        Lists all collections for a given database ID, but only if the user owns it.
        Crucially, it also queries the database to get the live document count for each collection.
        """
        # 1. Security: First, verify ownership and get the metadata document.
        meta = self.get_by_id_for_user(db_id, user_id)
        if not meta:
            raise PermissionError("Database not found or permission denied.")

        # 2. Get the actual internal database name from the metadata.
        internal_db_name = meta.get("dbName")
        if not internal_db_name:
            raise ValueError(f"Internal database name not found for metadata ID {db_id}.")
        
        # 3. Connect to the live user database.
        db = settings.MONGODB_CLIENT[internal_db_name]

        # 4. List collection names and get the document count for each one.
        collections_with_counts = []
        try:
            collection_names = db.list_collection_names(session=session)
            for name in collection_names:
                count = db[name].count_documents({}, session=session)
                collections_with_counts.append({
                    "name": name,
                    "num_documents": count
                })
        except Exception as e:
            # Handle cases where the DB connection might fail
            print(f"Error listing collections for {internal_db_name}: {e}")
            return [] # Return an empty list on error
            
        return collections_with_counts
