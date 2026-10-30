"""Orchestration for ephemeral playground sessions.

Design notes
------------
* Session start runs inside an async adrf view, so seeding uses the existing
  async services (``DatabaseService`` / ``DocumentService``) with ``await`` —
  the same event loop as every other API view. No ``asyncio.run`` /
  ``async_to_sync`` (those spawn a second loop and break the global
  ``AsyncMongoClient``).
* Cleanup runs in a Celery worker and is fully synchronous (sync PyMongo
  client + sync ``user_manager``), so it never depends on an event loop.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple
from uuid import uuid4

from bson import ObjectId
from django.conf import settings
from django.core.cache import cache

from core.application.playground_seed_analytics import (
    purge_playground_analytics,
    purge_playground_gridfs,
    seed_playground_analytics_sync,
    seed_playground_sample_files_sync,
)
from core.infrastructure.managers import user_manager
from core.infrastructure.playground import (
    PLAYGROUND_EMAIL_DOMAIN,
    hash_client_ip,
    is_playground_user,
    new_playground_session_id,
    playground_is_live,
)

logger = logging.getLogger(__name__)

# Seeded when a *new* playground session starts (skipped on resume).
# Keep within PLAYGROUND_MAX_DATABASES / COLLECTIONS / DOCUMENTS.
PLAYGROUND_SEEDS: list[dict[str, Any]] = [
    {
        "db_name": "demo_shop",
        "collections": [
            {
                "name": "products",
                "fields": [
                    {"name": "name", "type": "string"},
                    {"name": "sku", "type": "string"},
                    {"name": "price", "type": "number"},
                    {"name": "in_stock", "type": "boolean"},
                ],
            },
            {
                "name": "orders",
                "fields": [
                    {"name": "sku", "type": "string"},
                    {"name": "quantity", "type": "number"},
                    {"name": "total", "type": "number"},
                    {"name": "status", "type": "string"},
                ],
            },
        ],
        "documents": {
            "products": [
                {"name": "Widget", "sku": "A1", "price": 9.99, "in_stock": True},
                {"name": "Gadget", "sku": "B2", "price": 24.5, "in_stock": True},
                {"name": "Legacy part", "sku": "C3", "price": 4.0, "in_stock": False},
            ],
            "orders": [
                {"sku": "A1", "quantity": 2, "total": 19.98, "status": "shipped"},
                {"sku": "B2", "quantity": 1, "total": 24.5, "status": "pending"},
                {"sku": "A1", "quantity": 5, "total": 49.95, "status": "processing"},
                {"sku": "C3", "quantity": 3, "total": 12.0, "status": "cancelled"},
                {"sku": "B2", "quantity": 2, "total": 49.0, "status": "shipped"},
            ],
        },
    },
    {
        "db_name": "demo_blog",
        "collections": [
            {
                "name": "posts",
                "fields": [
                    {"name": "title", "type": "string"},
                    {"name": "author", "type": "string"},
                    {"name": "published", "type": "boolean"},
                ],
            },
            {
                "name": "comments",
                "fields": [
                    {"name": "post_title", "type": "string"},
                    {"name": "body", "type": "string"},
                ],
            },
        ],
        "documents": {
            "posts": [
                {
                    "title": "Welcome to Datacube",
                    "author": "Playground",
                    "published": True,
                },
                {
                    "title": "Draft: API tips",
                    "author": "Playground",
                    "published": False,
                },
                {
                    "title": "Files & media in one API",
                    "author": "Playground",
                    "published": True,
                },
            ],
            "comments": [
                {
                    "post_title": "Welcome to Datacube",
                    "body": "Great starting point for exploring the API.",
                },
                {
                    "post_title": "Welcome to Datacube",
                    "body": "Try editing this document from the dashboard.",
                },
                {
                    "post_title": "Files & media in one API",
                    "body": "Charts look better with sample traffic — thanks!",
                },
            ],
        },
    },
    {
        "db_name": "demo_crm",
        "collections": [
            {
                "name": "contacts",
                "fields": [
                    {"name": "name", "type": "string"},
                    {"name": "email", "type": "string"},
                    {"name": "company", "type": "string"},
                    {"name": "status", "type": "string"},
                ],
            },
        ],
        "documents": {
            "contacts": [
                {
                    "name": "Ada Lovelace",
                    "email": "ada@example.com",
                    "company": "Analytical Engines",
                    "status": "lead",
                },
                {
                    "name": "Alan Turing",
                    "email": "alan@example.com",
                    "company": "Bletchley Labs",
                    "status": "customer",
                },
                {
                    "name": "Grace Hopper",
                    "email": "grace@example.com",
                    "company": "Compiler Co",
                    "status": "prospect",
                },
                {
                    "name": "Katherine Johnson",
                    "email": "katherine@example.com",
                    "company": "Flight Dynamics",
                    "status": "customer",
                },
                {
                    "name": "Margaret Hamilton",
                    "email": "margaret@example.com",
                    "company": "Apollo Soft",
                    "status": "lead",
                },
            ],
        },
    },
]

# Backward-compatible alias (first seed DB) for older imports/docs.
PLAYGROUND_SEED = PLAYGROUND_SEEDS[0]


class PlaygroundCapacityError(Exception):
    """Raised when global or per-IP playground limits are exceeded."""


# --- Settings helpers -------------------------------------------------------

def _ttl_hours() -> int:
    return int(getattr(settings, "PLAYGROUND_SESSION_TTL_HOURS", 3))


def _max_global() -> int:
    return int(getattr(settings, "PLAYGROUND_MAX_ACTIVE_SESSIONS", 500))


def _max_per_ip() -> int:
    return int(getattr(settings, "PLAYGROUND_MAX_SESSIONS_PER_IP", 3))


def _start_attempts_per_hour() -> int:
    return int(getattr(settings, "PLAYGROUND_START_ATTEMPTS_PER_HOUR", 20))


# --- Abuse controls (sync) --------------------------------------------------

def assert_playground_start_rate_limit(ip: str) -> None:
    """Cache-based rate limit (DRF throttles don't play well with adrf async views)."""
    limit = _start_attempts_per_hour()
    if limit <= 0:
        return
    key = f"playground_start:{hash_client_ip(ip)}"
    count = cache.get(key, 0)
    if count >= limit:
        raise PlaygroundCapacityError(
            "Too many playground start attempts from your network. Try again later."
        )
    cache.set(key, count + 1, timeout=3600)


def assert_can_start_playground(ip_hash: str) -> None:
    if user_manager.count_live_playground_sessions() >= _max_global():
        raise PlaygroundCapacityError(
            "Playground is at capacity. Please try again later or sign up for a free account."
        )
    if user_manager.count_live_playground_sessions_by_ip(ip_hash) >= _max_per_ip():
        raise PlaygroundCapacityError(
            "Too many active playground sessions from your network. Try again later."
        )


def start_or_resume_playground(
    *,
    session_id: Optional[str],
    ip: str,
    user_agent: str,
) -> Tuple[Dict[str, Any], bool]:
    """Return ``(user_doc, reused)``; creates a session + user when needed.

    Pure sync (PyMongo + cache); safe to call from an async view.
    """
    if session_id:
        existing = user_manager.get_playground_user_by_session(session_id)
        if existing and playground_is_live(existing):
            user_manager.touch_playground_session(existing["_id"])
            return existing, True

    ip_hash = hash_client_ip(ip)
    assert_can_start_playground(ip_hash)
    assert_playground_start_rate_limit(ip)

    session_id = session_id or new_playground_session_id()
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=_ttl_hours())
    email = f"playground-{uuid4().hex[:12]}@{PLAYGROUND_EMAIL_DOMAIN}"

    user_doc = user_manager.create_playground_user(
        email=email,
        session_id=session_id,
        ip_hash=ip_hash,
        user_agent=(user_agent or "")[:512],
        expires_at=expires,
    )
    return user_doc, False


