import asyncio
from datetime import datetime, timezone
from functools import wraps
import time
from typing import Any, Callable, Type, Dict

# from rest_framework.views import APIView
from django.conf import settings
from adrf.views import APIView as AsyncAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.serializers import Serializer

from analytics.tasks import log_request_metrics_task


class BaseAPIView(AsyncAPIView):
    """
    Enhanced Base API View for MongoDB-backed DRF services.
    Provides automated error handling and standardized serializer validation.
    """

    @staticmethod
    def handle_errors(fn: Callable) -> Callable:
        """
        A universal decorator for sync and async views that catches common 
        errors and returns standard DRF responses.
        """
        if asyncio.iscoroutinefunction(fn):
            @wraps(fn)
            async def async_wrapper(self, request, *args, **kwargs):
                start_time = time.perf_counter()
                try:
                    response = await fn(self, request, *args, **kwargs)
                    # Success Logic: Log the operation
                    BaseAPIView._track(request, response, start_time)
                    return response
                except (ValueError, TypeError) as e:
                    BaseAPIView._track(request, None, start_time, error=e)

                    return Response(
                        {"success": False, "error": "Validation Error", "detail": str(e)}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                except Exception as e:
                    BaseAPIView._track(request, None, start_time, error=e)

                    return Response(
                        {"success": False, "error": "Internal Server Error", "detail": str(e)}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            return async_wrapper

        @wraps(fn)
        def sync_wrapper(self, request, *args, **kwargs):
            start_time = time.perf_counter()
            try:
                response = fn(self, request, *args, **kwargs)
                # Success Logic: Log the operation
                BaseAPIView._track(request, response, start_time)
                return response
            except (ValueError, TypeError) as e:
                BaseAPIView._track(request, None, start_time, error=e)
                return Response(
                    {"success": False, "error": "Validation Error", "detail": str(e)}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                BaseAPIView._track(request, None, start_time, error=e)

                return Response(
                    {"success": False, "error": "Internal Server Error", "detail": str(e)}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return sync_wrapper


    def validate_serializer(self, serializer_class: Type[Serializer],
                             data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standardizes the validation of incoming data against a DRF serializer.
        """
        serializer = serializer_class(data=data, context={'request': self.request})
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data # type: ignore

    @staticmethod
    def _track(request, response, start_time, error=None):
        """Extracts metadata and offloads to Celery."""
        if not request.user or not request.user.is_authenticated:
            return

        duration = (time.perf_counter() - start_time) * 1000
        
        # Package data for the background task
        telemetry_data = {
            "user_id": str(request.user.pk),
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code if response else 500,
            "duration_ms": duration,
            "collection": request.query_params.get('collection_name') or request.data.get('collection_name', 'system'),
            "is_error": error is not None
        }
        # Send to the 'analytics' queue
        log_request_metrics_task.delay(telemetry_data)

    

    