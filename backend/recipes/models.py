from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import MinValueValidator
from django.db import models


class User(AbstractUser):
    email = models.EmailField(
        "Адрес электронной почты",
        unique=True,
        max_length=254,
    )
    username = models.CharField(
        "Юзернейм",
        unique=True,
        max_length=150,
        validators=[
            UnicodeUsernameValidator(),
        ],
    )
    first_name = models.CharField("Имя", max_length=150)
    last_name = models.CharField("Фамилия", max_length=150)
    avatar = models.ImageField(
        "Ссылка на аватар", upload_to="avatars/", null=True, blank=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("username",)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        User,
        related_name="subscriptions",
        on_delete=models.CASCADE,
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        User,
        related_name="subscriptions_authors",
        on_delete=models.CASCADE,
        verbose_name="Автор",
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                fields=["subscriber", "author"], name="unique_subscription"
            ),
            models.CheckConstraint(
                condition=~models.Q(subscriber=models.F("author")),
                name="prevent_self_subscription",
            ),
        ]


class Ingredient(models.Model):
    name = models.CharField(
        max_length=128, verbose_name="Название ингредиента"
    )
    measurement_unit = models.CharField(
        max_length=64, verbose_name="Единица измерения"
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ("name",)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField("Название", max_length=256)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="authored_recipes",
        verbose_name="Автор",
    )
    text = models.TextField("Описание")
    image = models.ImageField("Изображение", upload_to="recipes/images/")
    cooking_time = models.PositiveIntegerField(
        "Время приготовления (минуты)", validators=[MinValueValidator(1)]
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        related_name="used_in_recipes",
        verbose_name="Ингредиенты",
    )
    pub_date = models.DateTimeField("Дата публикации", auto_now_add=True)

    class Meta:
        ordering = ("-pub_date",)
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="recipes_used_in",
        verbose_name="Ингредиент",
    )
    amount = models.PositiveSmallIntegerField(
        "Количество", validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = "Ингредиент рецепта"
        verbose_name_plural = "Ингредиенты рецептов"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_recipe_ingredient",
            )
        ]
        ordering = ["ingredient__name"]


class RecipeAssociation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="%(app_label)s_%(class)s_unique",
            )
        ]


class Favorite(RecipeAssociation):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorite_set",
        verbose_name="Рецепт",
    )

    class Meta(RecipeAssociation.Meta):
        verbose_name = "Избранный рецепт"
        verbose_name_plural = "Избранные рецепты"
        db_table = "recipes_favorite"


class ShoppingCart(RecipeAssociation):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="shoppingcart_set",
        verbose_name="Рецепт",
    )

    class Meta(RecipeAssociation.Meta):
        verbose_name = "Рецепт в корзине"
        verbose_name_plural = "Рецепты в корзине"
        db_table = "recipes_shoppingcart"
