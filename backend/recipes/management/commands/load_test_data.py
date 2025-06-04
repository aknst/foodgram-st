from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from recipes.models import Recipe, RecipeIngredient
from ingredients.models import Ingredient
from django.conf import settings
import json
from pathlib import Path

User = get_user_model()


class Command(BaseCommand):
    help = "Load initial data from JSON files in data directory"

    def handle(self, *args, **options):
        data_dir = Path(settings.BASE_DIR).parent / "data"

        ingredients_file = data_dir / "ingredients.json"
        if ingredients_file.exists():
            with open(ingredients_file, "r", encoding="utf-8") as f:
                ingredients = json.load(f)
                for ingredient in ingredients:
                    Ingredient.objects.get_or_create(
                        name=ingredient["name"],
                        defaults={"measurement_unit": ingredient["measurement_unit"]},
                    )
                self.stdout.write(self.style.SUCCESS("Successfully loaded ingredients"))

        users_file = data_dir / "users.json"
        if users_file.exists():
            with open(users_file, "r", encoding="utf-8") as f:
                users_data = json.load(f)
                for user_data in users_data:
                    try:
                        user = User.objects.get(username=user_data["username"])
                        self.stdout.write(
                            self.style.WARNING(
                                f"User {user_data['username']} already exists, skipping..."
                            )
                        )
                        continue
                    except User.DoesNotExist:
                        user = User.objects.create_user(
                            username=user_data["username"],
                            email=user_data["email"],
                            first_name=user_data["first_name"],
                            last_name=user_data["last_name"],
                            password=user_data["password"],
                        )
                        self.stdout.write(
                            self.style.SUCCESS(f"Created user {user.username}")
                        )
                self.stdout.write(self.style.SUCCESS("Successfully loaded users"))

        recipes_file = data_dir / "recipes.json"
        if recipes_file.exists():
            with open(recipes_file, "r", encoding="utf-8") as f:
                recipes_data = json.load(f)
                ingredients = Ingredient.objects.all()

                for recipe_data in recipes_data:
                    author = User.objects.get(username=recipe_data["author"])
                    recipe, created = Recipe.objects.get_or_create(
                        author=author,
                        name=recipe_data["name"],
                        defaults={
                            "text": recipe_data["text"],
                            "cooking_time": recipe_data["cooking_time"],
                        },
                    )

                    if not created:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Recipe {recipe_data['name']} already exists, skipping..."
                            )
                        )
                        continue

                    for ingredient_data in recipe_data["ingredients"]:
                        try:
                            ingredient = ingredients.get(name=ingredient_data["name"])
                            RecipeIngredient.objects.get_or_create(
                                recipe=recipe,
                                ingredient=ingredient,
                                amount=ingredient_data["amount"],
                            )
                        except Ingredient.DoesNotExist:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"Warning: Ingredient '{ingredient_data['name']}' not found for recipe '{recipe.name}'"
                                )
                            )
                            continue

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Created recipe {recipe.name} by {author.username}"
                        )
                    )

        self.stdout.write(self.style.SUCCESS("Successfully loaded all data"))
