"""
Service for managing documents in a MongoDB collection.

This file has been updated to integrate with the custom authentication system.
Key Changes:
1.  User-Aware Methods: All public methods (`list_docs`, `create_docs`, etc.)
    now require a `user_id` to ensure operations are performed on behalf of an
    authenticated and authorized user.
2.  Secure `get_collection` Method: This core helper method is now the primary
    security gate. It takes the `user_id` and uses the secure `get_by_id_for_user`
    method from MetadataService to verify ownership *before* returning a
    CollectionService instance.
3.  Secure `CollectionService` Instantiation: When `get_collection` creates
    an instance of `CollectionService`, it passes the `user_id` to its
    constructor, ensuring all subsequent raw database operations are also
    scoped to the correct user.
"""
from typing import List, Dict, Tuple
from api.services.metadata_service import MetadataService
from api.services.collection_service import CollectionService
from pymongo.errors import PyMongoError


class DocumentService:
    """Service for managing documents in a MongoDB collection."""

    def __init__(self):
        self.meta = MetadataService()

    async def get_collection(self, db_id: str, coll_name: str, user_id: str) -> CollectionService:
        """
        Get a collection service, but only after verifying the user owns the database.
        """
        meta = self.meta.get_by_id_for_user(db_id, user_id)
        if not meta:
            raise PermissionError(f"Database '{db_id}' not found or access denied.")

        try:
            collection_names = [c["name"] for c in meta.get("collections", [])]
        except KeyError as e:
            raise ValueError(f"Invalid metadata format: missing key {e}")

        if coll_name not in collection_names:
            raise ValueError(f"Collection '{coll_name}' not listed in metadata for database '{db_id}'.")

        return CollectionService(meta["database_name"], user_id=user_id)

    async def list_docs(
        self,
        db_id: str,
        coll_name: str,
        user_id: str,
        filt: dict,
        page: int,
        page_size: int
    ) -> Tuple[int, List[Dict]]:
        """List documents in a collection with pagination."""
        try:
            svc = await self.get_collection(db_id, coll_name, user_id)
            skip = (page - 1) * page_size
            total = await svc.count_documents(coll_name, filt or {})
            docs = await svc.find(coll_name, filt or {}, skip, page_size)
            return total, docs
        except (ValueError, PyMongoError, PermissionError) as e:
            raise RuntimeError(f"Failed to list documents: {e}")

    async def create_docs(
        self,
        db_id: str,
        coll_name: str,
        user_id: str,
        docs: List[Dict]
    ):
        """Insert multiple documents into a collection."""
        try:
            svc = await self.get_collection(db_id, coll_name, user_id)
            return await svc.insert_many(coll_name, docs)
        except (ValueError, PyMongoError, PermissionError) as e:
            raise RuntimeError(f"Failed to create documents: {e}")

    async def update_docs(
        self,
        db_id: str,
        coll_name: str,
        user_id: str,
        filt: dict,
        update: dict,
        update_all_fields: bool = False
    ):
        """Update documents in a collection."""
        if not update:
            raise ValueError("No update data provided.")
        try:
            svc = await self.get_collection(db_id, coll_name, user_id)
            
            if update_all_fields:
                return await svc.update_many(coll_name, filt or {}, update)
            else:
                return await svc.update_many_existing(coll_name, filt or {}, update)
        except (ValueError, PyMongoError, PermissionError) as e:
            raise RuntimeError(f"Failed to update documents: {e}")

    async def delete_docs(
        self,
        db_id: str,
        coll_name: str,
        user_id: str,
        filt: dict,
        soft: bool = True
    ):
        """Soft or hard delete documents in a collection."""
        try:
            svc = await self.get_collection(db_id, coll_name, user_id)
            if soft:
                return await svc.update_many(coll_name, filt or {}, {"is_deleted": True})
            else:
                return await svc.delete_many(coll_name, filt or {})
        except (ValueError, PyMongoError, PermissionError) as e:
            raise RuntimeError(f"Failed to delete documents: {e}")