"""Email OTP: generate, hash (pepper + SHA-256), verify."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Literal

from bson import ObjectId
from django.conf import settings

from core.infrastructure.db import mongo_conn

OtpPurpose = Literal["register", "login_email", "reset_password"]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc_aware(value: datetime) -> datetime:
    """MongoDB often returns naive datetimes; treat them as UTC for comparisons."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _otp_length() -> int:
    return int(getattr(settings, "OTP_LENGTH", 6))


def _otp_expires_minutes() -> int:
    return int(getattr(settings, "OTP_EXPIRES_MINUTES", 10))


def _otp_max_attempts() -> int:
    return int(getattr(settings, "OTP_MAX_ATTEMPTS", 5))


def _otp_pepper() -> bytes:
    pepper = getattr(settings, "OTP_PEPPER", "") or ""
    return str(pepper).encode("utf-8")


def _hash_code(code: str) -> str:
    """Salt the code with the server-side pepper and hash with SHA-256."""
    return hashlib.sha256(_otp_pepper() + code.strip().encode("utf-8")).hexdigest()


def _codes_match(code: str, code_hash: str) -> bool:
    return hmac.compare_digest(_hash_code(code), code_hash)


def generate_numeric_code(length: int | None = None) -> str:
    n = length if length is not None else _otp_length()
    upper = 10**n
    return f"{secrets.randbelow(upper):0{n}d}"


def save_otp_challenge(
    *,
    user_id: ObjectId,
    purpose: OtpPurpose,
    code: str,
) -> None:
    users = mongo_conn.get_collection("users")
    users.update_one(
        {"_id": user_id},
        {
            "$set": {
                "otp_hash": _hash_code(code),
                "otp_expires_at": _utc_now() + timedelta(minutes=_otp_expires_minutes()),
                "otp_purpose": purpose,
                "otp_attempts": 0,
                "updated_at": _utc_now(),
            }
        },
    )


def verify_otp_challenge(*, user_id: ObjectId, purpose: OtpPurpose, code: str) -> bool:
    users = mongo_conn.get_collection("users")
    doc = users.find_one({"_id": user_id})
    if not doc:
        return False
    if doc.get("otp_purpose") != purpose:
        return False

    expires = doc.get("otp_expires_at")
    if not expires or _as_utc_aware(expires) < _utc_now():
        clear_otp(user_id)
        return False

    attempts = int(doc.get("otp_attempts") or 0)
    max_attempts = _otp_max_attempts()
    if attempts >= max_attempts:
        clear_otp(user_id)
        return False

    otp_hash = doc.get("otp_hash")
    if not otp_hash:
        return False
    if not isinstance(otp_hash, str):
        otp_hash = str(otp_hash)

    if not _codes_match(code, otp_hash):
        new_attempts = attempts + 1
        if new_attempts >= max_attempts:
            clear_otp(user_id)
        else:
            users.update_one({"_id": user_id}, {"$inc": {"otp_attempts": 1}})
        return False

    clear_otp(user_id)
    return True


def clear_otp(user_id: ObjectId) -> None:
    mongo_conn.get_collection("users").update_one(
        {"_id": user_id},
        {"$unset": {"otp_hash": "", "otp_expires_at": "", "otp_purpose": "", "otp_attempts": ""}},
    )
