"""
Read-side aggregations across metadata DB and auth user documents.

Used by analytics dashboard endpoints (not written to datacube_analytics).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from bson import ObjectId
from django.conf import settings

from core.infrastructure.managers import user_manager


def _user_oid(user_id: str) -> ObjectId:
    return ObjectId(user_id)


async def aggregate_file_storage(user_id: str) -> dict[str, Any]:
    """Total bytes and file count from METADATA_DB.file_metadata."""
    coll = settings.FILE_METADATA_COLLECTION
    pipeline = [
        {"$match": {"user_id": _user_oid(user_id)}},
        {
            "$group": {
                "_id": None,
                "total_bytes": {"$sum": "$size"},
                "file_count": {"$sum": 1},
            }
        },
    ]
    cursor = await coll.aggregate(pipeline)
    rows = await cursor.to_list(length=1)
    if not rows:
        return {"total_bytes": 0, "file_count": 0}
    return {
        "total_bytes": int(rows[0].get("total_bytes") or 0),
        "file_count": int(rows[0].get("file_count") or 0),
    }


async def aggregate_metadata_counts(user_id: str) -> dict[str, int]:
    """Logical database and collection counts for the user."""
    coll = settings.METADATA_COLLECTION
    uid = _user_oid(user_id)
    database_count = await coll.count_documents({"user_id": uid})
    cursor = await coll.aggregate(
        [
            {"$match": {"user_id": uid}},
            {
                "$project": {
                    "n": {"$size": {"$ifNull": ["$collections", []]}},
                }
            },
            {"$group": {"_id": None, "collection_count": {"$sum": "$n"}}},
        ]
    )
    rows = await cursor.to_list(length=1)
    collection_count = int(rows[0]["collection_count"]) if rows else 0
    return {
        "database_count": database_count,
        "collection_count": collection_count,
    }


async def file_storage_trend(
    user_id: str,
    *,
    start: datetime,
    end: datetime,
) -> list[dict[str, Any]]:
    """Daily uploaded bytes (from file metadata uploaded_at)."""
    coll = settings.FILE_METADATA_COLLECTION
    pipeline = [
        {
            "$match": {
                "user_id": _user_oid(user_id),
                "uploaded_at": {"$gte": start, "$lte": end},
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$uploaded_at"}
                },
                "total_bytes": {"$sum": "$size"},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    cursor = await coll.aggregate(pipeline)
    rows = await cursor.to_list(length=100)
    return [
        {
            "date": row["_id"],
            "storage_mb": round((row.get("total_bytes") or 0) / (1024 * 1024), 2),
        }
        for row in rows
    ]


async def aggregate_http_methods(user_id: str, *, days: int = 7) -> dict[str, int]:
    """HTTP request counts by method (last N days)."""
    coll = settings.MONGODB_CLIENT["datacube_analytics"]["http_requests"]
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    pipeline = [
        {"$match": {"user_id": user_id, "timestamp": {"$gte": start, "$lte": end}}},
        {"$group": {"_id": "$method", "count": {"$sum": 1}}},
    ]
    cursor = await coll.aggregate(pipeline)
    rows = await cursor.to_list(length=20)
    return {row["_id"]: int(row["count"]) for row in rows}


async def count_slow_queries(user_id: str, *, days: int = 7) -> int:
    coll = settings.MONGODB_CLIENT["datacube_analytics"]["slow_queries"]
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    return await coll.count_documents({"user_id": user_id, "timestamp": {"$gte": start, "$lte": end}})


def get_usage_snapshot(user_id: str) -> dict[str, Any]:
    """API call usage from the auth user document."""
    doc = user_manager.get_user_by_id(user_id)
    if not doc:
        return {}
    usage = doc.get("usage") or {}
    plan = doc.get("subscription_plan", "free")
    return {
        "subscription_plan": plan,
        "api_calls_current_month": usage.get("api_calls_current_month", 0),
        "last_reset_date": usage.get("last_reset_date"),
        "role": doc.get("role", "developer"),
    }
