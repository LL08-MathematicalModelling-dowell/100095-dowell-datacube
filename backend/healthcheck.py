from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timezone

@method_decorator(csrf_exempt, name='dispatch')
class HealthCheck(APIView):
    def get(self, request):
        now = datetime.now(timezone.utc).isoformat()
        return Response({
            "success": True,
            "version": "1.3.2",
            "status": "UP",
            "timestamp": now,
            "server_time": now,
            "message": "Server is running fine"
        }, status=status.HTTP_200_OK)