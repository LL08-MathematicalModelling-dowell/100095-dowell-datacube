import asyncio
import logging
import requests

from rest_framework import status

from django.conf import settings
from rest_framework.response import Response

# Use the custom logger
logger = logging.getLogger('database_operations')

PAYMENT_API_URL = 'https://100105.pythonanywhere.com/api/v3/process-services/?type=api_service&api_key='


def check_api_key(api_key):
    try:
        if api_key == settings.API_KEY:
            return "success"
        else:
            res = requests.post(f"{PAYMENT_API_URL}{api_key}", data={"service_id": "DOWELL10043"})
            res = res.json()
            if res['success'] == True:
                return "success"
            return res['message']
    except Exception:
        return "Something went wrong"


def api_key_required(func):
    """Decorator to validate API key"""
    def wrapper(view_instance, request, *args, **kwargs):
        api_key = request.data.get("api_key")
        if not api_key or api_key != settings.EXPECTED_API_KEY:
            return Response(
                {"success": False, "message": "Invalid or missing API key"},
                status=status.HTTP_403_FORBIDDEN
            )
        return func(view_instance, request, *args, **kwargs)
    return wrapper


async def get_metadata_record(database_id):
    """Fetch metadata record for the specified database ID."""
    try:
        return await asyncio.to_thread(settings.METADATA_COLLECTION.find_one, {"_id": database_id})
    except Exception as e:
        logger.error(f"Error fetching metadata record for database ID '{database_id}': {e}")
        return None