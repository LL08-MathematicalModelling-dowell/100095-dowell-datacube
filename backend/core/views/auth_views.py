import os     # Import os
import stripe # Import stripe

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from core.serializers import (
  UserRegistrationSerializer,
  UserSerializer,
  APIKeySerializer,
  PasswordResetRequestSerializer,
  PasswordResetConfirmSerializer,
)
from core.utils.managers import user_manager
from core.utils.authentication import api_key_manager, MongoUser

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


# Configures Stripe with secret key
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


class RegistrationView(APIView):
    permission_classes = [AllowAny]

    def _send_verification_email(self, user_data, token):
        """Helper method to construct and send the verification email."""
        # IMPORTANT: Replace with your actual frontend URL
        verification_url = f"http://localhost:8000/api/auth/verify-email/{token}" 
        
        context = {
            "first_name": user_data['firstName'],
            "verification_url": verification_url,
        }
        
        html_message = render_to_string('core/email/verify_email.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject="Verify Your Email Address",
            message=plain_message,
            from_email=None,  # Uses DEFAULT_FROM_EMAIL from settings
            recipient_list=[user_data['email']],
            html_message=html_message,
            fail_silently=False, # Set to True in production if needed
        )

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user_doc = serializer.save() 
            user_id = user_doc['_id']

            # --- ADDED: Create Stripe Customer ---
            try:
                customer = stripe.Customer.create(
                    email=user_doc['email'],
                    name=f"{user_doc['firstName']} {user_doc['lastName']}",
                    metadata={'datacube_user_id': str(user_id)}
                )
                # Save the Stripe Customer ID to our user document
                user_manager.users_collection.update_one(
                    {'_id': user_id},
                    {'$set': {'stripe_customer_id': customer.id}}
                )
            except Exception as e:
                # Handle Stripe error, maybe log it and proceed
                print(f"Error creating Stripe customer: {e}")
                # Decide if registration should fail here. For now, we'll let it pass.

            # Generate token and send email
            # token = user_manager.generate_email_verification_token(user_id)
            # self._send_verification_email(user_doc, token)

            # {"message": "Registration successful. Please check your email to verify your account."}, 
            return Response(
                {"message": "Registration successful"}, 
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        user_doc = user_manager.get_user_by_email(email)

        if not user_doc or not user_manager.check_password(password, user_doc['password']):
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Create a proxy user object for token generation
        proxy_user = MongoUser(user_doc)
        
        # Manually generate JWT tokens
        refresh = RefreshToken.for_user(proxy_user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })


class PasswordResetRequestView(APIView):
    """
    Initiates the password reset process by sending an email to the user.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        user_doc = user_manager.get_user_by_email(email)

        # For security, we always return a success message, even if the user doesn't exist.
        # This prevents attackers from discovering which emails are registered.
        if user_doc:
            token = user_manager.generate_password_reset_token(user_doc['_id'])
            
            # IMPORTANT: Update this URL to point to your frontend page
            reset_url = f"http://localhost:8000/core/reset-password/{token}"
            
            context = {"reset_url": reset_url, "first_name": user_doc.get('firstName', 'User')}
            html_message = render_to_string('core/email/reset_password.html', context)
            
            send_mail(
                subject="Your Password Reset Request",
                message=strip_tags(html_message),
                from_email=None,
                recipient_list=[email],
                html_message=html_message,
            )

        return Response({"message": "If an account with that email exists, a password reset link has been sent."}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """
    Completes the password reset process by setting a new password.
    """
    permission_classes = [AllowAny]

    def post(self, request, token):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_doc = user_manager.verify_password_reset_token(token)
        if not user_doc:
            return Response({"error": "This password reset link is invalid or has expired."}, status=status.HTTP_400_BAD_REQUEST)

        # Update the user's password
        new_password = serializer.validated_data['password']
        hashed_password = user_manager.hash_pass(new_password)
        
        user_manager.users_collection.update_one(
            {'_id': user_doc['_id']},
            {'$set': {'password': hashed_password}}
        )

        # Clean up the token so it can't be used again
        user_manager.clear_password_reset_token(user_doc['_id'])

        return Response({"message": "Your password has been reset successfully. You can now log in."}, status=status.HTTP_200_OK)


class ResendVerificationEmailView(APIView):
    """
    Allows an authenticated but unverified user to request a new verification email.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # request.user is our MongoUser proxy object
        user_id_str = request.user.id
        
        # We need the full user document from the DB to get email and check status
        user_doc = user_manager.get_user_by_id(user_id_str)
        if not user_doc:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if user_doc.get("is_email_verified", False):
            return Response({"message": "Your email is already verified."}, status=status.HTTP_400_BAD_REQUEST)

        token = user_manager.generate_email_verification_token(user_doc['_id'])
        self._send_verification_email(user_doc, token)

        return Response({"message": "A new verification email has been sent."}, status=status.HTTP_200_OK)

    def _send_verification_email(self, user_doc, token):
        # IMPORTANT: Update this URL to point to your frontend page
        verification_url = f"http://localhost:8000/core/verify-email/{token}" 
        context = {
            "first_name": user_doc.get('firstName', 'User'),
            "verification_url": verification_url,
        }
        html_message = render_to_string('core/email/verify_email.html', context)
        send_mail(
            subject="Verify Your Email Address",
            message=strip_tags(html_message),
            from_email=None,
            recipient_list=[user_doc['email']],
            html_message=html_message,
        )


class EmailVerificationView(APIView):
    permission_classes = [AllowAny] # Anyone with a valid link can access this

    def get(self, request, token):
        user_doc = user_manager.verify_email_token(token)
        if user_doc:
            # You can redirect to a "success" page on your frontend
            return Response({"message": "Email verified successfully!"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid or expired verification link."}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class APIKeyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all API keys for the current user."""
        keys = api_key_manager.get_keys_for_user(request.user.id)
        serializer = APIKeySerializer(keys, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create a new API key for the current user."""
        key_name = request.data.get('name')
        if not key_name:
            return Response({"error": "A 'name' for the key is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        new_key = api_key_manager.generate_key(request.user.id, key_name)
        
        return Response({
            "message": "API Key created successfully. Store it securely!",
            "key": new_key,
            "name": key_name
        }, status=status.HTTP_201_CREATED)

    def delete(self, request, key_id):
        """Revoke (delete) an API key."""
        was_deleted = api_key_manager.revoke_key(key_id, request.user.id)
        if was_deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"error": "Key not found or you do not have permission to delete it."}, status=status.HTTP_404_NOT_FOUND)


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
