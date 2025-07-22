from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserRegistrationSerializer, UserSerializer, APIKeySerializer
from .utils.managers import user_manager
from .utils.authentication import api_key_manager, MongoUser


class RegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)
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
