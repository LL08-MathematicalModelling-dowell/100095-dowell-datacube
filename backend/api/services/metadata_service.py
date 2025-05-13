"""Service for managing documents in a MongoDB collection."""


from bson import ObjectId
from django.conf import settings
from pymongo import ReturnDocument
from api.utils.decorators import with_transaction


class MetadataService:
    """Service for managing metadata documents in a MongoDB collection."""
    def __init__(self):
        self._coll = settings.METADATA_COLLECTION

    def exists_db(self, name: str) -> bool:
        return bool(self._coll.find_one({"database_name": name}))

    def get_by_id(self, db_id: str) -> dict | None:
        return self._coll.find_one({"_id": ObjectId(db_id)})

    def list_databases(self, filter_term: str = None) -> list[dict]:
        docs = list(self._coll.find({}, {"_id": 1, "database_name": 1}))
        if filter_term:
            docs = [
                d for d in docs
                if filter_term.lower() in d["database_name"].lower()
            ]
        return [{"id": str(d["_id"]), "name": d["database_name"]} for d in docs]

    def list_collections(self, db_id: str) -> list[dict]:
        meta = self.get_by_id(db_id)
        if not meta:
            raise ValueError(f"Database '{db_id}' not found")
        db = settings.MONGODB_CLIENT[meta["database_name"]]

        out = []
        for name in db.list_collection_names():
            count = db[name].count_documents({})
            out.append({"name": name, "num_documents": count})
        return out

    # @with_transaction
    def create_db_meta(
        self,
        database_name: str,
        collections: list[dict],
        *,
        session=None
    ) -> dict:
        """
        Insert a new metadata document for a database.
        Returns the full metadata dict (with `_id`).
        """
        meta = {
            "database_name": database_name,
            "collections": [
                {
                    "name": coll["name"],
                    "fields": [
                        {"name": f["name"], "type": f.get("type", "string")}
                        for f in coll["fields"]
                    ]
                }
                for coll in collections
            ],
            "number_of_collections": len(collections),
            "number_of_fields": sum(len(coll["fields"]) for coll in collections),
        }
        result = self._coll.insert_one(meta, session=session)
        meta["_id"] = result.inserted_id
        return meta

    # @with_transaction
    def add_collections(
        self, database_id: str, new_collections: list[dict], *, session=None
    ) -> list[dict]:
        """
        Append new collections to an existing metadata document.
        Returns the list of added collection‐docs.
        """
        docs = [
            {
                "name": coll["name"],
                "fields": [
                    {"name": f["name"], "type": f.get("type", "string")}
                    for f in coll["fields"]
                ]
            }
            for coll in new_collections
        ]
        num_colls  = len(docs)
        num_fields = sum(len(d["fields"]) for d in docs)

        updated = self._coll.find_one_and_update(
            {"_id": ObjectId(database_id)},
            {
                "$addToSet": {"collections": {"$each": docs}},
                "$inc": {
                    "number_of_collections": num_colls,
                    "number_of_fields":      num_fields
                }
            },
            return_document=ReturnDocument.AFTER,
            session=session
        )
        if not updated:
            raise ValueError(f"Database '{database_id}' not found")
        return docs

    @with_transaction
    def drop_database(self, db_id: str, *, session=None) -> dict:
        meta = self._coll.find_one_and_delete({"_id": ObjectId(db_id)}, session=session)
        if not meta:
            raise ValueError(f"Database '{db_id}' not found")
        return meta

    @with_transaction
    def drop_collections(self, db_id: str, names: list[str], *, session=None) -> list[str]:
        meta = self.get_by_id(db_id)
        if not meta:
            raise ValueError(f"Database '{db_id}' not found")

        existing = {c["name"] for c in meta.get("collections", [])}
        invalid  = set(names) - existing
        if invalid:
            raise ValueError(f"Collections not in metadata: {', '.join(invalid)}")

        self._coll.update_one(
            {"_id": ObjectId(db_id)},
            {"$pull": {"collections": {"name": {"$in": names}}}},
            session=session
        )
        return names

    def list_by_filter(self, filter_doc: dict, page: int, page_size: int) -> tuple[int, list[dict]]:
        total = self._coll.count_documents(filter_doc)
        skip  = (page - 1) * page_size
        cursor = (
            self._coll
                .find(filter_doc, {"_id": 1, "database_name": 1})
                .skip(skip)
                .limit(page_size)
        )
        results = [
            {"id": str(d["_id"]), "database_name": d["database_name"]}
            for d in cursor
        ]
        return total, results

