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


class BooleanRelatedFieldFilter(admin.SimpleListFilter):
    LOOKUP_CHOICES = (
        ("yes", "Да"),
        ("no", "Нет"),
    )
    related_field = None

    def lookups(self, request, model_admin):
        return self.LOOKUP_CHOICES

    def queryset(self, request, queryset):
        if not self.related_field:
            return queryset

        if self.value() == "yes":
            return queryset.filter(
                **{f"{self.related_field}__isnull": False}
            ).distinct()
        if self.value() == "no":
            return queryset.filter(
                **{f"{self.related_field}__isnull": True}
            ).distinct()


class HasRecipesFilter(BooleanRelatedFieldFilter):
    title = "Есть рецепты"
    parameter_name = "has_recipes"
    related_field = "recipes"


class HasSubscriptionsFilter(BooleanRelatedFieldFilter):
    title = "Есть подписки"
    parameter_name = "has_subscriptions"
    related_field = "subscriptions"


class HasSubscribersFilter(BooleanRelatedFieldFilter):
    title = "Есть подписчики"
    parameter_name = "has_subscribers"
    related_field = "subscriptions_authors"


class IsUsedInRecipesFilter(BooleanRelatedFieldFilter):
    title = "Используется в рецептах"
    parameter_name = "is_used_in_recipes"
    related_field = "recipes"


class CookingTimeFilter(admin.SimpleListFilter):
    title = "Время приготовления"
    parameter_name = "cooking_time"

    def lookups(self, request, model_admin):
        times = (
            Recipe.objects.values_list("cooking_time", flat=True)
            .distinct()
            .order_by("cooking_time")
        )

        if len(times) < 3:
            return ()

        n = len(times)
        idx1 = n // 3
        idx2 = (2 * n) // 3

        self.threshold1 = times[idx1]
        self.threshold2 = times[idx2]

        return (
            ("quick", f"Быстрые (до {self.threshold1} мин)"),
            (
                "medium",
                f"Средние ({self.threshold1 + 1}–{self.threshold2} мин)",
            ),
            ("slow", f"Долгие (более {self.threshold2} мин)"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            return queryset

        if value == "quick":
            return queryset.filter(cooking_time__lte=self.threshold1)
        elif value == "medium":
            return queryset.filter(
                cooking_time__gt=self.threshold1,
                cooking_time__lte=self.threshold2,
            )
        elif value == "slow":
            return queryset.filter(cooking_time__gt=self.threshold2)

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
            recipe_count=Count("recipes"),
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

    @display(description="Имя")
    def full_name(self, user):
        return user.get_full_name()

    @display(description="Рецептов")
    def recipe_count(self, user):
        return user.recipes.count()

    @display(description="Подписки")
    def subscription_count(self, user):
        return user.subscriptions.count()

    @display(description="Подписчики")
    def subscriber_count(self, user):
        return user.subscriptions_authors.count()


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

    @admin.display(description="Рецептов")
    def recipe_count(self, ingredient):
        return ingredient.recipes.count()

    @admin.display(boolean=True, description="Используется в рецептах")
    def is_used_in_recipes(self, ingredient):
        return ingredient.recipes.exists()


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
        return mark_safe(
            "<br>".join(
                f"{ingredient.ingredient.name} ({ingredient.amount} "
                f"{ingredient.ingredient.measurement_unit})"
                for ingredient in recipe.recipe_ingredients.all()
            )
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

    @admin.display(description="В избранном")
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
