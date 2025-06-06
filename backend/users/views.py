from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Subscription
from .serializers import (
    PasswordResetSerializer,
    SubscriptionSerializer,
    TokenSerializer,
    UserSerializer,
)

User = get_user_model()


class SubscriptionsListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get(self, request, *args, **kwargs):
        self.pagination_class.page_size = 6
        self.pagination_class.page_size_query_param = "limit"
        self.pagination_class.max_page_size = 100

        subscriptions = request.user.subscriptions.all().order_by(
            "author__username"
        )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(subscriptions, request)

        recipes_limit = request.query_params.get("recipes_limit")
        if recipes_limit:
            try:
                recipes_limit = int(recipes_limit)
                if recipes_limit < 0:
                    recipes_limit = None
            except (ValueError, TypeError):
                recipes_limit = None

        serializer = SubscriptionSerializer(
            page,
            many=True,
            context={"request": request, "recipes_limit": recipes_limit},
        )

        return paginator.get_paginated_response(serializer.data)


User = get_user_model()


class UserView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        queryset = User.objects.all()
        paginator = PageNumberPagination()
        paginator.page_size = 6
        paginator.page_size_query_param = "limit"
        paginator.max_page_size = 100
        page = paginator.paginate_queryset(queryset, request)

        serializer = UserSerializer(
            page, many=True, context={"request": request, "action": "list"}
        )
        return paginator.get_paginated_response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = UserSerializer(
            data=request.data, context={"action": "create"}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                data=serializer.data,
                status=status.HTTP_201_CREATED,
            )
        return Response(
            data=serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class SingleUserView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id, *args, **kwargs):
        try:
            user = User.objects.get(id=user_id)
            serializer = UserSerializer(user, context={"request": request})
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND
            )


class CustomTokenCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = TokenSerializer(data=request.data)
        if serializer.is_valid():
            return Response(
                data={"auth_token": serializer.validated_data["auth_token"]},
                status=status.HTTP_200_OK,
            )
        return Response(
            data=serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )


class CustomTokenDestroyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        request.user.auth_token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(serializer.data)


class SubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id, *args, **kwargs):
        try:
            author = User.objects.get(id=user_id)
            if request.user == author:
                return Response(
                    {"detail": "Cannot subscribe to yourself"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            subscription, created = Subscription.objects.get_or_create(
                subscriber=request.user, author=author
            )

            if not created:
                return Response(
                    {"detail": "Already subscribed"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            recipes_limit = request.query_params.get("recipes_limit")
            if recipes_limit:
                try:
                    recipes_limit = int(recipes_limit)
                    if recipes_limit < 0:
                        recipes_limit = None
                except (ValueError, TypeError):
                    recipes_limit = None

            subscription = request.user.subscriptions.filter(
                author=author
            ).first()

            if not subscription:
                subscription = Subscription.objects.create(
                    subscriber=request.user, author=author
                )

            serializer = SubscriptionSerializer(
                subscription,
                context={"request": request, "recipes_limit": recipes_limit},
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except User.DoesNotExist:
            return Response(
                {"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, user_id, *args, **kwargs):
        try:
            author = User.objects.get(id=user_id)
            if request.user == author:
                return Response(
                    {"detail": "Cannot unsubscribe from yourself"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            subscription = request.user.subscriptions.filter(
                author=author
            ).first()

            if not subscription:
                return Response(
                    {"detail": "Not subscribed"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        except User.DoesNotExist:
            return Response(
                {"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )


class PasswordResetView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            current_password = serializer.validated_data.get(
                "current_password"
            )
            new_password = serializer.validated_data.get("new_password")

            if not request.user.check_password(current_password):
                return Response(
                    {"current_password": ["Current password is incorrect"]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            request.user.set_password(new_password)
            request.user.save()

            request.user.auth_token.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AvatarView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        return self.update_avatar(request)

    def patch(self, request, *args, **kwargs):
        return self.update_avatar(request)

    def update_avatar(self, request):
        if "avatar" not in request.data:
            return Response(
                {"detail": "Avatar field is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"avatar": serializer.data.get("avatar")},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        request.user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
