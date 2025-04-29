"""Service for managing documents in a MongoDB collection."""

from bson import ObjectId
from api.services.metadata_service import MetadataService
from api.services.collection_service import CollectionService


class DocumentService:
    """Service for managing documents in a MongoDB collection."""
    def __init__(self):
        self.meta = MetadataService()

    async def get_collection(self, db_id: str, coll_name: str) -> CollectionService:
        """Get a collection service for the specified database and collection."""
        try:
            meta = self.meta.get_by_id(db_id)
            if not meta:
                raise ValueError("Database not found")
            
            names = []
            if meta["collections"]:
                # If collections are defined in metadata, use them
                names = [c["name"] for c in meta["collections"]]
            else:
                # Otherwise, use collections_metadata
                names = [c["name"] for c in meta["collections_metadata"]]
   
            if coll_name not in names:
                raise ValueError("Collection not in metadata")
            return CollectionService(meta["database_name"])
        except Exception as e:
            raise ValueError("Collection not in metadata")

    async def list_docs(self, db_id, coll_name, filt, page, page_size):
        """List documents in a collection with pagination."""
        try:
            svc = await self.get_collection(db_id, coll_name)
            skip = (page - 1) * page_size
            total = await svc.count_documents(coll_name, filt)
            docs  = await svc.find(coll_name, filt, skip, page_size)
            return total, docs
        except Exception as e:
            print(f"Error in list_docs: {e}")
            return 0, []

    async def create_docs(self, db_id, coll_name, docs):
        """Create documents in a collection."""
        try:
            svc = await self.get_collection(db_id, coll_name)
            return await svc.insert_many(coll_name, docs)
        except Exception as e:
            print(f"Error in create_docs: {e}")
            return None

    async def update_docs(self, db_id, coll_name, filt, update):
        """Update documents in a collection."""
        try:
            svc = await self.get_collection(db_id, coll_name)
            print(f"===================   update_docs ===================")
            print(f"===================   coll_name = {coll_name} ===================")
            return await svc.update_many(coll_name, filt, {"$set": update})
        except Exception as e:
            print(f"Error in update_docs: {e}")
            return None

    async def delete_docs(self, db_id, coll_name, filt, soft=True):
        """Delete documents in a collection."""
        try:
            svc = await self.get_collection(db_id, coll_name)
            if soft:
                return await svc.update_many(coll_name, filt, {"$set": {"is_deleted": True}})
            else:
                return await svc.delete_many(coll_name, filt)
        except Exception as e:
            print(f"Error in delete_docs: {e}")
            return None

