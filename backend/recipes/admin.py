from django.contrib import admin

from .models import Favorite, Recipe, RecipeIngredient, ShoppingCart


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "author",
        "cooking_time",
        "pub_date",
        "favorite_count",
    )
    list_filter = ("author", "name")
    search_fields = ("name", "author__username")
    readonly_fields = ("pub_date", "favorite_count")
    empty_value_display = "-пусто-"

    def favorite_count(self, obj):
        return obj.favorites.count()

    favorite_count.short_description = "Количество добавлений в избранное"


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ("recipe", "ingredient", "amount")
    list_filter = ("recipe", "ingredient")
    search_fields = ("recipe__name", "ingredient__name")
    empty_value_display = "-пусто-"


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe", "added_at")
    list_filter = ("user", "recipe")
    search_fields = ("user__username", "recipe__name")
    empty_value_display = "-пусто-"


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe", "added_at")
    list_filter = ("user", "recipe")
    search_fields = ("user__username", "recipe__name")
    empty_value_display = "-пусто-"
