import stripe
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from core.utils.managers import user_manager

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class CreateCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        price_id = request.data.get('price_id')
        success_url = request.data.get('success_url')
        cancel_url = request.data.get('cancel_url')

        if not price_id or not success_url or not cancel_url:
            return Response({'error': 'price_id, success_url, and cancel_url are required.'}, status=400)

        user_doc = user_manager.get_user_by_id(request.user.id)
        if not user_doc or not user_doc.get('stripe_customer_id'):
            return Response({'error': 'Stripe customer not found for this user.'}, status=400)

        try:
            checkout_session = stripe.checkout.Session.create(
                customer=user_doc['stripe_customer_id'],
                payment_method_types=['card'],
                line_items=[{'price': price_id, 'quantity': 1}],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
            )
            return Response({'checkout_url': checkout_session.url})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CreateBillingPortalSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return_url = request.data.get('return_url')
        if not return_url:
            return Response({'error': 'return_url is required.'}, status=400)

        user_doc = user_manager.get_user_by_id(request.user.id)
        if not user_doc or not user_doc.get('stripe_customer_id'):
            return Response({'error': 'Stripe customer not found for this user.'}, status=400)

        try:
            portal_session = stripe.billing_portal.Session.create(
                customer=user_doc['stripe_customer_id'],
                return_url=return_url,
            )
            return Response({'portal_url': portal_session.url})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)