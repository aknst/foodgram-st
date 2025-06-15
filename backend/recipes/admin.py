from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import Favorite, Recipe, RecipeIngredient, ShoppingCart


class CookingTimeFilter(admin.SimpleListFilter):
    title = "Время приготовления"
    parameter_name = "cooking_time"

    def lookups(self, request, model_admin):
        recipes = Recipe.objects.all()
        if not recipes.exists():
            return (
                ("quick", "Быстрые (0)"),
                ("medium", "Средние (0)"),
                ("slow", "Долгие (0)"),
            )

        cooking_times = recipes.values_list("cooking_time", flat=True)
        max_time = max(cooking_times)

        quick_max = max_time * 0.33
        medium_max = max_time * 0.66

        quick_count = recipes.filter(cooking_time__lte=quick_max).count()
        medium_count = recipes.filter(
            cooking_time__gt=quick_max, cooking_time__lte=medium_max
        ).count()
        slow_count = recipes.filter(cooking_time__gt=medium_max).count()

        return (
            (
                f"quick_{quick_max}",
                f"Быстрые (до {quick_max} мин) ({quick_count})",
            ),
            (
                f"medium_{medium_max}",
                f"Средние (до {medium_max} мин) ({medium_count})",
            ),
            (
                f"slow_{max_time}",
                f"Долгие (более {medium_max} мин) ({slow_count})",
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
    list_filter = ("recipe", "ingredient")
    search_fields = ("recipe__name", "ingredient__name")
    empty_value_display = "-пусто-"


@admin.register(Favorite, ShoppingCart)
class RecipeAssociationAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
    list_filter = ("user", "recipe")
    search_fields = ("user__username", "recipe__name")
    empty_value_display = "-пусто-"
