from rest_framework import serializers
from django.contrib.auth import get_user_model
from ingredients.models import Ingredient
from .models import Recipe, RecipeIngredient, ShoppingCart, Favorite
import uuid
import base64
from django.core.files.base import ContentFile
from users.serializers import UserSerializer as UserSerializer

User = get_user_model()


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipe data in subscriptions"""

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
        read_only_fields = ("id", "name", "image", "cooking_time")

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop("fields", None)
        super().__init__(*args, **kwargs)
        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="recipe.name")
    image = serializers.ImageField(source="recipe.image", use_url=True)
    cooking_time = serializers.IntegerField(source="recipe.cooking_time")

    class Meta:
        model = Favorite
        fields = ("id", "name", "image", "cooking_time")
        read_only_fields = ("id", "name", "image", "cooking_time")


class RecipeLinkSerializer(serializers.Serializer):
    short_link = serializers.SerializerMethodField()

    def encode_id(self, id):
        hex_str = f"{id:x}"
        return hex_str.zfill(2)

    def get_short_link(self, obj):
        short_code = self.encode_id(obj.id)
        return f"/s/{short_code}"

    def to_representation(self, instance):
        return {"short-link": self.get_short_link(instance)}


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]
            filename = f"{uuid.uuid4()}.{ext}"
            data = ContentFile(base64.b64decode(imgstr), name=filename)
        return super().to_internal_value(data)


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount")
        read_only_fields = ("id",)

    def validate_id(self, value):
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"Ingredient with id {value} not found")
        return value

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value

    def to_representation(self, instance):
        if isinstance(instance, RecipeIngredient):
            return {
                "id": instance.ingredient_id,
                "name": instance.ingredient.name,
                "measurement_unit": instance.ingredient.measurement_unit,
                "amount": instance.amount,
            }

        return instance


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = IngredientInRecipeSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ("id", "ingredients", "name", "image", "text", "cooking_time")
        read_only_fields = ("id",)

    def validate_cooking_time(self, value):
        if value <= 0:
            raise serializers.ValidationError("Cooking time must be greater than 0")
        return value

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError("Ingredients list cannot be empty")

        ingredients = []
        for item in value:
            ingredient = Ingredient.objects.filter(id=item["id"]).first()
            if not ingredient:
                raise serializers.ValidationError(
                    f"Ingredient with id {item['id']} not found"
                )
            if ingredient in ingredients:
                raise serializers.ValidationError(
                    "Duplicate ingredients are not allowed"
                )
            ingredients.append(ingredient)
        return value

    def validate(self, data):
        if self.instance and not data.get("ingredients"):
            raise serializers.ValidationError(
                {"ingredients": ["This field is required"]}
            )
        return data

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.text = validated_data.get("text", instance.text)
        instance.cooking_time = validated_data.get(
            "cooking_time", instance.cooking_time
        )

        image = validated_data.get("image")
        if image:
            instance.image = image
        ingredients = validated_data.get("ingredients")
        if ingredients:
            RecipeIngredient.objects.filter(recipe=instance).delete()
            for ingredient_data in ingredients:
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient_id=ingredient_data["id"],
                    amount=ingredient_data["amount"],
                )

        instance.save()
        return instance

    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients")

        recipe = Recipe.objects.create(
            author=self.context["request"].user, **validated_data
        )
        for ingredient_data in ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=ingredient_data["id"],
                amount=ingredient_data["amount"],
            )

        serializer = RecipeListSerializer(
            recipe, context={"request": self.context.get("request")}
        )
        return serializer


class ShoppingCartRecipeSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="recipe.name")
    image = serializers.ImageField(source="recipe.image", use_url=True)
    cooking_time = serializers.IntegerField(source="recipe.cooking_time")

    class Meta:
        model = ShoppingCart
        fields = ("id", "name", "image", "cooking_time")
        read_only_fields = ("id", "name", "image", "cooking_time")


class RecipeListSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(many=True, source="recipe_ingredients")
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.ImageField(use_url=True)

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
        read_only_fields = (
            "id",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
        )

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.favorites.filter(user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.shopping_cart.filter(user=request.user).exists()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        author_data = UserSerializer(instance.author, context=self.context).data
        data["author"] = {
            "id": author_data["id"],
            "username": author_data["username"],
            "first_name": author_data["first_name"],
            "last_name": author_data["last_name"],
            "email": author_data["email"],
            "is_subscribed": False,
            "avatar": author_data.get("avatar", None),
        }
        data["ingredients"] = [
            {
                "id": ingredient.ingredient_id,
                "name": ingredient.ingredient.name,
                "measurement_unit": ingredient.ingredient.measurement_unit,
                "amount": ingredient.amount,
            }
            for ingredient in instance.recipe_ingredients.all()
        ]
        data["is_favorited"] = self.get_is_favorited(instance)
        data["is_in_shopping_cart"] = self.get_is_in_shopping_cart(instance)
        data["image"] = instance.image.url if instance.image else ""
        return data
