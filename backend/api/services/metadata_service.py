"""
# metadata_service.py
# Service for managing metadata documents in a MongoDB collection.
"""

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
    """
    
    def __init__(self, user_id: str):
        if not user_id:
            raise ValueError("MetadataService requires a valid user_id for operations.")
        
        self.user_id = ObjectId(user_id)
        self._coll = settings.METADATA_COLLECTION
        self._client = settings.MONGODB_CLIENT

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
            "user_id": self.user_id,  # Uses centralized ID
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
        
        # update_one using centralized user filter
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
        """
        Removes specific collections from metadata and physically drops them 
        from the internal database.
        """
        meta = await self.get_db(db_id)
        if not meta:
            raise ValueError("Database not found or permission denied.")

        internal_db_name = meta["dbName"]
        existing_names = {c["name"] for c in meta.get("collections", [])}
        
        # Check if requested collections actually exist
        invalid = set(names) - existing_names
        if invalid:
            raise ValueError(f"Collections not found in metadata: {', '.join(invalid)}")

        # 1. Update Metadata
        await self._coll.update_one(
            {"_id": ObjectId(db_id), "user_id": self.user_id},
            {
                "$pull": {"collections": {"name": {"$in": names}}},
                "$set": {"updated_at": datetime.now(timezone.utc)}
            },
            session=session
        )

        # 2. Drop Physical Collections
        db_instance = await settings.MONGODB_CLIENT[internal_db_name]
        for name in names:
            await db_instance.drop_collection(name)
 
        return names

    async def drop_database(self, db_id: str, *, session=None) -> Dict:
        """Drops metadata and physical DB using bound identity."""
        meta = await self._coll.find_one_and_delete(self._get_user_filter(db_id), session=session)
        if not meta:
            raise PermissionError("Access denied or Database not found.")
        
        # Physical drop using internal name retrieved from secure metadata
        await settings.MONGODB_CLIENT.drop_database(meta['dbName'])

        return meta

    async def list_databases_paginated(
        self, page: int = 1, page_size: int = 50, search_term: str | None = None
    ) -> Tuple[int, List[Dict]]:
        """
        Lists databases with pagination. Optimized to show collection counts 
        from metadata to avoid redundant network round-trips to every DB.
        """
        query = self._get_user_filter()
        if search_term:
            query["displayName"] = {"$regex": search_term.strip(), "$options": "i"}

        total = await self._coll.count_documents(query)
        skip = (page - 1) * page_size

        # REMOVE 'await' from here
        cursor = self._coll.find(query, {"_id": 1, "displayName": 1, "collections": 1}) \
             .sort("displayName", 1) \
             .skip(skip) \
             .limit(page_size)

        # AWAIT the result retrieval
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
        """
        Returns collections with their live document counts from the physical DB.
        """
        meta = await self.get_db(db_id)
        if not meta:
            raise PermissionError("Database not found or access denied.")

        internal_name = meta.get("dbName")
        db = self._client[internal_name]

        # Use metadata as the source of truth for which collections SHOULD exist
        results = []
        for col_meta in meta.get("collections", []):
            col_name = col_meta["name"]
            try:
                # count_documents is safer than estimated_document_count for small/filtered sets
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
        """Determines the 2025-standard string representation of a Python/BSON type."""
        if value is None: return "null"
        if isinstance(value, bool): return "boolean"  # Check bool before int (bool is a subclass of int)
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
        """Analyzes a batch of documents to find all field names and their observed types."""
        field_map = collections.defaultdict(set)
        for doc in docs:
            for key, val in doc.items():
                if key.startswith("_"): continue  # Skip internal MongoDB keys
                field_map[key].add(self._infer_type(val))
        
        # Merge multiple types into a single string (e.g., "string, null")
        return {k: ", ".join(sorted(v)) for k, v in field_map.items()}

    async def update_collection_schema_inference(self, db_id: str, coll_name: str, sample_docs: List[Dict]):
        """
        Learns the schema from new data and updates metadata if new fields 
        or new types are discovered.
        """
        new_schema = self._generate_schema_from_docs(sample_docs)
        if not new_schema:
            return

        meta = await self.get_db(db_id)
        if not meta:
            raise PermissionError("Access denied.")

        # Find the specific collection in the metadata array
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
                # Merge logic: if a field was "string" and now we see "integer", it becomes "integer, string"
                current_types = set(existing_fields[field_name].split(", "))
                incoming_types = set(inferred_types.split(", "))
                merged = ", ".join(sorted(current_types | incoming_types))
                
                if merged != existing_fields[field_name]:
                    existing_fields[field_name] = merged
                    has_changed = True

        if has_changed:
            updated_fields_list = [{"name": n, "type": t} for n, t in existing_fields.items()]
            self._coll.update_one(
                {
                    "_id": ObjectId(db_id), 
                    "user_id": self.user_id,
                    "collections.name": coll_name
                },
                {"$set": {"collections.$.fields": updated_fields_list, "updated_at": datetime.now()}}
            )

    async def prune_inactive_fields(self, db_id: str, dry_run: bool = True) -> Dict[str, Any]:
        """
        Maintenance task: Removes field metadata for fields that have not 
        appeared in any documents since the configured 'inactive_days' threshold.
        
        This keeps the schema 'clean' for users by hiding fields from old 
        schema versions that are no longer being sent to the API.
        """
        # 1. Fetch metadata using centralized user context
        meta = await self.get_db(db_id)
        if not meta:
            raise PermissionError("Database not found or access denied.")

        pruning_cfg = meta.get("pruning", {})
        if not pruning_cfg.get("enabled", False):
            return {"status": "skipped", "reason": "pruning_disabled_for_database"}

        # 2. Setup Thresholds
        days_threshold = pruning_cfg.get("inactive_days", 90)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_threshold)
        
        # Performance trick: Generate an ObjectId representing the cutoff time
        # This allows us to query the _id index directly for time-based filtering
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

        # 3. Process each collection defined in metadata
        for coll_meta in meta.get("collections", []):
            coll_name = coll_meta["name"]
            
            # AGGREGATION: Identify which fields are currently 'active'
            # We look at all docs newer than the cutoff and extract unique keys
            pipeline = [
                {"$match": {"_id": {"$gte": cutoff_oid}}},
                {"$project": {"fields": {"$objectToArray": "$$ROOT"}}},
                {"$unwind": "$fields"},
                # Filter out MongoDB internals and the ID
                {"$match": {"fields.k": {"$not": {"$regex": "^_"}}}}, 
                {"$group": {"_id": None, "active_keys": {"$addToSet": "$fields.k"}}}
            ]
            
            try:
                agg_result = list(db[coll_name].aggregate(pipeline))
                active_fields = set(agg_result[0]["active_keys"] if agg_result else [])
                
                current_metadata_fields = {f["name"] for f in coll_meta.get("fields", [])}
                
                # Fields in metadata that were NOT found in the recent document scan
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
                # Log error for specific collection but continue pruning others
                report["collections_processed"].append({
                    "name": coll_name, 
                    "error": str(e)
                })

        report["total_removed_count"] = total_removed
        return report

    def _perform_prune_update(self, db_id: str, coll_name: str, fields_to_remove: list):
        """Internal helper to execute the $pull operation on metadata."""
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


    # api/services/metadata_service.py update
    def check_quota_is_exceeded(self, user_id):
        """
        Decision Gate: Returns True if the user has reached their 2025 storage limit.
        """
        stats_db = settings.MONGODB_CLIENT["platform_ops"]
        # Get the latest snapshot for all user's databases
        latest_stat = stats_db["storage_snapshots"].find_one(
            {"user_id": user_id},
            sort=[("timestamp", -1)]
        )
        
        if not latest_stat:
            return False
            
        TOTAL_LIMIT_BYTES = 1024 * 1024 * 500  # 500MB Limit for 2025 Free Tier
        return latest_stat["total_size"] > TOTAL_LIMIT_BYTES
