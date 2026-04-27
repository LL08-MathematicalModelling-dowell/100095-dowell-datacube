from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from core.utils.authentication import MongoUser
from core.utils.managers import user_manager


class DemoLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Get or create the demo user
        demo_email = "samanta@dowellresearch.se"
        user_doc = user_manager.get_user_by_email(demo_email)
        if not user_doc:
            return Response({"error": "Demo user not found"}, status=404)
            # Create a demo user with read‑only permissions (set a flag)
            # user_doc = user_manager.create_demo_user(
            #     email=demo_email,
            #     first_name="Demo",
            #     last_name="User"
            # )
        # Generate JWT
        proxy_user = MongoUser(user_doc)
        refresh = RefreshToken.for_user(proxy_user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })