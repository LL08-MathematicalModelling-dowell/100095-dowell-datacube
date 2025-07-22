"""
# metadata_service.py
# Service for managing metadata documents in a MongoDB collection.
"""

from bson import ObjectId
from django.conf import settings
from pymongo import ReturnDocument
from api.utils.decorators import with_transaction

class MetadataService:
    """Service for managing metadata documents in a MongoDB collection."""
    def __init__(self):
        self._coll = settings.METADATA_COLLECTION

    def exists_db(self, name: str, user_id: str) -> bool:
        """Checks if a database with that name exists for a specific user."""
        return bool(self._coll.find_one({
            "database_name": name,
            "user_id": ObjectId(user_id)
        }))

    def get_by_id_for_user(self, db_id: str, user_id: str) -> dict | None:
        """Gets a database by its ID, ensuring it belongs to the user."""
        return self._coll.find_one({
            "_id": ObjectId(db_id),
            "user_id": ObjectId(user_id)
        })

    def list_databases_for_user(self, user_id: str) -> list[dict]:
        """Lists all databases owned by a specific user."""
        user_filter = {"user_id": ObjectId(user_id)}
        projection = {"_id": 1, "database_name": 1}
        docs = list(self._coll.find(user_filter, projection))
        return [{"id": str(d["_id"]), "name": d["database_name"]} for d in docs]

    # @with_transaction
    def create_db_meta(
        self,
        database_name: str,
        collections: list[dict],
        user_id: str,
        *,
        session=None
    ) -> dict:
        """
        Insert a new metadata document for a database, associated with a user.
        """
        meta = {
            "user_id": ObjectId(user_id),
            "database_name": database_name,
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

    @with_transaction
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
        settings.MONGODB_CLIENT.drop_database(meta['database_name'])
        
        return meta

    @with_transaction
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
        db = settings.MONGODB_CLIENT[meta['database_name']]
        for name in names:
            db.drop_collection(name)
 
        return names

    def list_databases_paginated_for_user(
        self, user_id: str, page: int, page_size: int, search_term: str = None
    ) -> tuple[int, list[dict]]:
        """
        Lists databases for a specific user with pagination and optional search.
        This replaces the insecure `list_by_filter` method.
        """
        filter_doc = {"user_id": ObjectId(user_id)}

        if search_term:
            filter_doc["database_name"] = {"$regex": search_term, "$options": "i"}

        total = self._coll.count_documents(filter_doc)
        skip  = (page - 1) * page_size

        cursor = (
            self._coll
                .find(filter_doc, {"_id": 1, "database_name": 1})
                .sort("database_name", 1)
                .skip(skip)
                .limit(page_size)
        )
 
        results = [
            {"id": str(d["_id"]), "name": d["database_name"]}
            for d in cursor
        ]

        return total, results
