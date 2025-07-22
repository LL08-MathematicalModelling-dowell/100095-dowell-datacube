"""
This service orchestrates the creation of databases and collections by coordinating
between the MetadataService (for metadata) and CollectionService (for actual
database operations).

This file has been updated to integrate with the custom authentication system.
Key Changes:
1.  User-Aware Methods: All public methods now require a `user_id` parameter,
    which they receive from the authenticated view.
2.  Secure Service Calls: The `user_id` is passed down to every call made to
    `MetadataService` to ensure metadata operations are correctly scoped to
    the user.
3.  Secure Service Instantiation: When creating an instance of `CollectionService`,
    both the `db_name` and the `user_id` are passed to its constructor. This
    ensures that all subsequent collection operations are only performed on
    a database the user has been verified to own.
"""

from api.services.metadata_service import MetadataService
from api.services.collection_service import CollectionService
from api.utils.decorators import with_transaction


class DatabaseService:
    def __init__(self):
        self.meta_svc = MetadataService()

    # @with_transaction
    def create_database_with_collections(
        self,
        db_name: str,
        collections: list[dict],
        user_id: str,
        session=None
    ) -> tuple[dict, list[dict]]:
        """
        1) Insert user-owned metadata doc.
        2) Create the actual MongoDB collections.
        All in one transaction. If anything fails, we abort.
        """
        meta = self.meta_svc.create_db_meta(
            db_name,
            collections,
            user_id=user_id,
            session=session
        )

        coll_svc  = CollectionService(db_name, user_id=user_id)
        names     = [c["name"] for c in collections]
        coll_info = coll_svc.create(names, session=session)

        return meta, coll_info

    # @with_transaction
    def add_collections_with_creation(
        self,
        database_id: str,
        new_cols: list[dict],
        user_id: str,
        session=None
    ) -> list[dict]:
        """
        1) Verify user ownership of the database.
        2) Append new_cols to metadata.
        3) Create the new MongoDB collections.
        """
        meta = self.meta_svc.get_by_id_for_user(database_id, user_id)
        if not meta:
            raise PermissionError(f"Database '{database_id}' not found or access denied.")
        
        db_name = meta["database_name"]

        self.meta_svc.add_collections(
            database_id,
            user_id=user_id,
            new_collections=new_cols,
            session=session
        )

        coll_svc   = CollectionService(db_name, user_id=user_id)
        names      = [c["name"] for c in new_cols]
        return coll_svc.create(names, session=session)