import asyncio
from django.conf import settings
from api.utils.decorators import with_transaction, run_async


class CollectionService:
    def __init__(self, db_name):
        self.db = settings.MONGODB_CLIENT[db_name]

    @with_transaction
    def create(self, coll_defs: list, *, session=None):
        """
        coll_defs = [{ "name": str, "fields": [{name,type}...] }, ...]
        Returns list of {name, id, fields}.
        """
        out = []
        for c in coll_defs:
            self.db.create_collection(c["name"], session=session)
            doc = {f["name"]: None for f in c["fields"]}
            res = self.db[c["name"]].insert_one(doc, session=session)
            out.append({
                "name": c["name"],
                "id": str(res.inserted_id),
                "fields": c["fields"]
            })
        return out

    @run_async
    async def count_documents(self, coll_name, filt):
        return await asyncio.to_thread(self.db[coll_name].count_documents, filt)

    @run_async
    async def find(self, coll_name, filt, skip, limit):
        cursor = self.db[coll_name].find(filt).skip(skip).limit(limit)
        return await asyncio.to_thread(list, cursor)

    @run_async
    async def insert_many(self, coll_name, docs):
        return await asyncio.to_thread(self.db[coll_name].insert_many, docs)

    @run_async
    async def update_many(self, coll_name, filt, update):
        return await asyncio.to_thread(self.db[coll_name].update_many, filt, update)

    @run_async
    async def delete_many(self, coll_name, filt):
        return await asyncio.to_thread(self.db[coll_name].delete_many, filt)