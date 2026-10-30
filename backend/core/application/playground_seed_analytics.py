"""Synthetic analytics + sample files for playground dashboard charts.

All writes use SYNC_MONGODB_CLIENT only (same constraint as DB seeding).
"""

from __future__ import annotations

import logging
import mimetypes
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from bson import ObjectId
from django.conf import settings

from core.infrastructure.managers import user_manager

logger = logging.getLogger(__name__)

ANALYTICS_DB = "datacube_analytics"
ANALYTICS_COLLECTIONS = (
    "http_requests",
    "db_operations",
    "errors",
    "slow_queries",
    "performance_metrics",
    "mongo_details",
    "client_info",
)

_HTTP_PATHS = (
    "/api/v2/crud/",
    "/api/v2/list_databases/",
    "/api/v2/list_collections/",
    "/api/v2/get_metadata/",
    "/api/v2/create_database/",
    "/api/v2/files/",
    "/core/api/v1/profile/",
    "/analytics/api/v2/dashboard/",
)

_OPS = (
    "document_query",
    "document_insert",
    "document_update",
    "document_deletion",
    "file_list",
    "file_metadata",
)


def _rng(user_id: str) -> random.Random:
    # Stable per user so re-seeds (if ever) look similar; still varied across users.
    return random.Random(f"playground-analytics:{user_id}")


def seed_playground_analytics_sync(
    user_id: str,
    databases: list[dict[str, Any]],
    *,
    days: int = 14,
) -> dict[str, int]:
    """Insert chart-friendly telemetry for the playground overview.

    ``databases`` items: ``{"id": str, "collections": [str, ...]}``.
    """
    if not databases:
        return {"http": 0, "ops": 0, "errors": 0, "slow": 0}

    client = settings.SYNC_MONGODB_CLIENT
    adb = client[ANALYTICS_DB]
    rng = _rng(user_id)
    now = datetime.now(timezone.utc)

    http_docs: list[dict[str, Any]] = []
    op_docs: list[dict[str, Any]] = []
    error_docs: list[dict[str, Any]] = []
    slow_docs: list[dict[str, Any]] = []
    perf_docs: list[dict[str, Any]] = []

    for day_offset in range(days):
        day = now - timedelta(days=days - 1 - day_offset)
        # Weekdays busier than weekends for a natural-looking curve.
        weekday = day.weekday()
        base = 18 if weekday < 5 else 8
        n_http = base + rng.randint(0, 12)
        n_ops = max(4, n_http // 2 + rng.randint(0, 6))

        for _ in range(n_http):
            hour = rng.randint(8, 22)
            minute = rng.randint(0, 59)
            ts = day.replace(hour=hour, minute=minute, second=rng.randint(0, 59), microsecond=0)
            method = rng.choices(
                ["GET", "POST", "PUT", "DELETE"],
                weights=[55, 30, 10, 5],
                k=1,
            )[0]
            path = rng.choice(_HTTP_PATHS)
            # ~8% errors for a visible errors tab without looking broken.
            is_error = rng.random() < 0.08
            if is_error:
                status_code = rng.choice([400, 401, 403, 404, 500, 502])
                success = False
                duration = round(rng.uniform(80, 900), 2)
            else:
                status_code = rng.choice([200, 200, 200, 201, 204])
                success = True
                duration = round(rng.uniform(12, 280), 2)

            http_docs.append(
                {
                    "user_id": user_id,
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "duration_ms": duration,
                    "timestamp": ts,
                    "success": success,
                }
            )
            if is_error and status_code >= 400:
                error_docs.append(
                    {
                        "user_id": user_id,
                        "status_code": status_code,
                        "error_type": "client_error" if status_code < 500 else "server_error",
                        "error_message": f"Sample playground {status_code} on {path}",
                        "timestamp": ts,
                    }
                )

            req_size = rng.randint(120, 8_000)
            resp_size = rng.randint(200, 24_000)
            perf_docs.append(
                {
                    "user_id": user_id,
                    "request_size_bytes": req_size,
                    "response_size_bytes": resp_size,
                    "throughput_bytes_per_sec": round(
                        (req_size + resp_size) / max(duration / 1000.0, 0.001), 2
                    ),
                    "warning": None,
                    "timestamp": ts,
                }
            )

        for _ in range(n_ops):
            hour = rng.randint(8, 22)
            ts = day.replace(hour=hour, minute=rng.randint(0, 59), second=rng.randint(0, 59))
            db = rng.choice(databases)
            coll = rng.choice(db["collections"] or ["system"])
            op = rng.choice(_OPS)
            duration = round(rng.uniform(5, 1_800), 2)
            op_docs.append(
                {
                    "user_id": user_id,
                    "db_id": db["id"],
                    "collection": coll,
                    "operation_type": op,
                    "document_count": rng.randint(1, 12),
                    "query_complexity": rng.choice(["simple", "simple", "moderate"]),
                    "timestamp": ts,
                }
            )
            if duration >= 500 and rng.random() < 0.35:
                slow_docs.append(
                    {
                        "user_id": user_id,
                        "query_details": {
                            "method": "GET" if op == "document_query" else "POST",
                            "path": "/api/v2/crud/",
                            "collection": coll,
                        },
                        "duration_ms": duration,
                        "threshold_ms": 500,
                        "collection": coll,
                        "db_id": db["id"],
                        "timestamp": ts,
                    }
                )

    if http_docs:
        adb["http_requests"].insert_many(http_docs)
    if op_docs:
        adb["db_operations"].insert_many(op_docs)
    if error_docs:
        adb["errors"].insert_many(error_docs)
    if slow_docs:
        adb["slow_queries"].insert_many(slow_docs)
    if perf_docs:
        adb["performance_metrics"].insert_many(perf_docs)

    # Surface usage counter on profile / overview cards.
    user_manager.users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "usage.api_calls_current_month": len(http_docs),
                "updated_at": now,
            }
        },
    )

    return {
        "http": len(http_docs),
        "ops": len(op_docs),
        "errors": len(error_docs),
        "slow": len(slow_docs),
    }


