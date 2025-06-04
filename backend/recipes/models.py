from django.db import models
from django.conf import settings
from ingredients.models import Ingredient


class Recipe(models.Model):
    name = models.CharField("Name", max_length=200)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Author",
    )
    text = models.TextField("Description")
    image = models.ImageField("Image", upload_to="recipes/images/")
    cooking_time = models.PositiveSmallIntegerField("Cooking time (minutes)")
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        related_name="recipes",
        verbose_name="Ingredients",
    )
    pub_date = models.DateTimeField("Publication date", auto_now_add=True)

    class Meta:
        ordering = ("-pub_date",)
        verbose_name = "Recipe"
        verbose_name_plural = "Recipes"

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        verbose_name="Recipe",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        verbose_name="Ingredient",
    )
    amount = models.PositiveSmallIntegerField("Amount")

    class Meta:
        verbose_name = "Recipe Ingredient"
        verbose_name_plural = "Recipe Ingredients"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"], name="unique_recipe_ingredient"
            )
        ]

    def __str__(self):
        return f"{self.ingredient.name} в {self.recipe.name}"


class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="User",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Recipe",
    )
    added_at = models.DateTimeField("Added date", auto_now_add=True)

    class Meta:
        verbose_name = "Favorite Recipe"
        verbose_name_plural = "Favorite Recipes"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_favorite_recipe"
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.recipe.name}"


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shopping_cart",
        verbose_name="User",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="shopping_cart",
        verbose_name="Recipe",
    )
    added_at = models.DateTimeField("Added date", auto_now_add=True)

    class Meta:
        verbose_name = "Shopping Cart Item"
        verbose_name_plural = "Shopping Cart Items"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_recipe_in_cart"
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.recipe.name}"
