"""
Service for orchestrating document CRUD operations.
Refactored for 2025:
1. Stateful user context: Bound to user_id at initialization.
2. Automated Schema Evolution: Automatically updates field metadata on write.
3. Separation of Concerns: Decouples metadata verification from data access.
"""
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Optional
from api.application.metadata_service import MetadataService
from api.application.collection_service import CollectionService
from api.application.service_context import UserServiceContext
from api.infrastructure.query_safety import (
    assert_mutating_filter_allowed,
    is_operator_update,
    plain_fields_for_partial_update,
    prepare_update_document,
    validate_filter,
)
from pymongo.errors import PyMongoError


class DocumentService:
    def __init__(self, user_id: str, *, role: str | None = None):
        if not user_id:
            raise ValueError("DocumentService requires a valid user_id.")

        self.ctx = UserServiceContext(user_id, role=role)
        self.user_id = self.ctx.user_id
        self.meta_svc = MetadataService(user_id=self.user_id, role=self.ctx.role)

    async def _get_scoped_collection_svc(self, db_id: str, coll_name: str) -> CollectionService:
        """
        Internal helper: Verifies permissions and resolves the internal dbName.
        """
        # Step 1: Securely fetch metadata (already scoped to self.user_id)
        meta = await self.meta_svc.get_db(db_id)
        if not meta:
            raise PermissionError("Database not found or access denied.")


        # Step 2: Validate the collection exists in the authorized schema
        authorized_collections = {c["name"] for c in meta.get("collections", [])}
        if coll_name not in authorized_collections:
            raise ValueError(f"Collection '{coll_name}' is not defined in metadata.")

        # Step 3: Instantiate CollectionService using the internal 'dbName'
        dislplay_name = meta.get("displayName")
        db_name = meta.get("dbName")
        return CollectionService(db_name=dislplay_name, user_id=self.user_id, internal_db_name=db_name) # type: ignore

    async def list_docs(
        self,
        db_id: str,
        coll_name: str,
        filt: Optional[dict] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[int, List[Dict]]:
        """Lists documents with pagination and user-scoping."""
        try:
            svc = await self._get_scoped_collection_svc(db_id, coll_name)
            skip = (page - 1) * page_size
            total = await svc.count_documents(coll_name, filt or {})
            docs = await svc.find(coll_name, filt or {}, skip, page_size)

            # remove "is_deleted" field from returned documents
            for doc in docs:
                doc.pop("is_deleted", None)

            return total, docs
        except (ValueError, PermissionError) as e:
            raise e
        except PyMongoError as e:
            raise RuntimeError(f"Database error during list: {e}")

    async def create_docs(self, db_id: str, coll_name: str, docs: List[Dict]):
        """Inserts documents and triggers schema discovery."""
        self.ctx.assert_can_write()
        try:
            # append "is_deleted" to all docs if not present
            for doc in docs:
                if "is_deleted" not in doc:
                    doc["is_deleted"] = False
            svc = await self._get_scoped_collection_svc(db_id, coll_name)
            result = await svc.insert_many(coll_name, docs)

            # Schema Evolution: Learn new field types from the inserted data
            if docs:
                await self.meta_svc.update_collection_schema_inference(db_id, coll_name, docs)
                
            return result
        except (ValueError, PermissionError) as e:
            raise e
        except PyMongoError as e:
            raise RuntimeError(f"Failed to create documents: {e}")

    async def update_docs(
        self,
        db_id: str,
        coll_name: str,
        filt: dict,
        update_data: dict,
        *,
        allow_new_fields: bool = False,
        update_many: bool = False,
        upsert: bool = False,
    ):
        """Update one or many documents; optional upsert when filter targets _id."""
        self.ctx.assert_can_write()
        validate_filter(filt or {})
        assert_mutating_filter_allowed(filt or {}, update_many=update_many)

        if upsert:
            if update_many:
                raise ValueError("upsert cannot be combined with update_many.")
            if not (filt.get("_id") or filt.get("id")):
                raise ValueError("upsert requires '_id' or 'id' in filters.")

        update_doc, schema_sample = prepare_update_document(update_data)
        if upsert:
            set_on_insert = update_doc.setdefault("$setOnInsert", {})
            if not isinstance(set_on_insert, dict):
                raise ValueError("$setOnInsert must be an object when provided.")
            set_on_insert.setdefault("is_deleted", False)

        try:
            svc = await self._get_scoped_collection_svc(db_id, coll_name)

            if allow_new_fields:
                if update_many:
                    result = await svc.update_many_raw(coll_name, filt, update_doc)
                else:
                    result = await svc.update_one_raw(
                        coll_name, filt, update_doc, upsert=upsert
                    )
            else:
                if is_operator_update(update_data) and not (
                    set(update_data.keys()) == {"$set"}
                ):
                    raise ValueError(
                        "Operator updates other than a lone $set require update_all_fields=true."
                    )
                plain = plain_fields_for_partial_update(update_data)
                if update_many:
                    result = await svc.update_many_existing_fields(
                        coll_name, filt, plain
                    )
                else:
                    result = await svc.update_one_existing_fields(
                        coll_name, filt, plain
                    )

            if schema_sample:
                await self.meta_svc.update_collection_schema_inference(
                    db_id, coll_name, [schema_sample]
                )
            return result
        except (ValueError, PermissionError):
            raise
        except PyMongoError as e:
            raise RuntimeError(f"Failed to update documents: {e}") from e

    async def delete_docs(self, db_id: str, coll_name: str, filt: dict, soft: bool = True):
        """Delete or soft-delete documents matching a non-empty filter."""
        self.ctx.assert_can_write()
        validate_filter(filt or {})
        assert_mutating_filter_allowed(filt or {}, update_many=True)

        try:
            svc = await self._get_scoped_collection_svc(db_id, coll_name)
            if soft:
                soft_delete_payload = {
                    "is_deleted": True,
                    "deleted_at": datetime.now(timezone.utc),
                }
                return await svc.soft_delete_many(coll_name, filt, soft_delete_payload)
            return await svc.delete_many(coll_name, filt)
        except (ValueError, PermissionError):
            raise
        except PyMongoError as e:
            raise RuntimeError(f"Deletion failed: {e}") from e