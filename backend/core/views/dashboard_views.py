from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from core.utils.authentication import api_key_manager # Import your API key manager
from api.services.metadata_service import MetadataService # To get user databases

class DashboardOverviewView(APIView):
    """
    Renders the main dashboard overview page for a logged-in user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user_id = request.user.id
        
        # Fetch data for the dashboard
        meta_svc = MetadataService()
        databases = meta_svc.list_databases_for_user(user_id)
        
        # You can enrich this data further if needed
        # For example, getting collection counts for each DB
        
        context = {
            'user': request.user, # The MongoUser proxy object
            'databases': databases
        }
        return render(request, 'dashboard/overview.html', context)

class DashboardAPIKeysView(APIView):
    """
    Handles listing, creating, and revoking API keys for a user.
    GET renders the page. POST/DELETE are API actions called by the frontend.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Renders the API Keys management page with a list of existing keys."""
        user_id = request.user.id
        keys = api_key_manager.get_keys_for_user(user_id)
        
        context = {
            'user': request.user,
            'api_keys': keys
        }
        return render(request, 'dashboard/api_keys.html', context)

    def post(self, request, *args, **kwargs):
        """Creates a new API key. Returns JSON."""
        key_name = request.data.get('name')
        if not key_name:
            return Response({"error": "A 'name' for the key is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        new_key = api_key_manager.generate_key(request.user.id, key_name)
        
        return Response({
            "message": "API Key created successfully. Store it securely!",
            "key": new_key,
            "name": key_name
        }, status=status.HTTP_201_CREATED)

    def delete(self, request, key_id, *args, **kwargs):
        """Revokes (deletes) an API key. Returns JSON."""
        was_deleted = api_key_manager.revoke_key(key_id, request.user.id)
        if was_deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"error": "Key not found or permission denied."}, status=status.HTTP_404_NOT_FOUND)

class DashboardBillingView(APIView):
    """Renders the billing management page."""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        context = {
            'user': request.user
            # You can add more context like subscription details here
        }
        return render(request, 'dashboard/billing.html', context)