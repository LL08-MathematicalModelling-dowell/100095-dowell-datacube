from typing import List, Dict, Tuple
from api.services.metadata_service import MetadataService
from api.services.collection_service import CollectionService
from pymongo.errors import PyMongoError


class DocumentService:
    """Service for managing documents in a MongoDB collection."""

    def __init__(self):
        self.meta = MetadataService()

    async def get_collection(self, db_id: str, coll_name: str) -> CollectionService:
        """Get a collection service for the specified database and collection."""
        meta = self.meta.get_by_id(db_id)
        if not meta:
            raise ValueError(f"Database metadata with id '{db_id}' not found.")

        try:
            collection_names = (
                [c["name"] for c in meta.get("collections", [])]
                if meta.get("collections")
                else [c["name"] for c in meta.get("collections_metadata", [])]
            )
        except KeyError as e:
            raise ValueError(f"Invalid metadata format: missing key {e}")

        if coll_name not in collection_names:
            raise ValueError(f"Collection '{coll_name}' not listed in metadata for database '{db_id}'.")

        return CollectionService(meta["database_name"])

    async def list_docs(
        self,
        db_id: str,
        coll_name: str,
        filt: dict,
        page: int,
        page_size: int
    ) -> Tuple[int, List[Dict]]:
        """List documents in a collection with pagination."""
        try:
            svc = await self.get_collection(db_id, coll_name)
            skip = (page - 1) * page_size
            total = await svc.count_documents(coll_name, filt or {})
            docs = await svc.find(coll_name, filt or {}, skip, page_size)
            return total, docs
        except (ValueError, PyMongoError) as e:
            raise RuntimeError(f"Failed to list documents: {e}")

    async def create_docs(
        self,
        db_id: str,
        coll_name: str,
        docs: List[Dict]
    ):
        """Insert multiple documents into a collection."""
        try:
            svc = await self.get_collection(db_id, coll_name)
            return await svc.insert_many(coll_name, docs)
        except (ValueError, PyMongoError) as e:
            raise RuntimeError(f"Failed to create documents: {e}")

    async def update_docs(
        self,
        db_id: str,
        coll_name: str,
        filt: dict,
        update: dict
    ):
        """Update documents in a collection."""
        if not update:
            raise ValueError("No update data provided.")
        try:
            svc = await self.get_collection(db_id, coll_name)
            
            # return await svc.update_many(coll_name, filt or {}, update)
            return await svc.update_many_existing(coll_name, filt or {}, update)
        except (ValueError, PyMongoError) as e:
            raise RuntimeError(f"Failed to update documents: {e}")

    async def delete_docs(
        self,
        db_id: str,
        coll_name: str,
        filt: dict,
        soft: bool = True
    ):
        """Soft or hard delete documents in a collection."""
        try:
            svc = await self.get_collection(db_id, coll_name)
            if soft:
                return await svc.update_many(coll_name, filt or {}, {"is_deleted": True})
            else:
                return await svc.delete_many(coll_name, filt or {})
        except (ValueError, PyMongoError) as e:
            raise RuntimeError(f"Failed to delete documents: {e}")
