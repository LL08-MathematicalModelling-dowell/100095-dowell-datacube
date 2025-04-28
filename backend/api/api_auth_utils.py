"""
This module provides utility functions and decorators for API authentication and user ID management.
Functions:
    get_user_id_from_api_key(api_key):
    append_user_id(name, user_id):
        Append user ID to a name with proper separator.
    remove_user_id(name):
        Remove user ID from a name.
    process_database_metadata(metadata, remove_uid=False):
        Process database metadata to add or remove user IDs from database names.
    api_key_required(view_func):
        Decorator to require and validate API key for views.
"""

from functools import wraps
from rest_framework import status
from rest_framework.response import Response
from django.conf import settings

def get_user_id_from_api_key(api_key):
    """
    Validate API key and return associated user ID.
    In a production environment, this should validate against a secure key store.
    
    Args:
        api_key (str): The API key to validate
        
    Returns:
        str: The user ID associated with the API key
        
    Raises:
        ValueError: If the API key is invalid or expired
    """
    # This is a placeholder implementation
    # In production, you would validate against your key store (database, Redis, etc.)
    if not api_key:
        raise ValueError("API key is required")
    
    # You should replace this with actual API key validation logic
    # This could query a database table that stores API keys and their associated user IDs
    if not api_key.startswith('sk_'):
        raise ValueError("Invalid API key format")
    
    # For demonstration, we're using a simple mapping
    # In production, this would be replaced with a database query
    api_key_store = getattr(settings, 'API_KEY_STORE', {})
    user_id = api_key_store.get(api_key)
    
    if not user_id:
        raise ValueError("Invalid or expired API key")
        
    return user_id

def append_user_id(name, user_id):
    """Append user ID to a name with proper separator."""
    return f"{name}__uid_{user_id}"

def remove_user_id(name):
    """Remove user ID from a name."""
    if '__uid_' in name:
        return name.split('__uid_')[0]
    return name

def process_database_metadata(metadata, remove_uid=False):
    """Process database metadata to add or remove user IDs from database names."""
    if not metadata:
        return metadata
        
    processed = metadata.copy()
    if remove_uid:
        processed['database_name'] = remove_user_id(processed['database_name'])
    
    return processed

def api_key_required(view_func):
    """Decorator to require and validate API key for views."""
    @wraps(view_func)
    def wrapped_view(view_instance, request, *args, **kwargs):
        try:
            # Get API key from header
            api_key = request.headers.get('X-API-Key')
            if not api_key:
                return Response(
                    {"success": False, "message": "API key is required"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Get user ID from API key
            user_id = get_user_id_from_api_key(api_key)
            
            # Add user_id to request object for use in the view
            request.user_id = user_id
            
            # Call the original view function
            return view_func(view_instance, request, *args, **kwargs)
            
        except ValueError as e:
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return Response(
                {"success": False, "message": "Authentication error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    return wrapped_view