from rest_framework import serializers
from .utils.managers import user_manager


class UserRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    firstName = serializers.CharField(max_length=100)
    lastName = serializers.CharField(max_length=100)
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        """Check if the email is already in use."""
        if user_manager.get_user_by_email(value):
            raise serializers.ValidationError("This email is already registered.")
        return value

    def create(self, validated_data):
        """Create and return a new user instance, given the validated data."""
        return user_manager.create_user(
            email=validated_data['email'],
            first_name=validated_data['firstName'],
            last_name=validated_data['lastName'],
            password=validated_data['password']
        )


class UserSerializer(serializers.Serializer):
    """Serializer for user data (without password)."""
    id = serializers.CharField(source='_id', read_only=True)
    email = serializers.EmailField()
    firstName = serializers.CharField()
    lastName = serializers.CharField()


class APIKeySerializer(serializers.Serializer):
    """Serializer for displaying API Key info."""
    id = serializers.CharField(source='_id', read_only=True)
    key = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=100)
    created_at = serializers.DateTimeField(read_only=True)



class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=8, write_only=True)