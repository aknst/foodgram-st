from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.serializers import RecipeSerializer
from rest_framework import serializers

from .models import Subscription

User = get_user_model()


class UserProfileSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            "is_subscribed",
            "avatar",
        )

    def get_is_subscribed(self, obj):
        request = self.context.get("request", None)
        if not request or not request.user.is_authenticated:
            return False
        if request.user == obj:
            return False
        return Subscription.objects.filter(
            subscriber=request.user,
            author=obj,
        ).exists()


class UserAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ("avatar",)


class SubscriptionsSerializer(UserProfileSerializer):
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta(UserProfileSerializer.Meta):
        fields = UserProfileSerializer.Meta.fields + (
            "recipes_count",
            "recipes",
        )

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get("request")
        limit = request.query_params.get("recipes_limit")
        qs = obj.recipes.all()
        if limit and limit.isdigit():
            qs = qs[: int(limit)]
        return RecipeSerializer(
            qs, many=True, context={"request": request}
        ).data


class UserWithRecipesSerializer(UserProfileSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source="recipes.count", read_only=True
    )

    class Meta(UserProfileSerializer.Meta):
        model = User
        fields = UserProfileSerializer.Meta.fields + (
            "recipes",
            "recipes_count",
        )
        read_only_fields = fields

    def get_recipes(self, user):
        request = self.context.get("request")
        limit = request.query_params.get("recipes_limit")
        qs = user.recipes.all()
        if limit is not None and limit.isdigit():
            qs = qs[: int(limit)]
        return RecipeSerializer(qs, many=True, context=self.context).data
