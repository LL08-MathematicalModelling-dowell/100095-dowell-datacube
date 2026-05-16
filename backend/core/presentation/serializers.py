from rest_framework import serializers

from core.infrastructure.managers import user_manager
from core.infrastructure.roles import ROLES, normalize_role
from core.infrastructure.user_access import effective_email_verified


class UserRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    firstName = serializers.CharField(max_length=100)
    lastName = serializers.CharField(max_length=100)
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        if user_manager.get_user_by_email(value):
            raise serializers.ValidationError("This email is already registered.")
        return value

    def create(self, validated_data):
        return user_manager.create_user(
            email=validated_data["email"],
            first_name=validated_data["firstName"],
            last_name=validated_data["lastName"],
            password=validated_data["password"],
        )


class UserSerializer(serializers.Serializer):
    """User document from Mongo (dict)."""

    id = serializers.SerializerMethodField()
    email = serializers.EmailField()
    firstName = serializers.CharField()
    lastName = serializers.CharField()
    role = serializers.SerializerMethodField()
    is_email_verified = serializers.SerializerMethodField()
    auth_method = serializers.SerializerMethodField()

    def get_id(self, obj):
        return str(obj.get("_id"))

    def get_role(self, obj):
        return normalize_role(obj.get("role"))

    def get_is_email_verified(self, obj):
        return effective_email_verified(obj)

    def get_auth_method(self, obj):
        return obj.get("auth_method") or "password"


class ProfilePatchSerializer(serializers.Serializer):
    firstName = serializers.CharField(max_length=100, required=False)
    lastName = serializers.CharField(max_length=100, required=False)


class EmailOnlyRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    firstName = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    lastName = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")

    def validate_email(self, value):
        if user_manager.get_user_by_email(value):
            raise serializers.ValidationError("This email is already registered.")
        return value

    def create(self, validated_data):
        return user_manager.create_email_only_user(
            email=validated_data["email"],
            first_name=validated_data.get("firstName") or "",
            last_name=validated_data.get("lastName") or "",
        )


class OtpRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    purpose = serializers.ChoiceField(choices=("register", "login_email"))


class OtpVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=12, min_length=4, trim_whitespace=True)
    purpose = serializers.ChoiceField(choices=("register", "login_email"))


class GoogleOAuthSerializer(serializers.Serializer):
    code = serializers.CharField()
    code_verifier = serializers.CharField()
    redirect_uri = serializers.URLField()


class GitHubOAuthSerializer(serializers.Serializer):
    code = serializers.CharField()
    code_verifier = serializers.CharField()
    redirect_uri = serializers.URLField()


class APIKeySerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    key = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=100)
    created_at = serializers.DateTimeField(read_only=True)

    def get_id(self, obj):
        return str(obj.get("_id"))


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=12, min_length=4, trim_whitespace=True)
    password = serializers.CharField(min_length=8, write_only=True)


class AdminSetUserRoleSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=[r for r in ROLES] + ["user"])