# --- Seeding (sync — must not touch AsyncMongoClient) -----------------------

def _seed_one_database_sync(user_id: str, seed: dict[str, Any]) -> dict[str, Any]:
    """Create one logical DB + collections + docs.

    Returns ``{id, collections, document_count}`` for analytics seeding.
    """
    from api.domain.metadata_models import new_database_metadata
    from api.infrastructure.naming import generate_db_name

    client = settings.SYNC_MONGODB_CLIENT
    meta_coll = client[settings.MONGODB_DATABASE][settings.MONGODB_COLLECTION]

    display_name = seed["db_name"]
    internal_db_name = generate_db_name(display_name, user_id)
    physical_db = client[internal_db_name]
    now = datetime.now(timezone.utc)

    collection_names: list[str] = []
    total_docs = 0
    storage_total = 0
    collection_stats: list[dict[str, Any]] = []

    for coll_def in seed["collections"]:
        name = coll_def["name"]
        physical_db.create_collection(name)
        collection_names.append(name)
        docs = list((seed.get("documents") or {}).get(name) or [])
        if docs:
            physical_db[name].insert_many([dict(d) for d in docs])
            total_docs += len(docs)
        # Rough size estimate so inventory storage cards aren't all zeros.
        approx_bytes = max(len(docs) * 420, 1_024)
        storage_total += approx_bytes
        collection_stats.append(
            {
                "name": name,
                "document_count_cached": len(docs),
                "storage_bytes": approx_bytes,
                "last_access_at": now,
            }
        )

    meta = new_database_metadata(
        user_id=ObjectId(user_id),
        display_name=display_name,
        internal_db_name=internal_db_name,
        collections=seed["collections"],
    )
    # Overlay live-ish stats used by analytics inventory / storage totals.
    for col_meta in meta.get("collections") or []:
        for stats in collection_stats:
            if stats["name"] == col_meta.get("name"):
                col_meta["document_count_cached"] = stats["document_count_cached"]
                col_meta["storage_bytes"] = stats["storage_bytes"]
                col_meta["last_access_at"] = stats["last_access_at"]
                break
    meta["storage_bytes_total"] = storage_total
    meta["stats_updated_at"] = now
    meta["last_access_at"] = now

    result = meta_coll.insert_one(meta)
    return {
        "id": str(result.inserted_id),
        "collections": collection_names,
        "document_count": total_docs,
    }


