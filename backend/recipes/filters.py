from django_filters import rest_framework as filters

from .models import Recipe


class RecipeFilter(filters.FilterSet):
    is_favorited = filters.BooleanFilter(method="filter_is_favorited")
    is_in_shopping_cart = filters.BooleanFilter(
        method="filter_is_in_shopping_cart"
    )

    class Meta:
        model = Recipe
        fields = ["author", "is_favorited", "is_in_shopping_cart"]

    def filter_is_favorited(self, recipes, name, value):
        if not self.request.user.is_authenticated:
            return recipes

        if value:
            return recipes.filter(favorite_set__user=self.request.user)
        return recipes

    def filter_is_in_shopping_cart(self, recipes, name, value):
        if not self.request.user.is_authenticated:
            return recipes

        if value:
            return recipes.filter(shoppingcart_set__user=self.request.user)
        return recipes.exclude(shoppingcart_set__user=self.request.user)
