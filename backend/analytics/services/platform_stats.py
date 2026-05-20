"""
Read-side aggregations across metadata DB and auth user documents.

Used by analytics dashboard endpoints (not written to datacube_analytics).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

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


async def aggregate_metadata_storage_totals(user_id: str) -> dict[str, int]:
    """Sum cached storage_bytes_total across user databases."""
    coll = settings.METADATA_COLLECTION
    pipeline = [
        {"$match": {"user_id": _user_oid(user_id)}},
        {
            "$group": {
                "_id": None,
                "storage_bytes": {"$sum": {"$ifNull": ["$storage_bytes_total", 0]}},
            }
        },
    ]
    cursor = await coll.aggregate(pipeline)
    rows = await cursor.to_list(length=1)
    if not rows:
        return {"storage_data_bytes": 0}
    return {"storage_data_bytes": int(rows[0].get("storage_bytes") or 0)}


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
            "kind": "files",
        }
        for row in rows
    ]


async def aggregate_http_methods(
    user_id: str,
    *,
    start: datetime,
    end: datetime,
) -> dict[str, int]:
    """HTTP request counts by method."""
    coll = settings.MONGODB_CLIENT["datacube_analytics"]["http_requests"]
    pipeline = [
        {"$match": {"user_id": user_id, "timestamp": {"$gte": start, "$lte": end}}},
        {"$group": {"_id": "$method", "count": {"$sum": 1}}},
    ]
    cursor = await coll.aggregate(pipeline)
    rows = await cursor.to_list(length=20)
    return {row["_id"]: int(row["count"]) for row in rows}


async def aggregate_http_summary(
    user_id: str,
    *,
    start: datetime,
    end: datetime,
) -> dict[str, Any]:
    """Totals and daily series for HTTP traffic in the period."""
    coll = settings.MONGODB_CLIENT["datacube_analytics"]["http_requests"]
    match = {"user_id": user_id, "timestamp": {"$gte": start, "$lte": end}}

    pipeline_totals = [
        {"$match": match},
        {
            "$group": {
                "_id": None,
                "total_requests": {"$sum": 1},
                "avg_duration_ms": {"$avg": "$duration_ms"},
                "error_count": {
                    "$sum": {"$cond": [{"$eq": ["$success", False]}, 1, 0]}
                },
            }
        },
    ]
    cursor = await coll.aggregate(pipeline_totals)
    rows = await cursor.to_list(length=1)
    total_requests = int(rows[0]["total_requests"]) if rows else 0
    avg_duration = round(float(rows[0]["avg_duration_ms"] or 0), 2) if rows else 0
    error_count = int(rows[0]["error_count"]) if rows else 0
    error_rate = round((error_count / total_requests) * 100, 2) if total_requests else 0

    pipeline_daily = [
        {"$match": match},
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                "count": {"$sum": 1},
                "avg_duration": {"$avg": "$duration_ms"},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    cursor2 = await coll.aggregate(pipeline_daily)
    daily_data = await cursor2.to_list(length=100)

    return {
        "total_requests": total_requests,
        "avg_response_time_ms": avg_duration,
        "error_rate_percent": error_rate,
        "daily_requests": {
            "dates": [d["_id"] for d in daily_data],
            "counts": [int(d["count"]) for d in daily_data],
            "avg_durations_ms": [round(float(d["avg_duration"] or 0), 2) for d in daily_data],
        },
    }


async def count_slow_queries(
    user_id: str,
    *,
    start: datetime,
    end: datetime,
) -> int:
    coll = settings.MONGODB_CLIENT["datacube_analytics"]["slow_queries"]
    return await coll.count_documents(
        {"user_id": user_id, "timestamp": {"$gte": start, "$lte": end}}
    )


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


async def aggregate_top_collections_scoped(
    user_id: str,
    *,
    start: datetime,
    end: datetime,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Top collections by operation count, including db_id."""
    coll = settings.MONGODB_CLIENT["datacube_analytics"]["db_operations"]
    pipeline = [
        {
            "$match": {
                "user_id": user_id,
                "timestamp": {"$gte": start, "$lte": end},
                "collection": {"$exists": True, "$nin": [None, "", "system"]},
            }
        },
        {
            "$group": {
                "_id": {"db_id": "$db_id", "collection": "$collection"},
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"count": -1}},
        {"$limit": limit},
    ]
    cursor = await coll.aggregate(pipeline)
    rows = await cursor.to_list(length=limit)
    return [
        {
            "db_id": r["_id"].get("db_id"),
            "name": r["_id"].get("collection"),
            "operations": int(r["count"]),
        }
        for r in rows
    ]