def seed_playground_database_sync(user_id: str) -> None:
    """Provision sample databases, files metadata, and chart telemetry.

    Uses SYNC_MONGODB_CLIENT only — calling async Mongo from per-request event
    loops binds the global AsyncMongoClient to the wrong loop and breaks
    analytics/dashboard.
    """
    total_docs = 0
    seeded_dbs: list[dict[str, Any]] = []
    for seed in PLAYGROUND_SEEDS:
        info = _seed_one_database_sync(user_id, seed)
        total_docs += int(info["document_count"])
        seeded_dbs.append({"id": info["id"], "collections": info["collections"]})

    if total_docs:
        user_manager.increment_playground_document_usage(user_id, total_docs)

    try:
        files_n = seed_playground_sample_files_sync(user_id)
        logger.info("Playground sample files seeded for %s: %s", user_id, files_n)
    except Exception:
        logger.exception("Playground sample file seed failed for %s", user_id)

    try:
        counts = seed_playground_analytics_sync(user_id, seeded_dbs)
        logger.info("Playground analytics seeded for %s: %s", user_id, counts)
    except Exception:
        logger.exception("Playground analytics seed failed for %s", user_id)


async def seed_playground_database(user_id: str) -> None:
    """Async alias kept for tests; production path uses sync seeding."""
    seed_playground_database_sync(user_id)


# --- Limit enforcement (async, called from services) ------------------------

