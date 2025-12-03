import secrets
from datetime import datetime
from bson import ObjectId
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions
from core.utils.managers import user_manager
from core.utils.db import mongo_conn


class MongoUser:
    """A proxy class for the user data retrieved from MongoDB."""
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.pk = self.id
        self.email = user_data.get('email')
        self.firstName = user_data.get('firstName')
        self.lastName = user_data.get('lastName')
        self._is_authenticated = True

    @property
    def is_authenticated(self):
        return self._is_authenticated


class CustomJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication backend.
    It overrides the `get_user` method to fetch user from MongoDB.
    """
    def get_user(self, validated_token):
        """
        Attempts to find and return a user using the given validated token.
        """
        try:
            user_id = validated_token['user_id']
            user_doc = user_manager.get_user_by_id(user_id)
            if user_doc:
                return MongoUser(user_doc)
        except KeyError:
            raise exceptions.AuthenticationFailed('Invalid token, no user_id found.')
        except Exception:
            raise exceptions.AuthenticationFailed('User not found for the given token.')
        
        return None


class APIKeyAuthentication(BaseAuthentication):
    """
    Custom authentication class for API Keys.
    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header, prepended with the string "Api-Key ".  For example:
    Authorization: Api-Key 401f7ac837da42b97f613d789819ff93537bee6a
    """
    keyword = 'Api-Key'

    def authenticate(self, request):
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None

        if len(auth) == 1:
            msg = 'Invalid token header. No credentials provided.'
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = 'Invalid token header. Token string should not contain spaces.'
            raise exceptions.AuthenticationFailed(msg)

        try:
            key = auth[1].decode()
        except UnicodeError:
            msg = 'Invalid token header. Token string should not contain invalid characters.'
            raise exceptions.AuthenticationFailed(msg)

        return self.authenticate_credentials(key)

    def authenticate_credentials(self, key):
        api_keys_collection = mongo_conn.get_collection('api_keys')
        api_key_doc = api_keys_collection.find_one({"key": key, "is_active": True})

        if not api_key_doc:
            raise exceptions.AuthenticationFailed('Invalid API Key.')

        user_doc = user_manager.get_user_by_id(api_key_doc['user_id'])
        if not user_doc:
            raise exceptions.AuthenticationFailed('User associated with this API Key not found.')

        return (MongoUser(user_doc), None) # (user, auth)


class APIKeyManager:
    """Manager class for handling API Key creation, retrieval, and revocation."""
    def __init__(self):
        self.collection = mongo_conn.get_collection('api_keys')
        
    def generate_key(self, user_id, name):
        # The actual secret key is still generated randomly
        key = f"sk_test_{secrets.token_urlsafe(32)}"
        
        key_data = {
            "key": key,
            "user_id": ObjectId(user_id),
            "name": name,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "key_display": f"{key[:11]}..."
        }
        self.collection.insert_one(key_data)
        
        # IMPORTANT: Return the full, un-hashed key ONLY upon creation
        return key

    def get_keys_for_user(self, user_id):
        # Exclude the sensitive 'key' field from the query result
        return list(self.collection.find({"user_id": ObjectId(user_id)}, {'key': 0})) 

    def revoke_key(self, key_id, user_id):
        result = self.collection.delete_one({"_id": ObjectId(key_id), "user_id": ObjectId(user_id)})
        return result.deleted_count > 0

api_key_manager = APIKeyManager()
