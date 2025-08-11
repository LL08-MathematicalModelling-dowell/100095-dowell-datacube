import secrets
import bcrypt
from datetime import datetime, timedelta, timezone # Import timezone
from bson import ObjectId
from .db import mongo_conn

class UserManager:
    def __init__(self):
        self.users_collection = mongo_conn.get_collection('users')

    def _hash_password(self, password):
        """Hashes the password with a salt."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    def check_password(self, password, hashed_password):
        """Checks a password against a hashed one."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

    def create_user(self, email, first_name, last_name, password):
        """Creates a new user, hashes the password, and saves to DB."""
        if self.users_collection.find_one({"email": email}):
            raise ValueError("User with this email already exists.")

        hashed_password = self._hash_password(password)
        
        user_data = {
            "email": email,
            "firstName": first_name,
            "lastName": last_name,
            "password": hashed_password,
            "is_email_verified": False,
            "email_verification_token": None,
            "email_token_expiry": None,
            "stripe_customer_id": None,
            "subscription_plan": "free", # Default plan
            "subscription_status": "active", # 'active', 'canceled', 'past_due'

            "usage": {
                "api_calls_current_month": 0,
                "last_reset_date": datetime.now(timezone.utc).isoformat()
            }
        }
        
        result = self.users_collection.insert_one(user_data)
        user_data['_id'] = result.inserted_id
        return user_data

    def generate_email_verification_token(self, user_id):
        """Generates a secure token and saves it to the user's document."""
        token = secrets.token_urlsafe(32)
        expiry = datetime.now(timezone.utc) + timedelta(hours=24) # Token is valid for 24 hours

        self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "email_verification_token": token,
                    "email_token_expiry": expiry
                }
            }
        )
        return token

    def verify_email_token(self, token):
        """Finds a user by token, verifies it, and updates their status."""
        user_doc = self.users_collection.find_one({
            "email_verification_token": token,
            "email_token_expiry": {"$gt": datetime.now(timezone.utc)}
        })

        if not user_doc:
            return None # Token is invalid or expired

        # Mark user as verified and clear the token fields
        self.users_collection.update_one(
            {"_id": user_doc["_id"]},
            {
                "$set": {"is_email_verified": True},
                "$unset": {"email_verification_token": "", "email_token_expiry": ""}
            }
        )
        return user_doc

    # def create_user(self, email, first_name, last_name, password):
    #     """Creates a new user, hashes the password, and saves to DB."""
    #     if self.users_collection.find_one({"email": email}):
    #         raise ValueError("User with this email already exists.")

    #     hashed_password = self._hash_password(password)
        
    #     user_data = {
    #         "email": email,
    #         "firstName": first_name,
    #         "lastName": last_name,
    #         "password": hashed_password,
    #     }
        
    #     result = self.users_collection.insert_one(user_data)
    #     user_data['_id'] = result.inserted_id
    #     return user_data

    def get_user_by_email(self, email):
        """Finds a user by their email address."""
        return self.users_collection.find_one({"email": email})

    def get_user_by_id(self, user_id):
        """Finds a user by their MongoDB ObjectId."""
        return self.users_collection.find_one({"_id": ObjectId(user_id)})

# Instantiate the manager
user_manager = UserManager()