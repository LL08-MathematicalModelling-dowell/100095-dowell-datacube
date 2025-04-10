import logging
from django.http import JsonResponse
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
import requests

logger = logging.getLogger(__name__)

AUTHENTICATION_SERVICE_URL = settings.AUTHENTICATION_SERVICE_URL  # Ensure this is set in settings

class APIKeyAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware to authenticate users via API key.
    The API key is retrieved from the request header and validated
    by making a request to the authentication app.
    """

    def process_request(self, request):
        api_key = request.headers.get("X-API-KEY")  # Retrieve API key from header
        
        if not api_key:
            return JsonResponse({"success": False, "message": "API key is required."}, status=401)
        
        try:
            # Validate the API key by making a request to the authentication service
            response = requests.post(
                f"{AUTHENTICATION_SERVICE_URL}/validate-api-key/",
                json={"api_key": api_key},
                timeout=5  # Set a timeout to avoid long waits
            )
            
            if response.status_code == 200:
                user_data = response.json().get("user")  # Extract user data
                request.user = user_data  # Attach user data to request
                return None
            else:
                return JsonResponse({"success": False, "message": "Invalid API key."}, status=403)
        
        except requests.exceptions.RequestException as e:
            logger.error(f"API key validation error: {e}")
            return JsonResponse({"success": False, "message": "Authentication service unavailable."}, status=503)
