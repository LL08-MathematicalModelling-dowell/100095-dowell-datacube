"""
Database and collection inventory for analytics (metadata + telemetry rollups).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from api.application.metadata_service import MetadataService
from api.domain.metadata_models import serialize_metadata_doc
from django.conf import settings


def _iso(dt: Any) -> Optional[str]:
    if dt is None:
        return None
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    return str(dt)


async def aggregate_db_operations(
    user_id: str,
    start: datetime,
    end: datetime,
    *,
    db_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    API call counts keyed by db_id and collection for the date window.
    Returns:
      by_db: { db_id: { total, by_collection: { name: count }, by_operation: { op: count } } }
      daily_by_db: { db_id: [ { date, count } ] }
    """
    coll = settings.MONGODB_CLIENT["datacube_analytics"]["db_operations"]
    match: dict[str, Any] = {
        "user_id": user_id,
        "timestamp": {"$gte": start, "$lte": end},
        "db_id": {"$exists": True, "$nin": [None, ""]},
    }
    if db_id:
        match["db_id"] = db_id

    pipeline_totals = [
        {"$match": match},
        {
            "$group": {
                "_id": {
                    "db_id": "$db_id",
                    "collection": {"$ifNull": ["$collection", "system"]},
                    "operation_type": "$operation_type",
                },
                "count": {"$sum": 1},
            }
        },
    ]
    cursor = await coll.aggregate(pipeline_totals)
    rows = await cursor.to_list(length=10_000)

    by_db: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = row["_id"]
        did = key.get("db_id") or "unknown"
        cname = key.get("collection") or "system"
        op = key.get("operation_type") or "unknown"
        cnt = int(row["count"])
        bucket = by_db.setdefault(
            did,
            {"total": 0, "by_collection": {}, "by_operation": {}},
        )
        bucket["total"] += cnt
        bucket["by_collection"][cname] = bucket["by_collection"].get(cname, 0) + cnt
        bucket["by_operation"][op] = bucket["by_operation"].get(op, 0) + cnt

    pipeline_daily = [
        {"$match": match},
        {
            "$group": {
                "_id": {
                    "db_id": "$db_id",
                    "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                },
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id.date": 1}},
    ]
    cursor2 = await coll.aggregate(pipeline_daily)
    daily_rows = await cursor2.to_list(length=5000)
    daily_by_db: dict[str, list[dict[str, Any]]] = {}
    for row in daily_rows:
        did = row["_id"]["db_id"]
        daily_by_db.setdefault(did, []).append(
            {"date": row["_id"]["date"], "api_calls": int(row["count"])}
        )

    return {"by_db": by_db, "daily_by_db": daily_by_db}


async def build_inventory(
    user_id: str,
    start: datetime,
    end: datetime,
    *,
    database_id: Optional[str] = None,
    refresh_storage: bool = False,
    skip_storage_refresh: bool = False,
) -> dict[str, Any]:
    """Full database/collection inventory for the analytics UI."""
    meta_svc = MetadataService(user_id=user_id)
    if database_id:
        meta = await meta_svc.get_db(database_id, record_access=False)
        db_docs = [meta] if meta else []
    else:
        db_docs = await meta_svc.list_user_databases_for_inventory()

    ops = await aggregate_db_operations(user_id, start, end, db_id=database_id)

    databases_out: list[dict[str, Any]] = []
    total_documents = 0
    total_data_bytes = 0
    last_activity: Optional[datetime] = None

    for doc in db_docs:
        if not doc:
            continue
        db_id = str(doc["_id"])
        if not skip_storage_refresh:
            if refresh_storage:
                try:
                    await meta_svc.refresh_storage_stats_for_db(db_id, force=True)
                    doc = await meta_svc.get_db(db_id, record_access=False) or doc
                except Exception:
                    pass
            else:
                try:
                    await meta_svc.refresh_storage_stats_for_db(db_id, max_age_hours=6)
                    doc = await meta_svc.get_db(db_id, record_access=False) or doc
                except Exception:
                    pass

        db_ops = ops["by_db"].get(db_id, {"total": 0, "by_collection": {}, "by_operation": {}})
        trend = ops["daily_by_db"].get(db_id, [])
        storage_total = int(doc.get("storage_bytes_total") or 0)
        total_data_bytes += storage_total

        collections_out = []
        doc_count_db = 0
        for col in doc.get("collections") or []:
            name = col["name"]
            cached = int(col.get("document_count_cached") or 0)
            live_count = cached
            try:
                internal = doc["dbName"]
                live_count = await settings.MONGODB_CLIENT[internal][name].estimated_document_count()
            except Exception:
                live_count = cached
            doc_count_db += live_count
            col_calls = int(db_ops["by_collection"].get(name, 0))
            col_access = col.get("last_access_at")
            if col_access and (last_activity is None or col_access > last_activity):
                last_activity = col_access
            collections_out.append(
                {
                    "name": name,
                    "created_at": _iso(col.get("created_at")),
                    "last_access_at": _iso(col_access),
                    "document_count": live_count,
                    "storage_bytes": int(col.get("storage_bytes") or 0),
                    "storage_mb": round((col.get("storage_bytes") or 0) / (1024 * 1024), 3),
                    "api_calls": col_calls,
                    "field_count": len(col.get("fields") or []),
                }
            )

        total_documents += doc_count_db
        db_access = doc.get("last_access_at")
        if db_access and (last_activity is None or db_access > last_activity):
            last_activity = db_access

        databases_out.append(
            {
                "id": db_id,
                "display_name": doc.get("displayName"),
                "internal_name": doc.get("dbName"),
                "created_at": _iso(doc.get("created_at")),
                "updated_at": _iso(doc.get("updated_at")),
                "last_access_at": _iso(db_access),
                "stats_updated_at": _iso(doc.get("stats_updated_at")),
                "collection_count": len(collections_out),
                "document_count": doc_count_db,
                "storage_bytes": storage_total,
                "storage_mb": round(storage_total / (1024 * 1024), 2),
                "api_calls": int(db_ops["total"]),
                "operations_by_type": db_ops.get("by_operation", {}),
                "collections": collections_out,
                "trend": trend,
            }
        )

    return {
        "databases": databases_out,
        "totals": {
            "database_count": len(databases_out),
            "collection_count": sum(d["collection_count"] for d in databases_out),
            "document_count": total_documents,
            "storage_data_bytes": total_data_bytes,
            "storage_data_mb": round(total_data_bytes / (1024 * 1024), 2),
            "api_calls": sum(d["api_calls"] for d in databases_out),
            "last_activity_at": _iso(last_activity),
        },
    }
