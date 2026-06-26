"""Playground session helpers (ephemeral demo users).

These are pure, dependency-light helpers used by the playground service,
views, and authentication layer. They never touch the async Mongo client.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from django.conf import settings
from django.http import HttpRequest


PLAYGROUND_COOKIE = "pg_session"
PLAYGROUND_EMAIL_DOMAIN = "demo.datacube.internal"


def playground_enabled() -> bool:
    return bool(getattr(settings, "PLAYGROUND_ENABLED", False))


def is_playground_user(user_doc: Optional[Dict[str, Any]]) -> bool:
    return bool(user_doc and user_doc.get("is_playground"))


def playground_is_live(user_doc: Optional[Dict[str, Any]]) -> bool:
    """True when the doc is a playground user whose session has not expired."""
    if not is_playground_user(user_doc):
        return False
    expires = user_doc.get("playground_expires_at")
    if expires is None:
        return True
    if isinstance(expires, str):
        try:
            expires = datetime.fromisoformat(expires.replace("Z", "+00:00"))
        except ValueError:
            return True
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    return expires > datetime.now(timezone.utc)


def get_client_ip(request: HttpRequest) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "") or "unknown"


def hash_client_ip(ip: str) -> str:
    pepper = getattr(settings, "SECRET_KEY", "playground-ip-pepper")
    return hashlib.sha256(f"{pepper}:{ip}".encode()).hexdigest()


def new_playground_session_id() -> str:
    return secrets.token_urlsafe(32)


def read_playground_session_id(request: HttpRequest) -> Optional[str]:
    """Resolve a returning session id from cookie, header, or request body."""
    cookie_val = request.COOKIES.get(PLAYGROUND_COOKIE)
    if cookie_val:
        return cookie_val
    header_val = request.META.get("HTTP_X_PLAYGROUND_SESSION")
    if header_val:
        return header_val.strip()
    body_val = getattr(request, "data", None)
    if isinstance(body_val, dict):
        sid = body_val.get("session_id")
        if isinstance(sid, str) and sid.strip():
            return sid.strip()
    return None
