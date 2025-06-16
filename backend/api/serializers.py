from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import Ingredient, Recipe, RecipeIngredient, Subscription
from rest_framework import serializers

User = get_user_model()


class UserProfileSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, read_only=True)

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
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserProfileSerializer.Meta):
        fields = UserProfileSerializer.Meta.fields + (
            "recipes_count",
            "recipes",
        )

    def get_recipes_count(self, user):
        return user.authored_recipes.count()

    def get_recipes(self, user):
        request = self.context.get("request")
        limit = request.query_params.get("recipes_limit")
        qs = user.authored_recipes.all()
        if limit and limit.isdigit():
            qs = qs[: int(limit)]
        return RecipeSerializer(
            qs, many=True, context={"request": request}
        ).data


class UserWithRecipesSerializer(UserProfileSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source="authored_recipes.count", read_only=True
    )

    class Meta(UserProfileSerializer.Meta):
        model = User
        fields = UserProfileSerializer.Meta.fields + (
            "recipes",
            "recipes_count",
        )

    def get_recipes(self, user):
        request = self.context.get("request")
        limit = request.query_params.get("recipes_limit")
        qs = user.authored_recipes.all()
        if limit is not None and limit.isdigit():
            qs = qs[: int(limit)]
        return RecipeSerializer(qs, many=True, context=self.context).data


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")
        read_only_fields = fields


class RecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
        read_only_fields = fields


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source="ingredient",
    )
    name = serializers.CharField(source="ingredient.name", read_only=True)
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit", read_only=True
    )
    amount = serializers.IntegerField(validators=[MinValueValidator(1)])

    class Meta:
        model = RecipeIngredient
        fields = (
            "id",
            "name",
            "measurement_unit",
            "amount",
        )


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = IngredientInRecipeSerializer(
        many=True,
        required=True,
    )
    cooking_time = serializers.IntegerField(
        validators=[MinValueValidator(1)],
    )
    image = Base64ImageField(required=True, allow_empty_file=False)

    class Meta:
        model = Recipe
        fields = ("id", "ingredients", "name", "image", "text", "cooking_time")
        read_only_fields = ("id",)

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError("Ингредиенты обязательны.")
        ingredients = [item["ingredient"] for item in value]
        if len(ingredients) != len(set(ingredients)):
            raise serializers.ValidationError(
                "Ингредиенты не должны повторяться."
            )
        return value

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError("Изображение обязательно.")
        return value

    def validate(self, attrs):
        if self.partial and "ingredients" not in self.initial_data:
            raise serializers.ValidationError(
                {"ingredients": "Ингредиенты обязательны для обновления."}
            )
        return super().validate(attrs)

    def _save_ingredients(self, recipe, ingredients_data):
        objs = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=item["ingredient"],
                amount=item["amount"],
            )
            for item in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(objs)

    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        recipe = super().create(validated_data)
        self._save_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop("ingredients", None)
        recipe = super().update(instance, validated_data)
        if ingredients_data is not None:
            recipe.recipe_ingredients.all().delete()
            self._save_ingredients(recipe, ingredients_data)
        return recipe

    def to_representation(self, instance):
        return RecipeListSerializer(instance, context=self.context).data


class RecipeListSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        many=True, source="recipe_ingredients", read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )
        read_only_fields = fields

    def get_is_favorited(self, obj):
        user = self.context.get("request").user
        return (
            user.is_authenticated
            and obj.favorite_set.filter(user=user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get("request").user
        return (
            user.is_authenticated
            and obj.shoppingcart_set.filter(user=user).exists()
        )
