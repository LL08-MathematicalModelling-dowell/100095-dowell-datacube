"""Service for managing documents in a MongoDB collection."""

from bson import ObjectId
from api.services.metadata_service import MetadataService
from api.services.collection_service import CollectionService
from api.utils.mongodb import to_object_id

class DocumentService:
    """Service for managing documents in a MongoDB collection."""
    def __init__(self):
        self.meta = MetadataService()

    async def get_collection(self, db_id, coll_name):
        """Get collection service for a specific database and collection."""
        meta = self.meta.get_by_id(db_id)
        if not meta:
            raise ValueError("DB not found")
        if coll_name not in [c["name"] for c in meta["collections"]]:
            raise ValueError("Collection not in metadata")
        return CollectionService(meta["database_name"])

    async def list_docs(self, db_id, coll_name, filters, page, page_size):
        """List documents in a collection with pagination and filtering."""
        svc = await self.get_collection(db_id, coll_name)
        filt = {**filters, "is_deleted": False}
        total = await svc.count_documents(coll_name, filt)
        docs = await svc.find(coll_name, filt, (page-1)*page_size, page_size)
        return total, docs

    async def create_docs(self, db_id, coll_name, docs):
        """Create documents in a collection."""
        svc = await self.get_collection(db_id, coll_name)
        return await svc.insert_many(coll_name, docs)

    async def update_docs(self, db_id, coll_name, filt, update):
        """Update documents in a collection."""
        svc = await self.get_collection(db_id, coll_name)
        return await svc.update_many(coll_name, filt, {"$set": update})

    async def delete_docs(self, db_id, coll_name, filt, soft=True):
        """Delete documents in a collection. If soft is True, mark as deleted."""
        svc = await self.get_collection(db_id, coll_name)
        if soft:
            return await svc.update_many(coll_name, filt, {"$set": {"is_deleted": True}})
        else:
            return await svc.delete_many(coll_name, filt)