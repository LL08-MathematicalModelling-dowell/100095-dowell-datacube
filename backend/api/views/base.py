import time
import inspect
from functools import wraps
from typing import Any, Callable, Type, Dict, List, Tuple

from django.conf import settings
from django.http import Http404
from adrf.views import APIView as AsyncAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.serializers import Serializer
from rest_framework.exceptions import APIException

from analytics.tasks import log_request_metrics_task
from api.services.metadata_service import MetadataService
from api.services.gridfs_service import GridFSService

class BaseAPIView(AsyncAPIView):
    @property
    def file_svc(self):
        return GridFSService(
            db_name=settings.FILE_STORAGE_DB_NAME,
            user_id=str(self.request.user.pk)
        )

    @property
    def metadata_svc(self):
        return MetadataService(user_id=str(self.request.user.pk))

    @staticmethod
    def handle_errors(fn: Callable) -> Callable:
        if inspect.iscoroutinefunction(fn):
            @wraps(fn)
            async def async_wrapper(self, request, *args, **kwargs):
                start_time = time.perf_counter()
                try:
                    response = await fn(self, request, *args, **kwargs)
                    BaseAPIView._track(request, response, start_time)
                    return response
                except (Http404, APIException) as e:
                    # Capture DRF's 401, 403, 404, etc.
                    BaseAPIView._track(request, None, start_time, error=e)
                    status_code = getattr(e, 'status_code', status.HTTP_404_NOT_FOUND if isinstance(e, Http404) else 500)
                    detail = getattr(e, 'detail', str(e))
                    return Response({"success": False, "error": type(e).__name__, "detail": detail}, status=status_code)
                except (ValueError, KeyError, TypeError) as e:
                    BaseAPIView._track(request, None, start_time, error=e)
                    return Response({"success": False, "error": "ValidationError", "detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    BaseAPIView._track(request, None, start_time, error=e)
                    return Response({"success": False, "error": "InternalServerError", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return async_wrapper

        @wraps(fn)
        def sync_wrapper(self, request, *args, **kwargs):
            start_time = time.perf_counter()
            try:
                response = fn(self, request, *args, **kwargs)
                BaseAPIView._track(request, response, start_time)
                return response
            except (Http404, APIException) as e:
                BaseAPIView._track(request, None, start_time, error=e)
                status_code = getattr(e, 'status_code', status.HTTP_404_NOT_FOUND if isinstance(e, Http404) else 500)
                return Response({"success": False, "error": type(e).__name__, "detail": getattr(e, 'detail', str(e))}, status=status_code)
            except (ValueError, KeyError, TypeError) as e:
                BaseAPIView._track(request, None, start_time, error=e)
                return Response({"success": False, "error": "ValidationError", "detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                BaseAPIView._track(request, None, start_time, error=e)
                return Response({"success": False, "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return sync_wrapper

    def validate_serializer(self, serializer_class: Type[Serializer], data: Dict[str, Any]) -> Dict[str, Any]:
        serializer = serializer_class(data=data, context={'request': self.request})
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data # type: ignore

    @staticmethod
    def _track(request, response, start_time, error=None):
        if not request.user or not request.user.is_authenticated: return
        duration = (time.perf_counter() - start_time) * 1000
        telemetry_data = {
            "user_id": str(request.user.pk),
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code if response else 500,
            "duration_ms": duration,
            "is_error": error is not None
        }
        log_request_metrics_task.delay(telemetry_data) # type: ignore
