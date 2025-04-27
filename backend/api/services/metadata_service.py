"""Service for managing documents in a MongoDB collection."""

from bson import ObjectId
from django.conf import settings
from api.utils.decorators import with_transaction

class MetadataService:
    """Service for managing metadata documents in a MongoDB collection."""

    def __init__(self):
        self._coll = settings.METADATA_COLLECTION

    def exists_db(self, name: str) -> bool:
        """Check if a database with the given name exists in the metadata collection."""
        return bool(self._coll.find_one({"database_name": name}))

    def get_by_id(self, db_id: str) -> dict:
        """Get metadata document by ID."""
        return self._coll.find_one({"_id": ObjectId(db_id)})

    def list_databases(self, filter_term: str = None) -> list:
        """Return list of {"id", "name"}."""
        docs = list(self._coll.find({}, {"_id": 1, "database_name": 1}))
        if filter_term:
            docs = [
                d for d in docs
                if filter_term.lower() in d["database_name"].lower()
            ]
        return [{"id": str(d["_id"]), "name": d["database_name"]} for d in docs]

    def list_collections(self, db_id: str) -> list:
        """Return list of {"name","num_documents"} for a given db."""
        meta = self.get_by_id(db_id)
        if not meta:
            raise ValueError(f"Database '{db_id}' not found")

        db_name = meta["database_name"]
        client  = settings.MONGODB_CLIENT
        db      = client[db_name]

        out = []
        for coll_name in db.list_collection_names():
            count = db[coll_name].count_documents({})
            out.append({"name": coll_name, "num_documents": count})
        return out

    @with_transaction
    def create_db_meta(self, database_name: str, collections: list, *, session=None) -> dict:
        """
        Insert a new metadata document for a database.

        Args:
          database_name: name of the new database
          collections:   list of {"name": str, "fields": [{"name":..., "type":...}, ...]}

        Returns:
          the metadata dict (including inserted _id)
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

    @with_transaction
    def add_collections(self, database_id: str, new_collections: list, *, session=None) -> None:
        """
        Append new collections to an existing metadata document.

        Args:
          database_id:     str or ObjectId of the metadata doc
          new_collections: list of {"name":..., "fields":[...]}
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

        self._coll.update_one(
            {"_id": ObjectId(database_id)},
            {
                "$addToSet": {"collections": {"$each": docs}},
                "$inc": {
                    "number_of_collections": num_colls,
                    "number_of_fields":      num_fields
                }
            },
            session=session
        )

    @with_transaction
    def drop_database(self, db_id: str, *, session=None) -> dict:
        """
        Atomically delete metadata and return the deleted doc;
        actual database drop is done outside.
        """
        meta = self._coll.find_one_and_delete(
            {"_id": ObjectId(db_id)},
            session=session
        )
        if not meta:
            raise ValueError(f"Database '{db_id}' not found")
        return meta

    @with_transaction
    def drop_collections(self, db_id: str, names: list, *, session=None) -> list:
        """
        Remove collection metadata. Returns list of actually pulled names.
        """
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

    def list_by_filter(self, filter_doc: dict, page: int, page_size: int):
        """Apply a raw Mongo filter on metadata, with pagination."""
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

