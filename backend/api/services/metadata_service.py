import collections
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any, Tuple
from django.conf import settings
from bson import ObjectId
from pymongo import ReturnDocument


class MetadataService:
    """
    Centralized Metadata Service.
    Scoped to a specific user at instantiation to ensure data isolation.
    Manages both database metadata (collections) and file metadata (GridFS).
    """
    
    def __init__(self, user_id: str):
        if not user_id:
            raise ValueError("MetadataService requires a valid user_id for operations.")
        
        self.user_id = ObjectId(user_id)
        # Database metadata collection (existing)
        self._coll = settings.METADATA_COLLECTION
        # File metadata collection (new)
        self._file_coll = settings.FILE_METADATA_COLLECTION
        self._client = settings.MONGODB_CLIENT

    def _stringify_objectids(self, doc):
        """Recursively convert ObjectId instances to strings in a document."""
        if doc is None:
            return None
        if isinstance(doc, list):
            return [self._stringify_objectids(item) for item in doc]
        if isinstance(doc, dict):
            result = {}
            for k, v in doc.items():
                if isinstance(v, ObjectId):
                    result[k] = str(v)
                elif isinstance(v, (dict, list)):
                    result[k] = self._stringify_objectids(v)
                else:
                    result[k] = v
            return result
        return doc

    # ----------------------------------------------------------------------
    # Existing methods for database metadata (unchanged, kept for context)
    # ----------------------------------------------------------------------
    def _format_collection_schema(self, collections: List[Dict]) -> List[Dict]:
        """Ensures all collection metadata follows a consistent structure."""
        return [
            {
                "name": coll["name"],
                "created_at": datetime.now(timezone.utc),
                "fields": [
                    {"name": f["name"], "type": f.get("type", "string")}
                    for f in coll.get("fields", [])
                ]
            }
            for coll in collections
        ]
        
    def _get_user_filter(self, db_id: Optional[str] = None) -> Dict:
        """Helper to consistently scope queries to the current user."""
        query = {"user_id": self.user_id}
        if db_id:
            query["_id"] = ObjectId(db_id)
        return query

    async def get_db(self, db_id: str) -> Optional[Dict]:
        """Fetches a database document strictly scoped to the bound user."""
        return await self._coll.find_one(self._get_user_filter(db_id))

    async def exists_db(self, display_name: str, *, session=None) -> bool:
        """Checks display name uniqueness within the user's scope."""
        query = self._get_user_filter()
        query["displayName"] = display_name.lower().strip()
        return await self._coll.count_documents(query, limit=1, session=session) > 0

    async def get_meta_internal_db_name(self, display_name: str) -> Optional[str]:
        """Retrieves the internal DB name for a given display name."""
        query = self._get_user_filter()
        query["displayName"] = display_name.lower().strip()
        doc = await self._coll.find_one(query, {"dbName": 1})
        return doc["dbName"] if doc else None

    async def create_db_meta(
        self,
        user_provided_name: str,
        internal_db_name: str,
        collections: List[Dict],
        *,
        session=None
    ) -> Dict:
        now = datetime.now(timezone.utc)
        meta = {
            "user_id": self.user_id,
            "displayName": user_provided_name.strip(),
            "dbName": internal_db_name,
            "created_at": now,
            "updated_at": now,
            "collections": self._format_collection_schema(collections),
        }
        result = await self._coll.insert_one(meta, session=session)
        meta["_id"] = result.inserted_id
        return meta

    async def add_collections(self, db_id: str, new_collections: List[Dict], *, session=None) -> List[Dict]:
        formatted_docs = self._format_collection_schema(new_collections)
        updated = await self._coll.find_one_and_update(
            self._get_user_filter(db_id),
            {
                "$push": {"collections": {"$each": formatted_docs}},
                "$set": {"updated_at": datetime.now(timezone.utc)}
            },
            return_document=ReturnDocument.AFTER,
            session=session
        )
        if not updated:
            raise PermissionError("Access denied or Database not found.")
        return formatted_docs

    async def drop_collections(self, db_id: str, names: List[str], *, session=None) -> List[str]:
        """Drops specified collections from metadata and physical DB, scoped to user permissions."""
        meta = await self.get_db(db_id)
        if not meta:
            raise ValueError("Database not found or permission denied.")

        internal_db_name = meta["dbName"]
        existing_names = {c["name"] for c in meta.get("collections", [])}
        invalid = set(names) - existing_names
        if invalid:
            raise ValueError(f"Collections not found in metadata: {', '.join(invalid)}")

        await self._coll.update_one(
            {"_id": ObjectId(db_id), "user_id": self.user_id},
            {
                "$pull": {"collections": {"name": {"$in": names}}},
                "$set": {"updated_at": datetime.now(timezone.utc)}
            },
            session=session
        )

        db_instance = await settings.MONGODB_CLIENT[internal_db_name]
        for name in names:
            await db_instance.drop_collection(name)
        return names

    async def drop_database(self, db_id: str, *, session=None) -> Dict:
        """Drops the entire database (metadata + physical) scoped to user permissions."""
        meta = await self._coll.find_one_and_delete(self._get_user_filter(db_id), session=session)
        if not meta:
            raise PermissionError("Access denied or Database not found.")
        await settings.MONGODB_CLIENT.drop_database(meta['dbName'])
        return meta

    async def list_databases_paginated(
        self, page: int = 1, page_size: int = 50, search_term: str | None = None
    ) -> Tuple[int, List[Dict]]:
        """Lists databases with pagination and optional search, scoped to the user."""
        query = self._get_user_filter()
        if search_term:
            query["displayName"] = {"$regex": search_term.strip(), "$options": "i"}

        total = await self._coll.count_documents(query)
        skip = (page - 1) * page_size
        cursor = self._coll.find(query, {"_id": 1, "displayName": 1, "collections": 1}) \
             .sort("displayName", 1) \
             .skip(skip) \
             .limit(page_size)
        results_docs = await cursor.to_list(length=page_size)

        results = []
        for doc in results_docs:
            results.append({
                "id": str(doc["_id"]),
                "name": doc["displayName"],
                "num_collections": len(doc.get("collections", []))
            })
        return total, results

    async def list_collections_with_live_counts(self, db_id: str, *, session=None) -> List[Dict]:
        """Lists collections for a database along with live document counts, scoped to user permissions."""
        meta = await self.get_db(db_id)
        if not meta:
            raise PermissionError("Database not found or access denied.")

        internal_name = meta.get("dbName")
        db = self._client[internal_name]

        results = []
        for col_meta in meta.get("collections", []):
            col_name = col_meta["name"]
            try:
                count = await db[col_name].count_documents({}, session=session)
                results.append({
                    "name": col_name,
                    "num_documents": count,
                    "fields": col_meta.get("fields", [])
                })
            except Exception:
                results.append({"name": col_name, "num_documents": 0, "error": "Unreachable"})
        return results

    def _infer_type(self, value: Any) -> str:
        """Basic type inference for schema generation."""
        if value is None: return "null"
        if isinstance(value, bool): return "boolean"
        if isinstance(value, int): return "integer"
        if isinstance(value, float): return "float"
        if isinstance(value, str): return "string"
        if isinstance(value, datetime): return "date"
        if isinstance(value, ObjectId): return "objectid"
        if isinstance(value, list):
            inner_type = self._infer_type(value[0]) if value else "any"
            return f"array<{inner_type}>"
        if isinstance(value, dict): return "object"
        return "unknown"

    def _generate_schema_from_docs(self, docs: List[Dict]) -> Dict[str, str]:
        """Generates a field schema by inferring types from a sample of documents."""
        field_map = collections.defaultdict(set)
        for doc in docs:
            for key, val in doc.items():
                if key.startswith("_"): continue
                field_map[key].add(self._infer_type(val))
        return {k: ", ".join(sorted(v)) for k, v in field_map.items()}

    async def update_collection_schema_inference(self, db_id: str, coll_name: str, sample_docs: List[Dict]):
        """Updates collection metadata schema by inferring field types from sample documents."""
        new_schema = self._generate_schema_from_docs(sample_docs)
        if not new_schema:
            return

        meta = await self.get_db(db_id)
        if not meta:
            raise PermissionError("Access denied.")

        all_collections = meta.get("collections", [])
        target_col = next((c for c in all_collections if c["name"] == coll_name), None)
        if not target_col:
            raise ValueError(f"Collection '{coll_name}' not found in metadata.")

        existing_fields = {f["name"]: f["type"] for f in target_col.get("fields", [])}
        has_changed = False

        for field_name, inferred_types in new_schema.items():
            if field_name not in existing_fields:
                existing_fields[field_name] = inferred_types
                has_changed = True
            else:
                current_types = set(existing_fields[field_name].split(", "))
                incoming_types = set(inferred_types.split(", "))
                merged = ", ".join(sorted(current_types | incoming_types))
                if merged != existing_fields[field_name]:
                    existing_fields[field_name] = merged
                    has_changed = True

        if has_changed:
            updated_fields_list = [{"name": n, "type": t} for n, t in existing_fields.items()]
            await self._coll.update_one(
                {
                    "_id": ObjectId(db_id), 
                    "user_id": self.user_id,
                    "collections.name": coll_name
                },
                {"$set": {"collections.$.fields": updated_fields_list, "updated_at": datetime.now()}}
            )

    async def prune_inactive_fields(self, db_id: str, dry_run: bool = True) -> Dict[str, Any]:
        """Prunes fields from collection metadata that haven't been active in a specified time frame.
        Uses ObjectId timestamps to determine activity. Only affects metadata, not actual documents.
        """
        meta = await self.get_db(db_id)
        if not meta:
            raise PermissionError("Database not found or access denied.")

        pruning_cfg = meta.get("pruning", {})
        if not pruning_cfg.get("enabled", False):
            return {"status": "skipped", "reason": "pruning_disabled_for_database"}

        days_threshold = pruning_cfg.get("inactive_days", 90)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_threshold)
        cutoff_oid = ObjectId.from_datetime(cutoff_date)
        internal_db_name = meta["dbName"]
        db = self._client[internal_db_name]

        report = {
            "status": "completed",
            "dry_run": dry_run,
            "cutoff_date": cutoff_date.isoformat(),
            "collections_processed": []
        }
        total_removed = 0

        for coll_meta in meta.get("collections", []):
            coll_name = coll_meta["name"]
            pipeline = [
                {"$match": {"_id": {"$gte": cutoff_oid}}},
                {"$project": {"fields": {"$objectToArray": "$$ROOT"}}},
                {"$unwind": "$fields"},
                {"$match": {"fields.k": {"$not": {"$regex": "^_"}}}}, 
                {"$group": {"_id": None, "active_keys": {"$addToSet": "$fields.k"}}}
            ]
            try:
                agg_result = list(db[coll_name].aggregate(pipeline))
                active_fields = set(agg_result[0]["active_keys"] if agg_result else [])
                current_metadata_fields = {f["name"] for f in coll_meta.get("fields", [])}
                inactive_fields = current_metadata_fields - active_fields

                if inactive_fields:
                    if not dry_run:
                        self._perform_prune_update(db_id, coll_name, list(inactive_fields))
                    total_removed += len(inactive_fields)
                    report["collections_processed"].append({
                        "name": coll_name,
                        "removed_count": len(inactive_fields),
                        "fields": list(inactive_fields)
                    })
            except Exception as e:
                report["collections_processed"].append({
                    "name": coll_name, 
                    "error": str(e)
                })

        report["total_removed_count"] = total_removed
        return report

    def _perform_prune_update(self, db_id: str, coll_name: str, fields_to_remove: list):
        """Performs the actual update to remove inactive fields from collection metadata."""
        self._coll.update_one(
            {
                "_id": ObjectId(db_id),
                "user_id": self.user_id,
                "collections.name": coll_name
            },
            {
                "$pull": {
                    "collections.$.fields": {"name": {"$in": fields_to_remove}}
                },
                "$set": {
                    "pruning.last_pruned_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )

    async def check_quota_is_exceeded(self) -> bool:
        """Checks if the user has exceeded their storage quota based on the latest snapshot."""
        ops_db = settings.MONGODB_CLIENT["platform_ops"]
        latest_stat = await ops_db["storage_snapshots"].find_one(
            {"user_id": self.user_id},
            sort=[("timestamp", -1)]
        )
        if not latest_stat:
            return False
        limit_mb = getattr(settings, "DATACUBE_FREE_TIER_MB", 500)
        total_limit_bytes = 1024 * 1024 * limit_mb
        current_usage = latest_stat.get("total_size", 0)
        is_exceeded = current_usage > total_limit_bytes

        if is_exceeded:
            await ops_db["user_activity"].insert_one({
                "timestamp": datetime.now(timezone.utc),
                "metadata": {"user_id": self.user_id, "type": "quota_block"},
                "details": f"Blocked write at {current_usage} bytes (Limit: {total_limit_bytes})"
            })
        return is_exceeded

    # ----------------------------------------------------------------------
    # New methods for file metadata (GridFS)
    # ----------------------------------------------------------------------
    def _get_file_user_filter(self, file_id: Optional[str] = None) -> Dict:
        """
        Helper to scope file metadata queries to the current user.
        If file_id is provided, include it in the filter.
        """
        query = {"user_id": self.user_id}
        if file_id:
            query["file_id"] = file_id  # type: ignore # store as string for easier querying
        return query

    async def create_file_entry(
        self,
        file_id: str,
        filename: str,
        size: int,
        content_type: Optional[str],
        storage_type: str,
        *,
        session=None
    ) -> Dict:
        """
        Creates a file metadata entry after a successful GridFS upload.
        The file_id is the GridFS ObjectId as a string.
        """
        now = datetime.now(timezone.utc)
        entry = {
            "user_id": self.user_id,
            "file_id": file_id,                # GridFS _id as string
            "filename": filename,
            "size": size,
            "content_type": content_type,
            "storage_type": storage_type,      # e.g., "gridfs"
            "uploaded_at": now,
            "updated_at": now,
        }
        result = await self._file_coll.insert_one(entry, session=session)
        entry["_id"] = result.inserted_id

        return self._stringify_objectids(entry) # type: ignore
        # return entry

    async def delete_file_entry(self, file_id: str, *, session=None) -> bool:
        """
        Deletes a file metadata entry scoped to the user.
        Returns True if a document was deleted, False otherwise.
        """
        result = await self._file_coll.delete_one(
            self._get_file_user_filter(file_id),
            session=session
        )
        return result.deleted_count == 1

    # Optional: add method to retrieve file entry if needed later
    async def get_file_entry(self, file_id: str) -> Optional[Dict]:
        """
        Retrieves a file metadata entry scoped to the user.
        """
        doc = await self._file_coll.find_one(self._get_file_user_filter(file_id))
        return self._stringify_objectids(doc) if doc else None # type: ignore

    async def list_files_paginated(
        self, page: int = 1, page_size: int = 50, search_term: Optional[str] = None
    ) -> Tuple[int, List[Dict]]:
        """
        List file metadata entries for the current user with pagination.
        Returns (total_count, list_of_docs).
        """
        query = {"user_id": self.user_id}
        if search_term:
            query["filename"] = {"$regex": search_term, "$options": "i"} # type: ignore
        
        total = await self._file_coll.count_documents(query)
        skip = (page - 1) * page_size

        cursor = self._file_coll.find(query).sort("uploaded_at", -1).skip(skip).limit(page_size)
        docs = await cursor.to_list(length=page_size)
        
        docs = [self._stringify_objectids(doc) for doc in docs]
        return total, docs # type: ignore

    async def get_storage_stats(self) -> Dict[str, Any]:
        """
        Calculates aggregate storage statistics for the current user.
        Returns total count and total size in bytes.
        """
        pipeline = [
            # 1. Filter documents belonging to this user
            {"$match": {"user_id": self.user_id}},
            # 2. Sum up the 'size' field and count documents
            {
                "$group": {
                    "_id": None,
                    "total_count": {"$sum": 1},
                    "total_size_bytes": {"$sum": "$size"}
                }
            }
        ]
        
        cursor = await self._file_coll.aggregate(pipeline)
        results = await cursor.to_list(length=1)
        
        if not results:
            return {
                "total_count": 0,
                "total_size_bytes": 0
            }
            
        # Remove the internal _id from response
        stats = results[0]
        stats.pop("_id", None)
        return stats
