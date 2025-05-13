from api.services.metadata_service import MetadataService
from api.services.collection_service import CollectionService
from api.utils.decorators import with_transaction


class DatabaseService:
    def __init__(self):
        self.meta_svc = MetadataService()

    @with_transaction
    def create_database_with_collections(
        self,
        db_name: str,
        collections: list[dict],
        session=None
    ) -> tuple[dict, list[dict]]:
        """
        1) Insert metadata doc
        2) Create the actual MongoDB collections
        All in one transaction. If anything fails, we abort.
        """
        meta = self.meta_svc.create_db_meta(db_name, collections, session=session)

        coll_svc  = CollectionService(db_name)
        names     = [c["name"] for c in collections]
        coll_info = coll_svc.create(names, session=session)

        return meta, coll_info

    @with_transaction
    def add_collections_with_creation(
        self,
        database_id: str,
        new_cols: list[dict],
        session=None
    ) -> list[dict]:
        """
        1) Append new_cols to metadata
        2) Create the new MongoDB collections
        """
        docs_added = self.meta_svc.add_collections(database_id, new_cols, session=session)
        db_name    = self.meta_svc.get_by_id(database_id)["database_name"]

        coll_svc   = CollectionService(db_name)
        names      = [c["name"] for c in new_cols]
        return coll_svc.create(names, session=session)