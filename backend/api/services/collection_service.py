"""
Service for managing physical MongoDB collection operations.
Refactored for 2025:
1.  Native Async: Replaces sync_to_async with native PyMongo 4.9+ async API.
2.  Stateful Identity: Locked to a verified db/user pair upon creation.
3.  Ownership Guard: PermissionError raised if user-database mapping is invalid.
"""

import re
from typing import Any, List, Dict, Optional
from django.conf import settings
from bson import ObjectId, errors
from pymongo.errors import CollectionInvalid, PyMongoError
from api.services.metadata_service import MetadataService
from api.utils.mongodb import build_existing_fields_update_pipeline




class MongoFilterHelper:
    # Pre-compile regex for performance if this is called frequently
    # matches keys that end with 'id' (case-insensitive) and also matches exactly 'id'
    ID_PATTERN = re.compile(r'^(.*id$|^id$)', re.IGNORECASE)

    def convert_filter_ids(self, filt: Any) -> Any:
        """
        Recursively converts string IDs in a filter to BSON ObjectId instances.
        
        Handles:
        - Nested dictionaries (Aggregation/Complex filters)
        - Lists of filters (e.g., inside $and, $or, $in)
        - Case-insensitive key matching (e.g., 'userId', 'USER_ID', '_id', 'id')
        """

        if isinstance(filt, dict):
            filt = {k if k != 'id' else '_id': v for k, v in filt.items()}
            return {
                k: self.convert_filter_ids(v) if isinstance(v, (dict, list)) 
                else self._convert_value(k, v)
                for k, v in filt.items()
            }
        elif isinstance(filt, list):
            return [self.convert_filter_ids(item) for item in filt]
        return filt

    def _convert_value(self, key: str, value: Any) -> Any:
        """Internal helper to validate and cast a single value."""
        # 1. Check if the key suggests an ID (case-insensitive)
        if isinstance(value, str) and self.ID_PATTERN.match(key):
            # 2. Check if the string is a valid 24-character hex string
            if ObjectId.is_valid(value):
                try:
                    return ObjectId(value)
                except errors.InvalidId:
                    return value
        return value

