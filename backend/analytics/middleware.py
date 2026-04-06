import os
import time
import json
import logging
from datetime import datetime, timezone

from django.http import RawPostDataException

from .tasks import (
    get_slow_threshold, log_http_request_task, 
    log_db_operation_task, log_performance_task,
    log_client_info_task, log_error_task, 
    log_mongo_detail_task, log_slow_query_task
)

logger = logging.getLogger(__name__)


class DatacubeObservabilityMiddleware:
    """
    High-performance middleware for Datacube MongoDB API.
    Captures latency, request/response metrics, and database operations.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.is_production = os.getenv('DJANGO_ENV') == 'production'
        
        # Define sensitive fields that should be redacted in production
        self.sensitive_fields = {
            'password', 'token', 'secret', 'key', 'authorization',
            'credit_card', 'ssn', 'social_security', 'api_key'
        }

    def _categorize_endpoint(self, path, method):
        """Categorize API endpoints for analytics grouping."""
        endpoint_map = {
            ('/api/create_database', 'POST'): 'database_creation',
            ('/api/add_collection', 'POST'): 'collection_creation',
            ('/api/list_databases', 'GET'): 'database_listing',
            ('/api/list_collections', 'GET'): 'collection_listing',
            ('/api/get_metadata', 'GET'): 'metadata_retrieval',
            ('/api/drop_database', 'DELETE'): 'database_deletion',
            ('/api/drop_collections', 'DELETE'): 'collection_deletion',
            ('/api/import_data', 'POST'): 'data_import',
            ('/api/crud', 'POST'): 'document_creation',
            ('/api/crud', 'PUT'): 'document_update',
            ('/api/crud', 'DELETE'): 'document_deletion',
            ('/api/crud', 'GET'): 'document_query',
            ('/health_check', 'GET'): 'health_check',
        }
        
        for endpoint_pattern, category in endpoint_map.items():
            if endpoint_pattern[0] in path and endpoint_pattern[1] == method:
                return category
        
        return 'other'

    def _redact_sensitive_data(self, data):
        """Redact sensitive data from logs in production."""
        if not self.is_production or not isinstance(data, dict):
            return data
        
        redacted_data = data.copy()
        
        def redact_dict(d):
            for key, value in list(d.items()):
                key_lower = str(key).lower()
                # Check if any sensitive field appears in the key name
                if any(sensitive in key_lower for sensitive in self.sensitive_fields):
                    d[key] = '[REDACTED]'
                elif isinstance(value, dict):
                    redact_dict(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            redact_dict(item)
            return d
        
        return redact_dict(redacted_data)

    def _extract_mongo_metrics(self, request_body, response_data):
        """Extract MongoDB-specific metrics from request and response."""
        metrics = {
            'document_count': 0,
            'operation_type': 'unknown',
            'query_complexity': 'simple'
        }
        
        try:
            # Extract from request body
            if isinstance(request_body, dict):
                # Document operations
                if 'documents' in request_body and isinstance(request_body['documents'], list):
                    metrics['document_count'] = len(request_body['documents'])
                    metrics['operation_type'] = 'bulk_insert' if metrics['document_count'] > 1 else 'single_insert'
                
                # Import data operations
                elif 'data' in request_body and isinstance(request_body['data'], list):
                    metrics['document_count'] = len(request_body['data'])
                    metrics['operation_type'] = 'data_import'
                
                # Query operations (if you have query endpoints)
                elif 'query' in request_body:
                    metrics['operation_type'] = 'query'
                    # Estimate query complexity
                    query = request_body['query']
                    if isinstance(query, dict):
                        depth = self._calculate_dict_depth(query)
                        metrics['query_complexity'] = 'complex' if depth > 2 else 'simple'
            
            # Extract from response data
            if isinstance(response_data, dict):
                # Count returned documents
                if 'documents' in response_data and isinstance(response_data['documents'], list):
                    metrics['returned_documents'] = len(response_data['documents'])
                elif 'data' in response_data and isinstance(response_data['data'], list):
                    metrics['returned_documents'] = len(response_data['data'])
                
                # MongoDB operation results
                if 'inserted_ids' in response_data:
                    metrics['inserted_count'] = len(response_data['inserted_ids'])
                if 'modified_count' in response_data:
                    metrics['modified_count'] = response_data['modified_count']
                if 'deleted_count' in response_data:
                    metrics['deleted_count'] = response_data['deleted_count']
                    
        except Exception as e:
            logger.debug(f"Error extracting MongoDB metrics: {e}")
        
        return metrics

    def _calculate_dict_depth(self, d, current_depth=0):
        """Calculate depth of nested dictionary for query complexity estimation."""
        if not isinstance(d, dict):
            return current_depth
        
        max_depth = current_depth + 1
        for value in d.values():
            if isinstance(value, dict):
                depth = self._calculate_dict_depth(value, current_depth + 1)
                max_depth = max(max_depth, depth)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        depth = self._calculate_dict_depth(item, current_depth + 1)
                        max_depth = max(max_depth, depth)
        
        return max_depth

    def __call__(self, request):
        # 1. High-precision start timer
        start_time = time.perf_counter()

        # 2. Capture raw body BEFORE it gets consumed
        raw_body = None
        parsed_json = {}
        if request.content_type == 'application/json' and request.body:
            try:
                raw_body = request.body.decode('utf-8')
                request._body = raw_body.encode('utf-8')
                parsed_json = json.loads(raw_body)
                request._parsed_json = parsed_json
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                logger.debug(f"Could not decode JSON body: {e}")
                raw_body = None # If decoding fails, we won't have the raw body for logging, but we can still proceed with an empty dict for parsed_json.

        # 3. Process request
        response = self.get_response(request)

        # 4. Capture response data if available
        response_data = {}
        try:
            if hasattr(response, 'data'):
                response_data = response.data
            elif hasattr(response, 'content'):
                content_type = response.get('Content-Type', '')
                if 'application/json' in content_type:
                    response_data = json.loads(response.content.decode('utf-8'))
        except Exception as e:
            logger.debug(f"Could not parse response data: {e}")

        # 5. Calculate latency (ms)
        duration = (time.perf_counter() - start_time) * 1000

        # if hasattr(request, 'user') and request.user.is_authenticated:
        if hasattr(request, 'user') and request.user and request.user.is_authenticated:
            request_body = {}
            if hasattr(request, '_parsed_json'):
                request_body = request._parsed_json
            elif hasattr(request, 'data'):
                request_body = request.data
            elif request.method in ['POST', 'PUT', 'PATCH']:
                request_body = dict(request.POST.items())

            db_id = (
                request_body.get('database_id') or
                request.GET.get('database_id') or
                request.POST.get('database_id')
            )
            coll_name = (
                request_body.get('collection_name') or
                request.GET.get('collection_name') or
                request.POST.get('collection_name', 'system')
            )

            # --- Request/Response sizes ---
            try:
                request_size = len(request.body) if request.body else 0
            except RawPostDataException:
                request_size = int(request.META.get('CONTENT_LENGTH', 0))
            response_size = len(response.content) if hasattr(response, 'content') else 0

            # --- MongoDB-specific metrics ---
            mongo_metrics = self._extract_mongo_metrics(request_body, response_data)

            # --- Redact sensitive data in production (optional) ---
            if self.is_production:
                request_body = self._redact_sensitive_data(request_body)
                response_data = self._redact_sensitive_data(response_data)

            user_id = str(request.user.id)
            method = request.method
            path = request.path
            status_code = response.status_code
            duration_ms = round(duration, 2)
            timestamp = int(time.time() * 1000)
            success = 200 <= status_code < 300

            # 1. HTTP Request
            http_data = {
                "user_id": user_id,
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "timestamp": datetime.fromtimestamp(timestamp/1000, tz=timezone.utc),
                "success": success,
            }
            log_http_request_task.delay(http_data) # type: ignore

            # 2. Database context (if applicable)
            if db_id or coll_name != 'system':
                db_data = {
                    "user_id": user_id,
                    "db_id": db_id,
                    "collection": coll_name,
                    "operation_type": mongo_metrics.get('operation_type', 'unknown'),
                    "document_count": mongo_metrics.get('document_count', 0),
                    "query_complexity": mongo_metrics.get('query_complexity', 'simple'),
                }
                log_db_operation_task.delay(db_data) # type: ignore

            # 3. Performance metrics
            throughput = round((response_size / (duration/1000)) if duration>0 else 0, 2)
            warning = None
            if duration > 1000: warning = 'slow_request'
            elif request_size > 1024*1024: warning = 'large_request'
            perf_data = {
                "user_id": user_id,
                "request_size_bytes": request_size,
                "response_size_bytes": response_size,
                "throughput_bytes_per_sec": throughput,
                "warning": warning,
            }
            log_performance_task.delay(perf_data) # type: ignore

            # 4. Client info
            client_data = {
                "user_id": user_id,
                "client_ip": request.META.get('REMOTE_ADDR', ''),
                "user_agent": request.META.get('HTTP_USER_AGENT', '')[:200],
                "content_type": request.content_type,
            }
            log_client_info_task.delay(client_data) # type: ignore

            # 5. Error (if 4xx/5xx)
            if status_code >= 400:
                error_data = {
                    "user_id": user_id,
                    "status_code": status_code,
                    "error_type": 'server_error' if status_code >= 500 else 'client_error',
                    "error_message": None,  # could extract from response
                }
                log_error_task.delay(error_data) # type: ignore

            # 6. MongoDB details (if any counts)
            if any(k in mongo_metrics for k in ['inserted_count','modified_count','deleted_count','returned_documents']):
                detail_data = {
                    "user_id": user_id,
                    "inserted_count": mongo_metrics.get('inserted_count'),
                    "modified_count": mongo_metrics.get('modified_count'),
                    "deleted_count": mongo_metrics.get('deleted_count'),
                    "returned_documents": mongo_metrics.get('returned_documents'),
                }
                log_mongo_detail_task.delay(detail_data) # type: ignore

            # 7. Slow query (if duration > threshold)
            threshold = get_slow_threshold(mongo_metrics.get('operation_type',''), path)
            if duration > threshold:
                slow_data = {
                    "user_id": user_id,
                    "query_details": {
                        "method": method,
                        "path": path,
                        "params": dict(request.GET.items()),
                    },
                    "duration_ms": duration_ms,
                    "threshold_ms": threshold,
                    "collection": coll_name,
                    "db_id": db_id,
                }
                log_slow_query_task.delay(slow_data) # type: ignore

        return response
