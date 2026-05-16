"""Email OTP: generate, hash, verify (bcrypt)."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Literal

import bcrypt
from bson import ObjectId
from bson.binary import Binary

from core.infrastructure.db import mongo_conn

OtpPurpose = Literal["register", "login_email", "reset_password"]

_OTP_TTL_MINUTES = 15
_MAX_ATTEMPTS = 5


def _hash_code(code: str) -> bytes:
    return bcrypt.hashpw(code.strip().encode("utf-8"), bcrypt.gensalt())


def _codes_match(plain: str, stored: bytes) -> bool:
    try:
        return bcrypt.checkpw(plain.strip().encode("utf-8"), stored)
    except Exception:
        return False


def generate_numeric_code(length: int = 6) -> str:
    n = secrets.randbelow(10**length)
    return f"{n:0{length}d}"


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
                "otp_expires_at": datetime.now(timezone.utc) + timedelta(minutes=_OTP_TTL_MINUTES),
                "otp_purpose": purpose,
                "otp_attempts": 0,
                "updated_at": datetime.now(timezone.utc),
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
    if not expires or expires < datetime.now(timezone.utc):
        users.update_one(
            {"_id": user_id},
            {"$unset": {"otp_hash": "", "otp_expires_at": "", "otp_purpose": "", "otp_attempts": ""}},
        )
        return False
    attempts = int(doc.get("otp_attempts") or 0)
    if attempts >= _MAX_ATTEMPTS:
        return False
    otp_hash = doc.get("otp_hash")
    if not otp_hash:
        return False
    if isinstance(otp_hash, Binary):
        otp_hash = bytes(otp_hash)
    elif isinstance(otp_hash, str):
        otp_hash = otp_hash.encode("utf-8")
    if not _codes_match(code, otp_hash):
        users.update_one({"_id": user_id}, {"$inc": {"otp_attempts": 1}})
        return False
    users.update_one(
        {"_id": user_id},
        {"$unset": {"otp_hash": "", "otp_expires_at": "", "otp_purpose": "", "otp_attempts": ""}},
    )
    return True


def clear_otp(user_id: ObjectId) -> None:
    mongo_conn.get_collection("users").update_one(
        {"_id": user_id},
        {"$unset": {"otp_hash": "", "otp_expires_at": "", "otp_purpose": "", "otp_attempts": ""}},
    )
