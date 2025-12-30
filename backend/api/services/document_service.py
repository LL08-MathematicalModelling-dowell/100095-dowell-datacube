"""
Service for orchestrating document CRUD operations.
Refactored for 2025:
1. Stateful user context: Bound to user_id at initialization.
2. Automated Schema Evolution: Automatically updates field metadata on write.
3. Separation of Concerns: Decouples metadata verification from data access.
"""
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Optional
from api.services.metadata_service import MetadataService
from api.services.collection_service import CollectionService
from pymongo.errors import PyMongoError


class DocumentService:
    def __init__(self, user_id: str):
        if not user_id:
            raise ValueError("DocumentService requires a valid user_id.")
        
        self.user_id = user_id
        self.meta_svc = MetadataService(user_id=user_id)

    async def _get_scoped_collection_svc(self, db_id: str, coll_name: str) -> CollectionService:
        """
        Internal helper: Verifies permissions and resolves the internal dbName.
        """
        # Step 1: Securely fetch metadata (already scoped to self.user_id)
        meta = await self.meta_svc.get_db(db_id)
        if not meta:
            raise PermissionError("Database not found or access denied.")


        # Step 2: Validate the collection exists in the authorized schema
        authorized_collections = {c["name"] for c in meta.get("collections", [])}
        if coll_name not in authorized_collections:
            raise ValueError(f"Collection '{coll_name}' is not defined in metadata.")

        # Step 3: Instantiate CollectionService using the internal 'dbName'
        dislplay_name = meta.get("displayName")
        db_name = meta.get("dbName")
        return CollectionService(db_name=dislplay_name, user_id=self.user_id, internal_db_name=db_name) # type: ignore

    async def list_docs(
        self,
        db_id: str,
        coll_name: str,
        filt: Optional[dict] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[int, List[Dict]]:
        """Lists documents with pagination and user-scoping."""
        try:
            svc = await self._get_scoped_collection_svc(db_id, coll_name)
            skip = (page - 1) * page_size
            total = await svc.count_documents(coll_name, filt or {})
            docs = await svc.find(coll_name, filt or {}, skip, page_size)

            # remove "is_deleted" field from returned documents
            for doc in docs:
                doc.pop("is_deleted", None)

            return total, docs
        except (ValueError, PermissionError) as e:
            raise e
        except PyMongoError as e:
            raise RuntimeError(f"Database error during list: {e}")

    async def create_docs(self, db_id: str, coll_name: str, docs: List[Dict]):
        """Inserts documents and triggers schema discovery."""
        try:
            # append "is_deleted" to all docs if not present
            for doc in docs:
                if "is_deleted" not in doc:
                    doc["is_deleted"] = False
            svc = await self._get_scoped_collection_svc(db_id, coll_name)
            result = await svc.insert_many(coll_name, docs)

            # Schema Evolution: Learn new field types from the inserted data
            if docs:
                await self.meta_svc.update_collection_schema_inference(db_id, coll_name, docs)
                
            return result
        except (ValueError, PermissionError) as e:
            raise e
        except PyMongoError as e:
            raise RuntimeError(f"Failed to create documents: {e}")

    async def update_docs(
        self,
        db_id: str,
        coll_name: str,
        filt: dict,
        update_data: dict,
        bulk: bool = False
    ):
        """Updates documents and updates field metadata if new fields are added."""
        if not update_data:
            raise ValueError("No update data provided.")
            
        try:
            svc = await self._get_scoped_collection_svc(db_id, coll_name)
            
            # Perform the update
            if bulk:
                result = await svc.update_many(coll_name, filt or {}, update_data)
            else:
                result = await svc.update_one(coll_name, filt or {}, update_data)

            # Schema Evolution: Analyze the update data for new fields
            if "$set" in update_data:
                await self.meta_svc.update_collection_schema_inference(
                    db_id, coll_name, [update_data["$set"]]
                )
            elif not any(k.startswith('$') for k in update_data.keys()):
                await self.meta_svc.update_collection_schema_inference(db_id, coll_name, [update_data])
            return result
        except PyMongoError as e:
            raise RuntimeError(f"Failed to update documents: {e}")

    async def delete_docs(self, db_id: str, coll_name: str, filt: dict, soft: bool = True):
        """Standardizes deletion logic."""
        try:
            svc = await self._get_scoped_collection_svc(db_id, coll_name)
            if soft:
                soft_delete_payload = {
                    "is_deleted": True,
                    "deleted_at": datetime.now(timezone.utc)
                }
                return await svc.update_many(coll_name, filt or {}, soft_delete_payload)
            else:
                return await svc.delete_many(coll_name, filt or {})
        except PyMongoError as e:
            raise RuntimeError(f"Deletion failed: {e}")