class CollectionService:
    def __init__(
        self, 
        *,  # <--- MAGIC STAR: Everything after this must be a keyword argument
        user_id: str,
        db_name: str,
        internal_db_name: Optional[str] = None,
        new_db: bool = False,
    ):
        self.user_id = user_id
        self.db_name = db_name
        self.internal_db_name = internal_db_name
        
        # Ensure settings and MONGODB_CLIENT exist
        if not settings or not hasattr(settings, 'MONGODB_CLIENT'):
            raise ValueError("Invalid settings provided to CollectionService")
            
        self.db = settings.MONGODB_CLIENT[internal_db_name]
        self.filter_helper = MongoFilterHelper()

    @classmethod
    async def _create( # Removed underscore; this is the public entry point
        cls, 
        db_name: str,
        user_id: str,
        internal_db_name: Optional[str] = None,
        new_db: bool = False,
    ) -> "CollectionService":
        
        meta_svc = MetadataService(user_id=user_id)

        if not new_db:
            if not await meta_svc.exists_db(db_name):
                raise PermissionError(f"Unauthorized access to '{db_name}'")

        if internal_db_name is None:
            internal_db_name = await meta_svc.get_meta_internal_db_name(db_name)

        # Call the constructor using explicit keywords
        return cls(
            user_id=user_id,
            db_name=db_name,
            internal_db_name=internal_db_name, # type: ignore
            new_db=new_db)

    async def _prepare_filter(self, filt: Dict) -> Dict:
        """Internal helper to ensure all filters are safe and standardized."""
        # 1. Convert string IDs to ObjectIds
        new_filt = self.filter_helper.convert_filter_ids(filt or {})
        
        # 2. Global Safety: Never update soft-deleted documents
        # This was missing from your update_one version!
        new_filt["is_deleted"] = {"$ne": True}
        return new_filt

    async def create(self, names: List[str], session=None) -> List[Dict]:
        """
        Explicitly creates collections. Native async in PyMongo 4.9+.
        """
        results = []
        for name in names:
            report = {"name": name, "created": False, "exists": False, "error": None}
            try:
                await self.db.create_collection(name, session=session)
                report["created"] = True
            except CollectionInvalid:
                report["exists"] = True
            except PyMongoError as e:
                report["error"] = str(e)
            results.append(report)
        return results

    async def count_documents(self, coll_name: str, filt: Optional[Dict] = None, session=None) -> int:
        """Returns document count using native async."""
        new_filt = self.filter_helper.convert_filter_ids(filt or {})
        new_filt["is_deleted"] = {"$ne": True}
        return await self.db[coll_name].count_documents(new_filt, session=session)

    async def find(
        self, coll_name: str, filt: Optional[Dict] = None, skip: int = 0, limit: int = 0, session=None
    ) -> List[Dict]:
        """Returns documents with modern cursor support."""
        # Ensure we do not return 'is_deleted' documents
        new_filt = self.filter_helper.convert_filter_ids(filt or {})
        new_filt["is_deleted"] = {"$ne": True}
        cursor = self.db[coll_name].find(new_filt, session=session).skip(skip).limit(limit)

        return await cursor.to_list(length=limit or 1000)

    async def insert_many(self, coll_name: str, docs: List[Dict], session=None):
        """Native async batch insertion."""
        if not docs:
            return None
        return await self.db[coll_name].insert_many(docs, session=session)

   
    async def update_one(self, coll_name: str, filt: Dict, update: Dict, session=None):
        """Updates exactly one document, following global safety filters."""
        safe_filt = await self._prepare_filter(filt)
        
        result = await self.db[coll_name].update_one(
            safe_filt, 
            {"$set": update}, 
            session=session
        )
        
        # Pro Tip: Log findings for debugging
        if result.matched_count == 0:
            print(f"DEBUG: No document matched filter {safe_filt} in {coll_name}")
        elif result.modified_count == 0:
            print(f"DEBUG: Document matched but no data changed (idempotent update)")
            
        return result

    async def update_many(self, coll_name: str, filt: Dict, update: Dict, session=None):
        """Batch updates multiple documents."""
        safe_filt = await self._prepare_filter(filt)
        
        return await self.db[coll_name].update_many(
            safe_filt,
            {"$set": update}, 
            session=session
        )


    # async def update_many(self, coll_name: str, filt: Dict, update: Dict, session=None):
    #     """Standard batch update."""
    #     # Ensure we do not update 'is_deleted' documents
    #     new_filt = self.filter_helper.convert_filter_ids(filt or {})
    #     new_filt["is_deleted"] = {"$ne": True}

    #     return await self.db[coll_name].update_many(
    #         new_filt,
    #         {"$set": update}, 
    #         session=session
    #     )

    # async def update_one(self, coll_name: str, filt: Dict, update: Dict, session=None):
    #     """Standard single document update."""
    #     new_filt = self.filter_helper.convert_filter_ids(filt or {})
    #     return await self.db[coll_name].update_one(
    #         new_filt, 
    #         {"$set": update}, 
    #         session=session
    #     )

    async def update_many_existing(self, coll_name: str, filt: Dict, update_data: Dict, session=None):
        """
        Optimized pipeline update: Uses build_existing_fields_update_pipeline
        to ensure only existing fields are modified.
        """
        pipeline = build_existing_fields_update_pipeline(update_data)
        new_filt = self.filter_helper.convert_filter_ids(filt or {})
        return await self.db[coll_name].update_many(
            new_filt, 
            pipeline, 
            session=session
        )

    async def delete_many(self, coll_name: str, filt: Dict, session=None):
        """Standard batch deletion."""
        new_filt = self.filter_helper.convert_filter_ids(filt or {})
        return await self.db[coll_name].delete_many(new_filt, session=session)