async def enforce_playground_database_limit(user_id: str) -> None:
    from api.application.metadata_service import MetadataService

    doc = user_manager.get_user_by_id(user_id)
    if not is_playground_user(doc):
        return
    max_dbs = int(getattr(settings, "PLAYGROUND_MAX_DATABASES", 1))
    meta_svc = MetadataService(user_id=user_id)
    total, _ = await meta_svc.list_databases_paginated(page=1, page_size=max_dbs + 1)
    if total >= max_dbs:
        raise ValueError(
            f"Playground accounts are limited to {max_dbs} database(s). Sign up to create more."
        )


async def enforce_playground_collection_limit(user_id: str, db_id: str, adding: int) -> None:
    from api.application.metadata_service import MetadataService

    doc = user_manager.get_user_by_id(user_id)
    if not is_playground_user(doc):
        return
    max_cols = int(getattr(settings, "PLAYGROUND_MAX_COLLECTIONS", 3))
    meta_svc = MetadataService(user_id=user_id)
    meta = await meta_svc.get_db(db_id)
    if not meta:
        return
    current = len(meta.get("collections") or [])
    if current + adding > max_cols:
        raise ValueError(
            f"Playground accounts are limited to {max_cols} collections per database."
        )


async def enforce_playground_document_limit(user_id: str, adding: int) -> None:
    doc = user_manager.get_user_by_id(user_id)
    if not is_playground_user(doc):
        return
    max_docs = int(getattr(settings, "PLAYGROUND_MAX_DOCUMENTS", 100))
    usage = int((doc.get("playground_usage") or {}).get("documents", 0))
    if usage + adding > max_docs:
        raise ValueError(
            f"Playground accounts are limited to {max_docs} documents. Sign up for a full account."
        )
    user_manager.increment_playground_document_usage(user_id, adding)


def assert_playground_can_use_api_keys(user_id: str) -> None:
    doc = user_manager.get_user_by_id(user_id)
    if is_playground_user(doc):
        raise ValueError(
            "API keys are not available in playground mode. Create a free account to continue."
        )


def assert_playground_can_upload_files(user_id: str) -> None:
    doc = user_manager.get_user_by_id(user_id)
    if is_playground_user(doc):
        raise ValueError("File uploads are disabled in playground mode.")


# --- Cleanup (sync, Celery worker) ------------------------------------------

def _sync_metadata_collection():
    return settings.SYNC_MONGODB_CLIENT[settings.MONGODB_DATABASE][settings.MONGODB_COLLECTION]


def _sync_file_metadata_collection():
    return settings.SYNC_MONGODB_CLIENT[settings.MONGODB_DATABASE]["file_metadata"]


def purge_playground_user_data(user_id: str) -> None:
    """Drop tenant DBs, metadata, files, and analytics for a playground user."""
    uid = ObjectId(user_id)
    meta_coll = _sync_metadata_collection()
    client = settings.SYNC_MONGODB_CLIENT

    for meta in meta_coll.find({"user_id": uid}):
        db_name = meta.get("dbName")
        if db_name:
            try:
                client.drop_database(db_name)
            except Exception:
                logger.exception("Failed to drop tenant DB %s", db_name)
        meta_coll.delete_one({"_id": meta["_id"]})

    try:
        purge_playground_gridfs(user_id)
    except Exception:
        logger.exception("Failed to delete GridFS files for user %s", user_id)

    try:
        _sync_file_metadata_collection().delete_many(
            {"user_id": {"$in": [uid, str(uid)]}}
        )
    except Exception:
        logger.exception("Failed to delete file metadata for user %s", user_id)

    try:
        purge_playground_analytics(user_id)
    except Exception:
        logger.exception("Failed to delete analytics for user %s", user_id)


def cleanup_expired_playground_sessions() -> int:
    """Find expired playground users, purge their data, delete the user."""
    expired = user_manager.list_expired_playground_users()
    removed = 0
    for doc in expired:
        uid = str(doc["_id"])
        try:
            purge_playground_user_data(uid)
        except Exception:
            logger.exception("Failed to purge playground data for user %s", uid)
        user_manager.hard_delete_user(doc["_id"])
        removed += 1
    return removed
