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

from core.infrastructure.managers import user_manager
from core.infrastructure.playground import (
    PLAYGROUND_EMAIL_DOMAIN,
    hash_client_ip,
    is_playground_user,
    new_playground_session_id,
    playground_is_live,
)

logger = logging.getLogger(__name__)

PLAYGROUND_SEED = {
    "db_name": "demo_store",
    "collections": [
        {
            "name": "products",
            "fields": [
                {"name": "name", "type": "string"},
                {"name": "price", "type": "number"},
                {"name": "in_stock", "type": "boolean"},
            ],
        },
        {
            "name": "orders",
            "fields": [
                {"name": "product", "type": "string"},
                {"name": "quantity", "type": "number"},
                {"name": "status", "type": "string"},
            ],
        },
    ],
    "documents": {
        "products": [
            {"name": "Widget", "price": 9.99, "in_stock": True},
            {"name": "Gadget", "price": 24.5, "in_stock": True},
            {"name": "Legacy part", "price": 4.0, "in_stock": False},
        ],
        "orders": [
            {"product": "Widget", "quantity": 2, "status": "shipped"},
            {"product": "Gadget", "quantity": 1, "status": "pending"},
        ],
    },
}


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

def seed_playground_database_sync(user_id: str) -> None:
    """Provision demo_store using SYNC_MONGODB_CLIENT only.

    Playground start runs in an async adrf view, but seeding must stay on the
    sync PyMongo client. Calling async Mongo from per-request event loops binds
    the global AsyncMongoClient to the wrong loop and breaks analytics/dashboard.
    """
    from api.domain.metadata_models import new_database_metadata
    from api.infrastructure.naming import generate_db_name

    client = settings.SYNC_MONGODB_CLIENT
    meta_coll = client[settings.MONGODB_DATABASE][settings.MONGODB_COLLECTION]

    display_name = PLAYGROUND_SEED["db_name"]
    internal_db_name = generate_db_name(display_name, user_id)
    physical_db = client[internal_db_name]

    for coll_def in PLAYGROUND_SEED["collections"]:
        physical_db.create_collection(coll_def["name"])

    total_docs = 0
    for coll_name, docs in PLAYGROUND_SEED["documents"].items():
        if docs:
            physical_db[coll_name].insert_many([dict(d) for d in docs])
            total_docs += len(docs)

    meta = new_database_metadata(
        user_id=ObjectId(user_id),
        display_name=display_name,
        internal_db_name=internal_db_name,
        collections=PLAYGROUND_SEED["collections"],
    )
    meta_coll.insert_one(meta)

    if total_docs:
        user_manager.increment_playground_document_usage(user_id, total_docs)


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
    """Drop all tenant DBs, metadata, and file records for a playground user."""
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
        _sync_file_metadata_collection().delete_many(
            {"user_id": {"$in": [uid, str(uid)]}}
        )
    except Exception:
        logger.exception("Failed to delete file metadata for user %s", user_id)


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
