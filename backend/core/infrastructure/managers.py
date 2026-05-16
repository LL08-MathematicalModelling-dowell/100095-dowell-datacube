import secrets
import bcrypt
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from gridfs import GridFSBucket
from gridfs.errors import NoFile

from core.infrastructure.db import mongo_conn
from core.infrastructure.roles import DEFAULT_ROLE, normalize_role


class UserManager:
    def __init__(self):
        self.users_collection = mongo_conn.get_collection("users")

    def avatar_bucket(self) -> GridFSBucket:
        return GridFSBucket(mongo_conn.db, bucket_name="avatars")

    def _hash_password(self, password):
        """Hashes the password with a salt."""
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    def hash_pass(self, password):
        return self._hash_password(password)

    def check_password(self, password, hashed_password):
        """Checks a password against a hashed one."""
        if hashed_password is None:
            return False
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password)

    def create_user(self, email, first_name, last_name, password, *, role=None):
        """Creates a new user with password; email must be verified via OTP before full API access."""
        if self.users_collection.find_one({"email": email, "deleted_at": None}):
            raise ValueError("User with this email already exists.")
        if password is None:
            raise ValueError("Password is required.")
        hashed_password = self._hash_password(password)
        now = datetime.now(timezone.utc)
        user_data = {
            "email": email,
            "firstName": first_name,
            "lastName": last_name,
            "password": hashed_password,
            "is_email_verified": False,
            "email_verification_token": None,
            "email_token_expiry": None,
            "auth_schema_version": 2,
            "auth_method": "password",
            "role": normalize_role(role) if role else DEFAULT_ROLE,
            "auth_providers": [],
            "avatar_file_id": None,
            "stripe_customer_id": None,
            "subscription_plan": "free",
            "subscription_status": "active",
            "usage": {
                "api_calls_current_month": 0,
                "last_reset_date": now.isoformat(),
            },
            "created_at": now,
            "updated_at": now,
        }
        result = self.users_collection.insert_one(user_data)
        user_data["_id"] = result.inserted_id
        return user_data

    def create_email_only_user(self, email, first_name="", last_name="", *, role=None):
        """User without password (magic OTP / future OAuth-only path)."""
        if self.users_collection.find_one({"email": email, "deleted_at": None}):
            raise ValueError("User with this email already exists.")
        now = datetime.now(timezone.utc)
        user_data = {
            "email": email,
            "firstName": first_name or email.split("@")[0],
            "lastName": last_name or "",
            "password": None,
            "is_email_verified": False,
            "email_verification_token": None,
            "email_token_expiry": None,
            "auth_schema_version": 2,
            "auth_method": "email_otp",
            "role": normalize_role(role) if role else DEFAULT_ROLE,
            "auth_providers": [],
            "avatar_file_id": None,
            "stripe_customer_id": None,
            "subscription_plan": "free",
            "subscription_status": "active",
            "usage": {
                "api_calls_current_month": 0,
                "last_reset_date": now.isoformat(),
            },
            "created_at": now,
            "updated_at": now,
        }
        result = self.users_collection.insert_one(user_data)
        user_data["_id"] = result.inserted_id
        return user_data

    def upsert_oauth_user(
        self,
        email: str,
        first_name: str,
        last_name: str,
        provider: str,
        provider_sub: str,
        *,
        role=None,
    ):
        """
        Creates or updates user from OAuth. Email is treated as verified when provider asserts it.
        """
        now = datetime.now(timezone.utc)
        existing = self.users_collection.find_one({"email": email, "deleted_at": None})
        provider_entry = {"provider": provider, "sub": provider_sub, "linked_at": now}
        if existing:
            providers = list(existing.get("auth_providers") or [])
            pair = (provider, provider_sub)
            if not any((p.get("provider"), p.get("sub")) == pair for p in providers):
                providers.append(provider_entry)
            self.users_collection.update_one(
                {"_id": existing["_id"]},
                {
                    "$set": {
                        "is_email_verified": True,
                        "firstName": first_name or existing.get("firstName"),
                        "lastName": last_name or existing.get("lastName"),
                        "auth_providers": providers,
                        "updated_at": now,
                    },
                },
            )
            return self.users_collection.find_one({"_id": existing["_id"]})
        user_data = {
            "email": email,
            "firstName": first_name or email.split("@")[0],
            "lastName": last_name or "",
            "password": None,
            "is_email_verified": True,
            "email_verification_token": None,
            "email_token_expiry": None,
            "auth_schema_version": 2,
            "auth_method": provider,
            "role": normalize_role(role) if role else DEFAULT_ROLE,
            "auth_providers": [provider_entry],
            "avatar_file_id": None,
            "stripe_customer_id": None,
            "subscription_plan": "free",
            "subscription_status": "active",
            "usage": {"api_calls_current_month": 0, "last_reset_date": now.isoformat()},
            "created_at": now,
            "updated_at": now,
        }
        result = self.users_collection.insert_one(user_data)
        user_data["_id"] = result.inserted_id
        return user_data

    def set_email_verified(self, user_id: ObjectId, verified: bool = True):
        self.users_collection.update_one(
            {"_id": user_id},
            {"$set": {"is_email_verified": verified, "updated_at": datetime.now(timezone.utc)}},
        )

    def update_profile(self, user_id: ObjectId, *, first_name=None, last_name=None):
        patch = {"updated_at": datetime.now(timezone.utc)}
        if first_name is not None:
            patch["firstName"] = first_name
        if last_name is not None:
            patch["lastName"] = last_name
        self.users_collection.update_one({"_id": user_id}, {"$set": patch})

    def set_avatar(self, user_id: ObjectId, file_id: ObjectId):
        self.users_collection.update_one(
            {"_id": user_id},
            {"$set": {"avatar_file_id": file_id, "updated_at": datetime.now(timezone.utc)}},
        )

    def soft_delete_user(self, user_id: ObjectId):
        now = datetime.now(timezone.utc)
        self.users_collection.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "deleted_at": now,
                    "updated_at": now,
                    "password": None,
                },
                "$unset": {
                    "email_verification_token": "",
                    "email_token_expiry": "",
                    "password_reset_token": "",
                    "password_reset_expiry": "",
                    "otp_hash": "",
                    "otp_expires_at": "",
                    "otp_purpose": "",
                    "otp_attempts": "",
                },
            },
        )

    def remove_avatar_file(self, user_id: ObjectId):
        doc = self.users_collection.find_one({"_id": user_id})
        if not doc or not doc.get("avatar_file_id"):
            return
        try:
            self.avatar_bucket().delete(doc["avatar_file_id"])
        except (NoFile, Exception):
            pass
        self.users_collection.update_one(
            {"_id": user_id},
            {"$set": {"avatar_file_id": None, "updated_at": datetime.now(timezone.utc)}},
        )

    def generate_email_verification_token(self, user_id):
        """Generates a secure token and saves it to the user's document."""
        token = secrets.token_urlsafe(32)
        expiry = datetime.now(timezone.utc) + timedelta(hours=24)

        self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"email_verification_token": token, "email_token_expiry": expiry}},
        )
        return token

    def verify_email_token(self, token):
        """Finds a user by token, verifies it, and updates their status."""
        user_doc = self.users_collection.find_one(
            {
                "email_verification_token": token,
                "email_token_expiry": {"$gt": datetime.now(timezone.utc)},
                "deleted_at": None,
            }
        )

        if not user_doc:
            return None

        self.users_collection.update_one(
            {"_id": user_doc["_id"]},
            {
                "$set": {"is_email_verified": True},
                "$unset": {"email_verification_token": "", "email_token_expiry": ""},
            },
        )
        return user_doc

    def get_user_by_email(self, email):
        return self.users_collection.find_one({"email": email, "deleted_at": None})

    def get_user_by_id(self, user_id):
        return self.users_collection.find_one({"_id": ObjectId(user_id), "deleted_at": None})

    def generate_password_reset_token(self, user_id):
        token = secrets.token_urlsafe(32)
        expiry = datetime.now(timezone.utc) + timedelta(hours=1)

        self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"password_reset_token": token, "password_reset_expiry": expiry}},
        )
        return token

    def verify_password_reset_token(self, token):
        user_doc = self.users_collection.find_one(
            {
                "password_reset_token": token,
                "password_reset_expiry": {"$gt": datetime.now(timezone.utc)},
                "deleted_at": None,
            }
        )
        return user_doc

    def clear_password_reset_token(self, user_id):
        self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$unset": {"password_reset_token": "", "password_reset_expiry": ""}},
        )

    def ensure_verified_demo_user(self, email: str):
        """Create or upgrade a local demo account (verified, passwordless)."""
        from core.infrastructure.user_access import effective_email_verified

        doc = self.users_collection.find_one({"email": email, "deleted_at": None})
        if doc:
            if not effective_email_verified(doc):
                self.set_email_verified(doc["_id"], True)
            return self.users_collection.find_one({"_id": doc["_id"]})

        now = datetime.now(timezone.utc)
        user_data = {
            "email": email,
            "firstName": "Demo",
            "lastName": "User",
            "password": None,
            "is_email_verified": True,
            "email_verification_token": None,
            "email_token_expiry": None,
            "auth_schema_version": 2,
            "auth_method": "demo",
            "role": DEFAULT_ROLE,
            "auth_providers": [],
            "avatar_file_id": None,
            "stripe_customer_id": None,
            "subscription_plan": "free",
            "subscription_status": "active",
            "usage": {
                "api_calls_current_month": 0,
                "last_reset_date": now.isoformat(),
            },
            "created_at": now,
            "updated_at": now,
        }
        result = self.users_collection.insert_one(user_data)
        user_data["_id"] = result.inserted_id
        return user_data


user_manager = UserManager()
