from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.db import models
from .models import Recipe, ShoppingCart, RecipeIngredient, Favorite
from .serializers import (
    RecipeCreateSerializer,
    RecipeListSerializer,
    RecipeLinkSerializer,
    ShoppingCartRecipeSerializer,
    FavoriteRecipeSerializer,
)
from .filters import RecipeFilter
from .pagination import CustomPagination


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = RecipeFilter
    search_fields = ["name"]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action in ["create", "partial_update"]:
            return RecipeCreateSerializer
        return RecipeListSerializer

    def get_serializer(self, *args, **kwargs):
        context = self.get_serializer_context()
        context["request"] = self.request
        kwargs["context"] = context

        if self.action == "list":
            kwargs["many"] = True

        serializer_class = self.get_serializer_class()
        return serializer_class(*args, **kwargs)

    def get_queryset(self):
        queryset = self.queryset
        
        # For unauthenticated users, return all recipes
        if not self.request.user.is_authenticated:
            return queryset
            
        # For authenticated users, apply filters
        filters = {}
        if self.request.query_params.get('is_favorited') == '1':
            filters['favorites__user'] = self.request.user
        if self.request.query_params.get('is_in_shopping_cart') == '1':
            filters['shopping_cart__user'] = self.request.user
        
        if filters:
            return queryset.filter(**filters)
        return queryset

    @action(
        detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = request.user

        ingredients = (
            RecipeIngredient.objects.filter(recipe__shopping_cart__user=user)
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total_amount=models.Sum("amount"))
            .order_by("ingredient__name")
        )

        content = "\n\n".join(
            [
                f"{item['ingredient__name']} ({item['ingredient__measurement_unit']}) - {item['total_amount']}"
                for item in ingredients
            ]
        )

        response = HttpResponse(content, content_type="text/plain")
        response["Content-Disposition"] = 'attachment; filename="shopping_cart.txt"'
        return response

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response_serializer = serializer.save()
        headers = self.get_success_headers(response_serializer.data)

        return Response(
            response_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        if instance.author != request.user:
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        updated_instance = self.get_object()
        response_serializer = RecipeListSerializer(
            updated_instance, context={"request": request}
        )

        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}

        return Response(response_serializer.data)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_permissions(self):
        if self.action in ["create", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if instance.author != request.user:
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        recipe = self.get_object()
        
        if request.method == "DELETE":
            favorite = Favorite.objects.filter(user=request.user, recipe=recipe)
            if not favorite.exists():
                return Response(
                    {"errors": ["Recipe is not in favorites"]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if Favorite.objects.filter(user=request.user, recipe=recipe).exists():
            return Response(
                {"errors": ["Recipe is already in favorites"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        favorite = Favorite.objects.create(user=request.user, recipe=recipe)
        serializer = FavoriteRecipeSerializer(
            favorite, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[permissions.IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        recipe = self.get_object()
        
        if request.method == "DELETE":
            cart_item = ShoppingCart.objects.filter(
                user=request.user, recipe=recipe
            )
            
            if not cart_item.exists():
                return Response(
                    {"errors": ["Recipe is not in shopping cart"]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if ShoppingCart.objects.filter(user=request.user, recipe=recipe).exists():
            return Response(
                {"errors": ["Recipe is already in shopping cart"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart_item = ShoppingCart.objects.create(user=request.user, recipe=recipe)
        serializer = ShoppingCartRecipeSerializer(
            cart_item, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        serializer = RecipeLinkSerializer(recipe)
        return Response(serializer.data)
