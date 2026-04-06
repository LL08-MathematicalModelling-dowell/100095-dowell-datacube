import time
import inspect
from functools import wraps
from typing import Any, Callable, Type, Dict
from datetime import datetime, timezone
from urllib import response

from django.conf import settings
from django.http import Http404

from adrf.views import APIView as AsyncAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.serializers import Serializer
from rest_framework.exceptions import APIException

from api.services.metadata_service import MetadataService
from api.services.gridfs_service import GridFSService

# Import analytics tasks
from analytics.tasks import (
    log_http_request_task,
    log_db_operation_task,
    log_performance_task,
    log_client_info_task,
    log_error_task,
    log_slow_query_task,
)

class BaseAPIView(AsyncAPIView):
    _forced_user_id = None  # Add this to store the owner_id from the signed URL

    @property
    def file_svc(self):
        # Use the forced ID if available (for signed URLs), else fall back to request.user
        uid = self._forced_user_id or (str(self.request.user.pk) if self.request.user and self.request.user.is_authenticated else None)
        
        if not uid:
            raise PermissionDenied("User context not found for File Service.")

        return GridFSService(
            db_name=settings.FILE_STORAGE_DB_NAME,
            user_id=uid
        )

    # @property
    # def file_svc(self):
    #     return GridFSService(
    #         db_name=settings.FILE_STORAGE_DB_NAME,
    #         user_id=str(self.request.user.pk)
    #     )

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
                    # Check if we need to manually perform content negotiation
                    if not hasattr(response, 'accepted_renderer'):
                        negatitator = self.get_content_negotiator()
                        renderers = self.get_renderers()
                        # Select the appropriate renderer based on the request
                        conneg = negatitator.select_renderer(request, renderers, self.format_kwarg)
                        
                        response.accepted_renderer = conneg[0]
                        response.accepted_media_type = conneg[1]
                        # FIX: Call without positional arguments
                        response.renderer_context = self.get_renderer_context() 
                    
                    if hasattr(response, 'render') and callable(response.render):
                        # Render to ensure response.content is available for _track
                        await response.render() if inspect.iscoroutinefunction(response.render) else response.render()
                        
                    BaseAPIView._track(request, response, start_time)
                    return response
                except (Http404, APIException) as e:
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
                # Check if we need to manually perform content negotiation
                if not hasattr(response, 'accepted_renderer'):
                    negatitator = self.get_content_negotiator()
                    renderers = self.get_renderers()
                    # Select the appropriate renderer based on the request
                    conneg = negatitator.select_renderer(request, renderers, self.format_kwarg)
                    
                    response.accepted_renderer = conneg[0]
                    response.accepted_media_type = conneg[1]
                    # FIX: Call without positional arguments
                    response.renderer_context = self.get_renderer_context() 
                
                if hasattr(response, 'render') and callable(response.render):
                    # Render to ensure response.content is available for _track
                    response.render()

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
        return serializer.validated_data

    @staticmethod
    def _track(request, response, start_time, error=None):
        """Send analytics data to Celery tasks asynchronously."""
        if not request.user or not request.user.is_authenticated:
            return

        duration_ms = (time.perf_counter() - start_time) * 1000
        user_id = str(request.user.pk)
        method = request.method
        path = request.path
        status_code = response.status_code if response else (getattr(error, 'status_code', 500) if error else 500)
        success = error is None and 200 <= status_code < 300

        # 1. HTTP Request log
        http_data = {
            "user_id": user_id,
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
            "timestamp": datetime.now(timezone.utc),
            "success": success,
        }
        log_http_request_task.delay(http_data) # type: ignore

        # 2. Client info
        client_data = {
            "user_id": user_id,
            "client_ip": request.META.get('REMOTE_ADDR', ''),
            "user_agent": request.META.get('HTTP_USER_AGENT', '')[:200],
            "content_type": request.content_type,
        }
        log_client_info_task.delay(client_data) # type: ignore

        # 3. Performance metrics (request/response sizes)
        request_size = 0
        try:
            request_size = len(request.body) if hasattr(request, 'body') and request.body else 0
        except:
            request_size = int(request.META.get('CONTENT_LENGTH', 0))
        response_size = len(response.content) if response and hasattr(response, 'content') else 0
        throughput = round((response_size / (duration_ms / 1000)) if duration_ms > 0 else 0, 2)
        warning = None
        if duration_ms > 1000:
            warning = "slow_request"
        elif request_size > 1024 * 1024:
            warning = "large_request"

        perf_data = {
            "user_id": user_id,
            "request_size_bytes": request_size,
            "response_size_bytes": response_size,
            "throughput_bytes_per_sec": throughput,
            "warning": warning,
        }
        log_performance_task.delay(perf_data) # type: ignore

        # 4. Error log (if any)
        if error or status_code >= 400:
            error_type = 'server_error' if status_code >= 500 else 'client_error'
            error_message = str(error) if error else None
            error_data = {
                "user_id": user_id,
                "status_code": status_code,
                "error_type": error_type,
                "error_message": error_message,
            }
            log_error_task.delay(error_data) # type: ignore

        # 5. Database context (try to extract db_id and collection from request data)
        db_id = None
        collection = "unknown"
        operation_type = "unknown"
        document_count = 0
        query_complexity = "simple"

        # Attempt to extract from POST/JSON body or GET parameters
        if request.method in ['POST', 'PUT', 'PATCH']:
            body_data = {}
            if hasattr(request, 'data'):
                body_data = request.data
            elif hasattr(request, '_parsed_json'):
                body_data = request._parsed_json
            else:
                try:
                    body_data = request.POST.dict()
                except:
                    pass
            db_id = body_data.get('database_id') or request.GET.get('database_id')
            collection = body_data.get('collection_name') or request.GET.get('collection_name', 'unknown')
            # Infer operation type from method and endpoint
            if 'crud' in path:
                if method == 'POST':
                    operation_type = 'document_creation'
                elif method == 'PUT':
                    operation_type = 'document_update'
                elif method == 'DELETE':
                    operation_type = 'document_deletion'
                elif method == 'GET':
                    operation_type = 'document_query'
            elif 'import' in path:
                operation_type = 'data_import'
                if 'data' in body_data and isinstance(body_data['data'], list):
                    document_count = len(body_data['data'])
            elif 'create_database' in path:
                operation_type = 'database_creation'
            elif 'drop_database' in path:
                operation_type = 'database_deletion'
            elif 'add_collection' in path:
                operation_type = 'collection_creation'
            elif 'drop_collections' in path:
                operation_type = 'collection_deletion'
            elif 'list_databases' in path or 'list_collections' in path:
                operation_type = 'listing'

            # Count documents if present
            if 'documents' in body_data and isinstance(body_data['documents'], list):
                document_count = len(body_data['documents'])
            elif 'document' in body_data:
                document_count = 1

        if db_id or collection != 'unknown':
            db_data = {
                "user_id": user_id,
                "db_id": db_id,
                "collection": collection,
                "operation_type": operation_type,
                "document_count": document_count,
                "query_complexity": query_complexity,
            }
            log_db_operation_task.delay(db_data) # type: ignore

        # 6. Slow query detection (if duration exceeds threshold)
        # Simple threshold: 1000ms for most, but you can use a more sophisticated mapping
        threshold = 1000
        if 'import' in path:
            threshold = 5000
        elif 'crud' in path and method == 'POST':
            threshold = 1000
        elif 'query' in path or method == 'GET':
            threshold = 500

        if duration_ms > threshold:
            slow_data = {
                "user_id": user_id,
                "query_details": {
                    "method": method,
                    "path": path,
                    "params": dict(request.GET.items()),
                    "request_body_size": request_size,
                },
                "duration_ms": round(duration_ms, 2),
                "threshold_ms": threshold,
                "collection": collection,
                "db_id": db_id,
            }
            log_slow_query_task.delay(slow_data) # type: ignore
