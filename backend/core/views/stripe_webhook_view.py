import os     # Import os
import stripe # Import stripe

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from core.utils.managers import user_manager


class StripeWebhookView(APIView):
    """
    Listens for events from Stripe to update user subscription status.
    """
    permission_classes = [AllowAny] # Must be public for Stripe to access

    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except ValueError as e:
            # Invalid payload
            return Response(status=400)
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            return Response(status=400)

        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            customer_id = session.get('customer')
            subscription_id = session.get('subscription')
            
            # Retrieve the full subscription object to get plan details
            subscription = stripe.Subscription.retrieve(subscription_id)

            price_id = subscription['items']['data'][0]['price']['id']

            pro_plan_id = os.getenv("PRO_PRICE_ID")
            free_plan_id = os.getenv("FREE_PRICE_ID")

            plan_map = {
                str(pro_plan_id): 'pro',
                str(free_plan_id): 'free',
            }
            plan_name = plan_map.get(price_id, 'pro')
            
            # Update the user's document in your database
            user_manager.users_collection.update_one(
                {'stripe_customer_id': customer_id},
                {'$set': {
                    'subscription_plan': plan_name,
                    'subscription_status': 'active'
                }}
            )

        elif event['type'] == 'customer.subscription.deleted':
            # Handle a canceled subscription
            subscription = event['data']['object']
            customer_id = subscription.get('customer')
            
            # Downgrade the user to the free plan
            user_manager.users_collection.update_one(
                {'stripe_customer_id': customer_id},
                {'$set': {
                    'subscription_plan': 'free',
                    'subscription_status': 'canceled'
                }}
            )
        
        return Response(status=200)
