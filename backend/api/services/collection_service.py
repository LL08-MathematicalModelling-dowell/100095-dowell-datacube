''' This file contains environment variables for the frontend application.'''
from django.conf import settings
from asgiref.sync import sync_to_async


class CollectionService:
    def __init__(self, db_name):
        self.db = settings.MONGODB_CLIENT[db_name]

    async def count_documents(self, coll_name: str, filt: dict) -> int:
        """Count documents matching filter."""
        return await sync_to_async(lambda: self.db[coll_name].count_documents(filt or {}), thread_sensitive=True)()

    async def find(self, coll_name: str, filt: dict = None, skip: int = 0, limit: int = 0) -> list:
        """Return list of documents matching filter."""
        def find_docs():
            cursor = self.db[coll_name].find(filt or {}).skip(skip).limit(limit)
            return list(cursor)
        return await sync_to_async(find_docs, thread_sensitive=True)()

    async def insert_many(self, coll_name: str, docs: list):
        """Insert documents."""
        return await sync_to_async(lambda: self.db[coll_name].insert_many(docs), thread_sensitive=True)()

    async def update_many(self, coll_name: str, filt: dict, update: dict):
        """Update documents."""
        return await sync_to_async(lambda: self.db[coll_name].update_many(filt or {}, update), thread_sensitive=True)()

    async def delete_many(self, coll_name: str, filt: dict):
        """Delete documents."""
        return await sync_to_async(lambda: self.db[coll_name].delete_many(filt or {}), thread_sensitive=True)()
