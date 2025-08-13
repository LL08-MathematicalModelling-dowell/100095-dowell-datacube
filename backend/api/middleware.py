from django.http import JsonResponse
from datetime import datetime, timezone
from core.utils.managers import user_manager
import calendar


class UsageMeteringMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Define plan limits here
        self.plan_limits = {
            'free': {'api_calls': 1000},
            'pro': {'api_calls': 50000},
        }

    def __call__(self, request):
        # Only meter requests to the core data plane
        if not request.path.startswith('/api/v1/data/crud'):
             return self.get_response(request)

        # request.user is set by the authentication middleware
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return self.get_response(request)
        
        user_id = request.user.id
        
        # Fetch the full user document to get subscription and usage info
        user_doc = user_manager.get_user_by_id(user_id)
        if not user_doc:
            return JsonResponse({'error': 'User not found'}, status=404)

        # Check if the month has rolled over
        now = datetime.now(timezone.utc)
        last_reset = datetime.fromisoformat(user_doc['usage']['last_reset_date'])
        
        if now.month != last_reset.month or now.year != last_reset.year:
            # Month has changed, reset the counter
            user_manager.users_collection.update_one(
                {'_id': user_doc['_id']},
                {'$set': {
                    'usage.api_calls_current_month': 0,
                    'usage.last_reset_date': now.isoformat()
                }}
            )
            # Refresh the document to get the reset values
            user_doc = user_manager.get_user_by_id(user_id)

        # Enforce limits
        plan = user_doc.get('subscription_plan', 'free')
        limit = self.plan_limits.get(plan, self.plan_limits['free'])['api_calls']
        current_usage = user_doc['usage']['api_calls_current_month']

        if current_usage >= limit:
            return JsonResponse(
                {'error': f'API call limit of {limit} for the {plan} plan exceeded.'},
                status=429 # Too Many Requests
            )

        # Increment usage count using an atomic operation
        user_manager.users_collection.update_one(
            {'_id': user_doc['_id']},
            {'$inc': {'usage.api_calls_current_month': 1}}
        )

        return self.get_response(request)