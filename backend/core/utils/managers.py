import bcrypt
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
        }
        
        result = self.users_collection.insert_one(user_data)
        user_data['_id'] = result.inserted_id
        return user_data

    def get_user_by_email(self, email):
        """Finds a user by their email address."""
        return self.users_collection.find_one({"email": email})

    def get_user_by_id(self, user_id):
        """Finds a user by their MongoDB ObjectId."""
        return self.users_collection.find_one({"_id": ObjectId(user_id)})

# Instantiate the manager
user_manager = UserManager()