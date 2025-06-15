from django.contrib import admin

from ingredients.models import Ingredient


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
            return queryset.filter(recipes__isnull=False).distinct()
        if self.value() == "no":
            return queryset.filter(recipes__isnull=True)


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
    def recipe_count(self, obj):
        return obj.recipes.count()

    @admin.display(boolean=True, description="Используется в рецептах")
    def is_used_in_recipes(self, obj):
        return obj.recipes.exists()
