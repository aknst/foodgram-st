from django.contrib import admin
from django.contrib.admin import display
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscription,
    User,
)


class HasRecipesFilter(admin.SimpleListFilter):
    title = "Есть рецепты"
    parameter_name = "has_recipes"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Да"),
            ("no", "Нет"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(authored_recipes__isnull=False).distinct()
        if self.value() == "no":
            return queryset.filter(authored_recipes__isnull=True)


class HasSubscriptionsFilter(admin.SimpleListFilter):
    title = "Есть подписки"
    parameter_name = "has_subscriptions"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Да"),
            ("no", "Нет"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(subscriptions__isnull=False).distinct()
        if self.value() == "no":
            return queryset.filter(subscriptions__isnull=True)


class HasSubscribersFilter(admin.SimpleListFilter):
    title = "Есть подписчики"
    parameter_name = "has_subscribers"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Да"),
            ("no", "Нет"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(
                subscriptions_authors__isnull=False
            ).distinct()
        if self.value() == "no":
            return queryset.filter(subscriptions_authors__isnull=True)


class IsUsedInRecipesFilter(admin.SimpleListFilter):
    title = "Используется в рецептах"
    parameter_name = "is_used_in_recipes"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Да"),
            ("no", "Нет"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(used_in_recipes__isnull=False).distinct()
        if self.value() == "no":
            return queryset.filter(used_in_recipes__isnull=True)


class CookingTimeFilter(admin.SimpleListFilter):
    title = "Время приготовления"
    parameter_name = "cooking_time"

    def lookups(self, request, model_admin):
        recipes = Recipe.objects.all()
        if not recipes.exists():
            return (
                ("quick", "Быстрые"),
                ("medium", "Средние"),
                ("slow", "Долгие"),
            )

        cooking_times = recipes.values_list("cooking_time", flat=True)
        max_time = max(cooking_times)

        quick_max = max_time * 0.33
        medium_max = max_time * 0.66

        return (
            (
                f"quick_{quick_max}",
                f"Быстрые (до {quick_max:.0f} мин)",
            ),
            (
                f"medium_{medium_max}",
                f"Средние (до {medium_max:.0f} мин)",
            ),
            (
                f"slow_{max_time}",
                f"Долгие (более {medium_max:.0f} мин)",
            ),
        )

    def queryset(self, request, queryset):
        if self.value():
            value, max_time = self.value().split("_")
            max_time = float(max_time)
            if value == "quick":
                return queryset.filter(cooking_time__lte=max_time)
            elif value == "medium":
                return queryset.filter(
                    cooking_time__gt=max_time / 3,
                    cooking_time__lte=max_time * 2 / 3,
                )
            elif value == "slow":
                return queryset.filter(cooking_time__gt=max_time * 2 / 3)
        return queryset


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {"fields": ("id", "username", "password")}),
        (
            "Личная информация",
            {"fields": ("first_name", "last_name", "email", "avatar")},
        ),
        (
            "Права доступа",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Время активности", {"fields": ("last_login", "date_joined")}),
    )

    list_display = (
        "id",
        "username",
        "full_name",
        "email",
        "avatar_html",
        "recipe_count",
        "subscription_count",
        "subscriber_count",
        "is_staff",
    )

    search_fields = ("username", "email", "first_name", "last_name")
    list_filter = (
        HasRecipesFilter,
        HasSubscriptionsFilter,
        HasSubscribersFilter,
        "is_active",
        "is_staff",
    )
    readonly_fields = ("id",)
    ordering = ("username",)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            recipe_count=Count("authored_recipes"),
            subscription_count=Count("subscriptions"),
            subscriber_count=Count("subscriptions_authors"),
        )

    @display(description="Аватар")
    @mark_safe
    def avatar_html(self, user):
        if user.avatar:
            return (
                f'<img src="{user.avatar.url}"'
                ' width="30" height="30"'
                f' alt="{user.username}">'
            )
        return "-"

    @display(description="Имя пользователя")
    def full_name(self, user):
        return user.get_full_name()

    @display(description="Кол-во рецептов")
    def recipe_count(self, user):
        return user.authored_recipes.count()

    @display(description="Подписки")
    def subscription_count(self, user):
        return user.subscriptions.count()

    @display(description="Подписчики")
    def subscriber_count(self, user):
        return user.subscriptions_authors.count()

    @display(boolean=True, description="Есть рецепты")
    def has_authored_recipes(self, user):
        return user.has_authored_recipes > 0

    @display(boolean=True, description="Есть подписки")
    def has_subscriptions(self, user):
        return user.has_subscriptions > 0

    @display(boolean=True, description="Есть подписчики")
    def has_subscribers(self, user):
        return user.has_subscribers > 0


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("subscriber", "author")
    list_filter = ("subscriber", "author")
    search_fields = ("subscriber__username", "author__username")
    empty_value_display = "-пусто-"

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        ordering = ("subscriber", "author")


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "measurement_unit",
        "recipe_count",
        "is_used_in_recipes",
    )
    search_fields = ("name", "measurement_unit")
    list_filter = ("measurement_unit", IsUsedInRecipesFilter)
    ordering = ("name",)

    @admin.display(description="Количество рецептов")
    def recipe_count(self, ingredient):
        return ingredient.used_in_recipes.count()

    @admin.display(boolean=True, description="Используется в рецептах")
    def is_used_in_recipes(self, ingredient):
        return ingredient.used_in_recipes.exists()


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "cooking_time",
        "author",
        "favorite_count",
        "ingredients_list",
        "image_preview",
    )
    list_filter = (
        CookingTimeFilter,
        "author",
        "pub_date",
    )
    search_fields = (
        "name",
        "author__username",
        "text",
    )
    readonly_fields = (
        "pub_date",
        "favorite_count",
        "image_preview",
    )
    empty_value_display = "-пусто-"
    ordering = ("-pub_date",)

    @admin.display(description="Ингредиенты")
    def ingredients_list(self, recipe):
        ingredients = recipe.recipe_ingredients.all()
        if not ingredients:
            return mark_safe("-пусто-")

        items = "".join(
            f"<li>"
            f"{ingredient.ingredient.name} ({ingredient.amount} "
            f"{ingredient.ingredient.measurement_unit})</li>"
            for ingredient in ingredients
        )

        return mark_safe(
            f'<ul style="margin: 0; padding-left: 20px;">{items}</ul>'
        )

    @admin.display(description="Изображение")
    @mark_safe
    def image_preview(self, recipe):
        if recipe.image:
            return format_html(
                '<img src="{}" width="100" height="100" '
                'style="object-fit: cover;">',
                recipe.image.url,
            )
        return "-пусто-"

    @admin.display(description="Добавлений в избранное")
    def favorite_count(self, recipe):
        return recipe.favorite_set.count()


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ("recipe", "ingredient", "amount")
    list_filter = ("recipe",)
    search_fields = ("recipe__name", "ingredient__name")
    empty_value_display = "-пусто-"


@admin.register(Favorite, ShoppingCart)
class RecipeAssociationAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
    list_filter = ("user", "recipe")
    search_fields = ("user__username", "recipe__name")
    empty_value_display = "-пусто-"
