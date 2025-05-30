from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from .models import Recipe
from .serializers import RecipeCreateSerializer, RecipeListSerializer
from .filters import RecipeFilter
from .pagination import CustomPagination


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = RecipeFilter
    search_fields = ["name"]
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action in ["create", "partial_update"]:
            return RecipeCreateSerializer
        return RecipeListSerializer

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        context = self.get_serializer_context()
        context["request"] = self.request
        kwargs["context"] = context

        if self.action == "list":
            kwargs["many"] = True

        return serializer_class(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response_serializer = serializer.save()
        headers = self.get_success_headers(response_serializer.data)

        return Response(
            response_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # Get paginated results
        page = self.paginate_queryset(queryset)
        if page is not None:
            # Serialize the paginated page
            serializer = self.get_serializer(page, many=True)
            # Return paginated response with proper format
            return self.get_paginated_response(serializer.data)

        # If no pagination
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_permissions(self):
        if self.action in ["create", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        if request.method == "POST":
            recipe.favorites.create(user=request.user)
            return Response(status=status.HTTP_201_CREATED)

        recipe.favorites.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        if request.method == "POST":
            recipe.shopping_cart.create(user=request.user)
            serializer = RecipeListSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        recipe.shopping_cart.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        # TODO: Implement shopping cart download
        pass
