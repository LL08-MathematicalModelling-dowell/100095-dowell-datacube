import time
import logging
from .tasks import log_request_metrics_task  

logger = logging.getLogger(__name__)


class DatacubeObservabilityMiddleware:
    """
    High-performance middleware for Datacube. 
    Captures latency, IO, and slow queries without blocking the response.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. High-precision start timer
        start_time = time.perf_counter()

        # 2. Process request
        response = self.get_response(request)

        # 3. Calculate latency (ms)
        duration = (time.perf_counter() - start_time) * 1000

        # 4. Offload to Celery for authenticated users
        if hasattr(request, 'user') and request.user.is_authenticated:
            
            # Identify the target resource for the Analysis App
            # We check both Query Params (GET) and Body (POST/PUT/DELETE)
            db_id = request.GET.get('database_id') or request.POST.get('database_id')
            coll_name = request.GET.get('collection_name') or request.POST.get('collection_name', 'system')

            payload = {
                "user_id": str(request.user.id),
                "db_id": db_id,
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_ms": duration,
                "query_params": dict(request.GET.items()),
                "collection": coll_name
            }

            # DEBUG: Log safely instead of json.dumps(response)
            logger.debug(f"Datacube Telemetry dispatched for {request.path} - Latency: {duration:.2f}ms")

            print(f"<<<<<<<<<  payload --> {request.data}>>>>")

            # Fire and Forget: Send to background worker (analytics queue)
            try:
                log_request_metrics_task.delay(payload)
            except Exception as e:
                # Never let analytics failure crash the main API response
                logger.error(f"Failed to dispatch telemetry task: {e}")

        return response
