from datetime import datetime

from django.db import models
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscription,
    User,
)
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
from .permissons import IsAuthorOrReadOnly
from .serializers import (
    IngredientSerializer,
    RecipeListSerializer,
    RecipeSerializer,
    RecipeWriteSerializer,
    UserAvatarSerializer,
    UserProfileSerializer,
    UserWithRecipesSerializer,
)


class UserViewSet(DjoserUserViewSet):
    serializer_class = UserProfileSerializer

    def get_permissions(self):
        if self.action == "me":
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        author_to_follow = get_object_or_404(User, id=id)
        current_user = request.user

        if request.method == "POST":
            if current_user == author_to_follow:
                return Response(
                    {"detail": "Вы не можете подписаться на себя."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            subscription, created = Subscription.objects.get_or_create(
                subscriber=current_user,
                author=author_to_follow,
            )
            if not created:
                return Response(
                    {
                        "detail": (
                            f"Вы уже подписаны на пользователя "
                            f"'{author_to_follow.username}'"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = UserWithRecipesSerializer(
                author_to_follow, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        subscription_qs = Subscription.objects.filter(
            subscriber=current_user, author=author_to_follow
        )
        if not subscription_qs.exists():
            return Response(
                {
                    "detail": (
                        f"Вы не подписаны на пользователя "
                        f"'{author_to_follow.username}'"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        subscription_qs.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"])
    def subscriptions(self, request):
        subscriptions = request.user.subscriptions.select_related(
            "author"
        ).all()
        authors = [sub.author for sub in subscriptions]

        page = self.paginate_queryset(authors)
        return self.get_paginated_response(
            UserWithRecipesSerializer(
                page,
                many=True,
                context={"request": request},
            ).data
        )

    @action(
        detail=False,
        methods=["put", "delete"],
        permission_classes=[IsAuthenticated],
        serializer_class=UserAvatarSerializer,
        url_path="me/avatar",
    )
    def avatar(self, request):
        user = request.user
        if request.method == "PUT":
            serializer = self.get_serializer(user, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        elif request.method == "DELETE":
            if user.avatar:
                user.avatar.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {"detail": "Аватар не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = self.queryset
        name = self.request.query_params.get("name")
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


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
                        f"- {r.name}, автор: "
                        f"{r.author.get_full_name() or r.author.username}"
                        for r in recipes
                    ],
                ]
            )
            + "\n"
        )

        return FileResponse(
            content,
            as_attachment=True,
            filename="shopping_cart.txt",
            content_type="text/plain",
        )

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

    def _toggle_relation(self, request, recipe, model):
        user = request.user
        loc_name = "в избранном" if model == Favorite else "в корзине"
        if request.method == "POST":
            obj, created = model.objects.get_or_create(
                user=user, recipe=recipe
            )
            if not created:
                return Response(
                    {"detail": f"Рецепт '{recipe.name}' уже {loc_name}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = RecipeSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        deleted_count, _ = model.objects.filter(
            user=user, recipe=recipe
        ).delete()
        if deleted_count == 0:
            return Response(
                {"detail": f"Рецепт '{recipe.name}' не найден {loc_name}."},
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
        exists = Recipe.objects.filter(pk=pk).exists()
        if not exists:
            return Response(
                {"detail": "Рецепт не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )
        short_url = request.build_absolute_uri(f"/s/{pk}")
        return Response({"short-link": short_url})