def playground_demo_files_dir() -> Path:
    """``backend/playground_demo_files`` (image/video samples for seeding)."""
    return Path(__file__).resolve().parents[2] / "playground_demo_files"


def _guess_content_type(path: Path) -> str:
    guessed, _ = mimetypes.guess_type(path.name)
    return guessed or "application/octet-stream"


def _list_demo_media_files() -> list[Path]:
    """Prefer known demo names; fall back to any image/video in the folder."""
    root = playground_demo_files_dir()
    if not root.is_dir():
        return []

    preferred = [
        "beautiful-fall-nature-scenery-free-image.jpeg",
        "file_test_demo.mp4",
        "sunset_behind_the_skyline_on_the_beach_over_the_sea.mp4",
    ]
    found: list[Path] = []
    for name in preferred:
        path = root / name
        if path.is_file():
            found.append(path)

    if found:
        return found

    exts = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4", ".webm", ".pdf"}
    return sorted(p for p in root.iterdir() if p.is_file() and p.suffix.lower() in exts)


def seed_playground_sample_files_sync(user_id: str) -> int:
    """Upload real demo media into GridFS + file_metadata for the playground user.

    Sources files from ``backend/playground_demo_files/``. Playground *user*
    uploads stay disabled; seeded files are still streamable via signed URLs.
    """
    paths = _list_demo_media_files()
    if not paths:
        logger.warning(
            "No playground demo media in %s — skipping file seed",
            playground_demo_files_dir(),
        )
        return 0

    from gridfs import GridFSBucket

    client = settings.SYNC_MONGODB_CLIENT
    db_name = settings.FILE_STORAGE_DB_NAME
    if not db_name:
        raise RuntimeError("FILE_STORAGE_DB_NAME is not configured")

    bucket = GridFSBucket(client[db_name], bucket_name="user_storage")
    meta_coll = client[settings.MONGODB_DATABASE]["file_metadata"]
    uid = ObjectId(user_id)
    now = datetime.now(timezone.utc)
    docs: list[dict[str, Any]] = []

    for index, path in enumerate(paths):
        content_type = _guess_content_type(path)
        size = path.stat().st_size
        with path.open("rb") as handle:
            file_id = bucket.upload_from_stream(
                path.name,
                handle,
                metadata={
                    "contentType": content_type,
                    "user_id": user_id,  # match GridFSService (string)
                    "is_playground_sample": True,
                },
            )
        uploaded = now - timedelta(days=2 + index * 3, hours=3)
        docs.append(
            {
                "user_id": uid,
                "file_id": str(file_id),
                "filename": path.name,
                "size": size,
                "content_type": content_type,
                "storage_type": "gridfs",
                "uploaded_at": uploaded,
                "updated_at": uploaded,
                "is_playground_sample": True,
            }
        )

    if docs:
        meta_coll.insert_many(docs)
    return len(docs)


def purge_playground_gridfs(user_id: str) -> int:
    """Delete GridFS objects owned by the playground user."""
    from gridfs import GridFSBucket

    db_name = getattr(settings, "FILE_STORAGE_DB_NAME", None)
    if not db_name:
        return 0

    client = settings.SYNC_MONGODB_CLIENT
    bucket = GridFSBucket(client[db_name], bucket_name="user_storage")
    removed = 0
    # GridFS metadata.user_id is stored as a string by GridFSService / seed.
    for grid_out in bucket.find({"metadata.user_id": user_id}):
        try:
            bucket.delete(grid_out._id)
            removed += 1
        except Exception:
            logger.exception("Failed deleting GridFS file %s for %s", grid_out._id, user_id)
    return removed


def purge_playground_analytics(user_id: str) -> None:
    """Remove seeded (and any real) analytics rows for a playground user."""
    client = settings.SYNC_MONGODB_CLIENT
    adb = client[ANALYTICS_DB]
    for name in ANALYTICS_COLLECTIONS:
        try:
            adb[name].delete_many({"user_id": user_id})
        except Exception:
            logger.exception("Failed clearing analytics.%s for %s", name, user_id)
