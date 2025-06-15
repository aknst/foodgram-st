from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Subscription
from .serializers import (
    SubscriptionsSerializer,
    UserAvatarSerializer,
    UserProfileSerializer,
    UserWithRecipesSerializer,
)

User = get_user_model()


class UserView(UserViewSet):
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

        if current_user == author_to_follow:
            return Response(
                {"detail": "You cannot subscribe to yourself"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.method == "POST":
            if Subscription.objects.filter(
                subscriber=current_user, author=author_to_follow
            ).exists():
                return Response(
                    {"detail": "You are already subscribed to this user"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            Subscription.objects.create(
                subscriber=current_user, author=author_to_follow
            )
            serializer = UserWithRecipesSerializer(
                author_to_follow, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == "DELETE":
            subscription = Subscription.objects.filter(
                subscriber=current_user, author=author_to_follow
            )
            if not subscription.exists():
                return Response(
                    {"detail": "You are not subscribed to this user"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"])
    def subscriptions(self, request):
        subscriptions = request.user.subscriptions.select_related(
            "author"
        ).all()
        authors = [sub.author for sub in subscriptions]

        page = self.paginate_queryset(authors)
        if page is not None:
            serializer = SubscriptionsSerializer(
                page,
                many=True,
                context={"request": request},
            )
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionsSerializer(
            authors,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)

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
                {"detail": "Avatar not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
