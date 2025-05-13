''' This file contains environment variables for the frontend application.'''


from django.conf import settings
from api.utils.mongodb import build_existing_fields_update_pipeline
from pymongo.errors import CollectionInvalid
from asgiref.sync import sync_to_async
# from api.utils.decorators import with_transaction


class CollectionService:
    def __init__(self, db_name: str):
        self.db = settings.MONGODB_CLIENT[db_name]

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
        """Updates documents, creade field if not exist"""
        return await sync_to_async(
            lambda: self.db[coll_name].update_many(filt or {}, {"$set": update}),
            thread_sensitive=True
        )()

    async def update_many_existing(
        self, coll_name: str, filt: dict, update_data: dict
    ):
        """Update documents existing filed s only, does not create if filed not available"""
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
