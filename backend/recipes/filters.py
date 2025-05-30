from django_filters import rest_framework as filters
from .models import Recipe


class RecipeFilter(filters.FilterSet):
    is_favorited = filters.BooleanFilter(method="filter_is_favorited")
    is_in_shopping_cart = filters.BooleanFilter(method="filter_is_in_shopping_cart")

    class Meta:
        model = Recipe
        fields = ["author", "is_favorited", "is_in_shopping_cart"]

    def filter_is_favorited(self, queryset, name, value):
        if value:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset
