from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from rest_framework.authtoken.models import Token
from rest_framework.validators import UniqueValidator
from .fields import Base64ImageField
import re

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user registration and profile management"""

    email = serializers.EmailField(
        required=True,
        max_length=254,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message=_("This email address is already registered."),
            )
        ],
    )
    username = serializers.CharField(
        required=True,
        max_length=150,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message=_("This username is already taken."),
            ),
            RegexValidator(
                regex=r"^[\w.@+-]+$",
                message=_(
                    "Username must contain only letters, digits, and @/./+/-/_ characters"
                ),
            ),
        ],
    )
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)
    password = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )

    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "avatar",
        )
        extra_kwargs = {"password": {"write_only": True}}

    def to_representation(self, instance):
        """Add is_subscribed field for user list view"""
        representation = super().to_representation(instance)
        representation["is_subscribed"] = False
        return representation

    def validate_username(self, value):
        """Validate username format"""
        if not re.match(r"^[\w.@+-]+$", value):
            raise serializers.ValidationError(
                _(
                    "Username must contain only letters, digits, and @/./+/-/_ characters"
                )
            )
        return value

    def create(self, validated_data):
        """Create and return a new user"""
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class TokenSerializer(serializers.Serializer):
    """Serializer for token authentication"""

    auth_token = serializers.CharField(read_only=True)
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, data):
        """Validate user credentials and return token"""
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            raise serializers.ValidationError(_("Email and password are required."))

        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError(
                _("Unable to authenticate with provided credentials.")
            )

        token, created = Token.objects.get_or_create(user=user)
        return {"auth_token": token.key}


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for password reset"""

    current_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}, required=True
    )
    new_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}, required=True
    )

    def validate(self, data):
        """Validate current password and ensure new password is not empty"""
        current_password = data.get("current_password")
        new_password = data.get("new_password")

        if not current_password or not new_password:
            raise serializers.ValidationError(
                _("Both current and new passwords are required.")
            )

        if current_password == new_password:
            raise serializers.ValidationError(
                _("New password must be different from current password.")
            )

        return data
