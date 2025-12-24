"""
Service for managing physical MongoDB collection operations.
Refactored for 2025:
1.  Native Async: Replaces sync_to_async with native PyMongo 4.9+ async API.
2.  Stateful Identity: Locked to a verified db/user pair upon creation.
3.  Ownership Guard: PermissionError raised if user-database mapping is invalid.
"""
from typing import List, Dict, Optional, Any
from django.conf import settings
from pymongo.errors import CollectionInvalid, PyMongoError
from api.services.metadata_service import MetadataService
from api.utils.mongodb import build_existing_fields_update_pipeline


class CollectionService:
    def __init__(
            self, 
            db_name: str,
            user_id: str,
            internal_db_name: Optional[str] = None,
            new_db: Optional[bool] = False    
        ):
        """
        Initialization performs a mandatory security check.
        Instantiating this for a database not owned by the user is a fatal error.
        """
        self.user_id = user_id
        self.db_name = db_name
        
        meta_svc = MetadataService(user_id=user_id)
        if not new_db:
            if not meta_svc.exists_db(db_name):
                raise PermissionError(f"Unauthorized: Access to '{db_name}' denied.")

        if internal_db_name is None:
            internal_db_name = meta_svc.get_meta_internal_db_name(db_name)

        self.db = settings.MONGODB_CLIENT[internal_db_name]

    def create(self, names: List[str], session=None) -> List[Dict]:
        """
        Explicitly creates collections. Native async in PyMongo 4.9+.
        """
        results = []
        for name in names:
            report = {"name": name, "created": False, "exists": False, "error": None}
            try:
                self.db.create_collection(name, session=session)
                report["created"] = True
            except CollectionInvalid:
                report["exists"] = True
            except PyMongoError as e:
                report["error"] = str(e)
            results.append(report)
        return results

    def count_documents(self, coll_name: str, filt: Optional[Dict] = None, session=None) -> int:
        """Returns document count using native async."""
        return self.db[coll_name].count_documents(filt or {}, session=session)

    def find(
        self, coll_name: str, filt: Optional[Dict] = None, skip: int = 0, limit: int = 0, session=None
    ) -> List[Dict]:
        """Returns documents with modern cursor support."""
        # Ensure we do not return 'is_deleted' documents
        new_filt = filt or {}
        new_filt["is_deleted"] = {"$ne": True}
        cursor = self.db[coll_name].find(new_filt, session=session).skip(skip).limit(limit)
        return list(cursor)

    def insert_many(self, coll_name: str, docs: List[Dict], session=None):
        """Native async batch insertion."""
        if not docs:
            return None
        return self.db[coll_name].insert_many(docs, session=session)

    def update_many(self, coll_name: str, filt: Dict, update: Dict, session=None):
        """Standard batch update."""
        # Ensure we do not update 'is_deleted' documents
        new_filt = filt or {}
        new_filt["is_deleted"] = {"$ne": True}

        return self.db[coll_name].update_many(
            new_filt,
            {"$set": update}, 
            session=session
        )

    def update_one(self, coll_name: str, filt: Dict, update: Dict, session=None):
        """Standard single document update."""
        return self.db[coll_name].update_one(
            filt or {}, 
            {"$set": update}, 
            session=session
        )

    def update_many_existing(self, coll_name: str, filt: Dict, update_data: Dict, session=None):
        """
        Optimized pipeline update: Uses build_existing_fields_update_pipeline
        to ensure only existing fields are modified.
        """
        pipeline = build_existing_fields_update_pipeline(update_data)
        return self.db[coll_name].update_many(
            filt or {}, 
            pipeline, 
            session=session
        )

    def delete_many(self, coll_name: str, filt: Dict, session=None):
        """Standard batch deletion."""
        return self.db[coll_name].delete_many(filt or {}, session=session)