from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from rest_framework.authtoken.models import Token
from rest_framework.validators import UniqueValidator
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

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "password")
        extra_kwargs = {"password": {"write_only": True}}

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
                _("Unable to log in with provided credentials.")
            )

        token, created = Token.objects.get_or_create(user=user)
        return {"auth_token": token.key}
