"""
This service provides CRUD operations for collections within a specific database.

This file has been updated to integrate with the custom authentication system.
Key Changes:
1.  Secure Initialization: The __init__ method now requires both a `db_name`
    and a `user_id`. It uses the MetadataService to verify that the user
    is the legitimate owner of the database before proceeding.
2.  Exception on Unauthorized Access: If a user tries to instantiate this
    service for a database they do not own, a PermissionError is raised,
    preventing any further operations.
3.  Implicit Security: Because the ownership check happens at instantiation,
    all subsequent methods (`find`, `insert_many`, etc.) are implicitly
    secure, as they can only operate on collections within a database that
    the user has already been authorized to access.
"""

from django.conf import settings
from pymongo.errors import CollectionInvalid
from asgiref.sync import sync_to_async

from api.utils.mongodb import build_existing_fields_update_pipeline
from api.services.metadata_service import MetadataService
# from api.utils.decorators import with_transaction



class CollectionService:
    def __init__(self, db_name: str, user_id: str):
        """
        Initializes the service for a specific database, but only after
        verifying the user has permission to access it.
        """
        meta_svc = MetadataService()

        if not meta_svc.exists_db_by_internal_name(internal_name=db_name, user_id=user_id):
            raise PermissionError(f"Access denied: You do not own database '{db_name}' or it does not exist.")

        # This line is only reached if the security check passes.
        self.db = settings.MONGODB_CLIENT[db_name]
        self.db_name = db_name
        self.user_id = user_id

    # @with_transaction
    def create(
        self,
        names: list[str],
        session=None,
    ) -> list[dict]:
        """
        Create each named collection. Returns a list of dicts:
          {
            "name":    <collection name>,
            "created": True if created,
            "exists":  True if already existed,
            "error":   <error message> or None
          }
        """
        results = []
        for name in names:
            rec = {"name": name, "created": False, "exists": False, "error": None}
            try:
                self.db.create_collection(name, session=session)
                rec["created"] = True
            except CollectionInvalid:
                rec["exists"] = True
            except Exception as e:
                rec["error"] = str(e)


            results.append(rec)
        return results

    async def count_documents(self, coll_name: str, filt: dict) -> int:
        return await sync_to_async(
            lambda: self.db[coll_name].count_documents(filt or {}),
            thread_sensitive=True
        )()

    async def find(
        self, coll_name: str, filt: dict = None, skip: int = 0, limit: int = 0
    ) -> list[dict]:
        def _find():
            cursor = self.db[coll_name].find(filt or {}).skip(skip).limit(limit)
            return list(cursor)
        return await sync_to_async(_find, thread_sensitive=True)()

    async def insert_many(self, coll_name: str, docs: list[dict]):
        return await sync_to_async(
            lambda: self.db[coll_name].insert_many(docs),
            thread_sensitive=True
        )()

    async def update_many(self, coll_name: str, filt: dict, update: dict):
        """Updates documents, creating fields if they do not exist."""
        return await sync_to_async(
            lambda: self.db[coll_name].update_many(filt or {}, {"$set": update}),
            thread_sensitive=True
        )()

    async def update_many_existing(
        self, coll_name: str, filt: dict, update_data: dict
    ):
        """Updates only existing fields in documents, does not create new fields."""
        pipeline = build_existing_fields_update_pipeline(update_data)
        return await sync_to_async(
            lambda: self.db[coll_name].update_many(filt, pipeline),
            thread_sensitive=True
        )()

    async def delete_many(self, coll_name: str, filt: dict):
        return await sync_to_async(
            lambda: self.db[coll_name].delete_many(filt or {}),
            thread_sensitive=True
        )()
