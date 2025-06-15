from datetime import datetime
from io import BytesIO

from django.db import models
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from .filters import RecipeFilter
from .models import Favorite, Recipe, RecipeIngredient, ShoppingCart
from .permissons import IsAuthorOrReadOnly
from .serializers import (
    RecipeListSerializer,
    RecipeSerializer,
    RecipeWriteSerializer,
)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = RecipeFilter
    search_fields = ["name"]
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_serializer_class(self):
        if self.action in ["create", "partial_update"]:
            return RecipeWriteSerializer
        return RecipeListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_authenticated:
            if self.request.query_params.get("is_favorited") == "1":
                qs = qs.filter(favorite_set__user=user)
            if self.request.query_params.get("is_in_shopping_cart") == "1":
                qs = qs.filter(shoppingcart_set__user=user)
        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        return self._toggle_relation(request, self.get_object(), Favorite)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        return self._toggle_relation(request, self.get_object(), ShoppingCart)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        user = request.user

        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__shoppingcart_set__user=user
            )
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total_amount=models.Sum("amount"))
            .order_by("ingredient__name")
        )

        recipes = (
            Recipe.objects.filter(shoppingcart_set__user=user)
            .select_related("author")
            .distinct()
        )

        content = (
            "\n".join(
                [
                    f"Список покупок сгенерирован: "
                    f"{datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    "",
                    "Ингредиенты:",
                    *[
                        f"{idx}. {item['ingredient__name'].capitalize()} "
                        f"({item['ingredient__measurement_unit']}) – "
                        f"{item['total_amount']}"
                        for idx, item in enumerate(ingredients, 1)
                    ],
                    "",
                    "Рецепты с этими ингредиентами:",
                    *[
                        f"- {r.name} by "
                        f"{r.author.get_full_name() or r.author.username}"
                        for r in recipes
                    ],
                ]
            )
            + "\n"
        )

        buffer = BytesIO(content.encode("utf-8"))
        return FileResponse(
            buffer,
            as_attachment=True,
            filename="shopping_cart.txt",
            content_type="text/plain",
        )

    def _toggle_relation(self, request, recipe, model):
        user = request.user
        if request.method == "POST":
            obj, created = model.objects.get_or_create(
                user=user, recipe=recipe
            )
            if not created:
                return Response(
                    {"detail": f"Recipe {recipe.id} is already added"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = RecipeSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        deleted_count, _ = model.objects.filter(
            user=user, recipe=recipe
        ).delete()
        if deleted_count == 0:
            return Response(
                {"detail": f"Recipe {recipe.id} was not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["get"],
        url_path="get-link",
        permission_classes=[AllowAny],
    )
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        short_url = request.build_absolute_uri(f"/s/{recipe.id}")
        return Response({"short-link": short_url})


def redirect_short_link(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    return redirect(f"/recipes/{recipe.id}")
