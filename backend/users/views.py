from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.pagination import PageNumberPagination
from .models import Subscription
from .serializers import UserSerializer, TokenSerializer, PasswordResetSerializer, SubscriptionSerializer

User = get_user_model()

class SubscriptionsListView(APIView):
    """View for listing all user subscriptions"""
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get(self, request, *args, **kwargs):
        """List all subscriptions of the current user"""
        self.pagination_class.page_size = 6
        self.pagination_class.page_size_query_param = "limit"
        self.pagination_class.max_page_size = 100

        # Get all users the current user is subscribed to
        subscriptions = User.objects.filter(
            subscribers__subscriber=request.user
        ).order_by('username')

        # Apply pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(subscriptions, request)

        # Get recipes_limit from query params
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            try:
                recipes_limit = int(recipes_limit)
                if recipes_limit < 0:
                    recipes_limit = None
            except (ValueError, TypeError):
                recipes_limit = None

        # Serialize with context for recipes_limit
        serializer = SubscriptionSerializer(
            page,
            many=True,
            context={'request': request, 'recipes_limit': recipes_limit}
        )

        return paginator.get_paginated_response(serializer.data)

User = get_user_model()


class UserView(APIView):
    """View for user registration and listing"""

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """List users with pagination"""
        queryset = User.objects.all()
        paginator = PageNumberPagination()
        paginator.page_size = 6
        paginator.page_size_query_param = "limit"
        paginator.max_page_size = 100
        page = paginator.paginate_queryset(queryset, request)

        serializer = UserSerializer(
            page,
            many=True,
            context={"request": request, "action": "list"}
        )
        return paginator.get_paginated_response(serializer.data)

    def post(self, request, *args, **kwargs):
        """Create a new user"""
        serializer = UserSerializer(
            data=request.data,
            context={"action": "create"}
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
    """View for retrieving a single user"""

    permission_classes = [AllowAny]

    def get(self, request, user_id, *args, **kwargs):
        """Retrieve a single user by ID"""
        try:
            user = User.objects.get(id=user_id)
            serializer = UserSerializer(user, context={"request": request})
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)


class CustomTokenCreateView(APIView):
    """View for token authentication"""

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """Create authentication token"""
        serializer = TokenSerializer(data=request.data)
        if serializer.is_valid():
            return Response(
                data={"auth_token": serializer.validated_data["auth_token"]},
                status=status.HTTP_200_OK,
            )
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenDestroyView(APIView):
    """View for token deletion"""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Delete user's authentication token"""
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CurrentUserView(APIView):
    """View for retrieving current authenticated user"""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Retrieve current authenticated user"""
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(serializer.data)


class SubscriptionView(APIView):
    """View for managing user subscriptions"""
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id, *args, **kwargs):
        """Subscribe to a user"""
        try:
            author = User.objects.get(id=user_id)
            if request.user == author:
                return Response(
                    {"detail": "Cannot subscribe to yourself"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            subscription, created = Subscription.objects.get_or_create(
                subscriber=request.user,
                author=author
            )

            if not created:
                return Response(
                    {"detail": "Already subscribed"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get recipes_limit from query params
            recipes_limit = request.query_params.get('recipes_limit')
            if recipes_limit:
                try:
                    recipes_limit = int(recipes_limit)
                    if recipes_limit < 0:
                        recipes_limit = None
                except (ValueError, TypeError):
                    recipes_limit = None

            serializer = SubscriptionSerializer(
                author,
                context={'request': request, 'recipes_limit': recipes_limit}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except User.DoesNotExist:
            return Response(
                {"detail": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, user_id, *args, **kwargs):
        """Unsubscribe from a user"""
        try:
            author = User.objects.get(id=user_id)
            if request.user == author:
                return Response(
                    {"detail": "Cannot unsubscribe from yourself"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            subscription = Subscription.objects.filter(
                subscriber=request.user,
                author=author
            ).first()

            if not subscription:
                return Response(
                    {"detail": "Not subscribed"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        except User.DoesNotExist:
            return Response(
                {"detail": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class PasswordResetView(APIView):
    """View for password reset"""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Update user's password"""
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            current_password = serializer.validated_data.get('current_password')
            new_password = serializer.validated_data.get('new_password')

            # Check if current password is correct
            if not request.user.check_password(current_password):
                return Response(
                    {"current_password": ["Current password is incorrect"]},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update password
            request.user.set_password(new_password)
            request.user.save()

            # Invalidate existing token
            Token.objects.filter(user=request.user).delete()

            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AvatarView(APIView):
    """View for updating user avatar"""

    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        """Update user avatar"""
        return self.update_avatar(request)

    def patch(self, request, *args, **kwargs):
        """Update user avatar"""
        return self.update_avatar(request)

    def update_avatar(self, request):
        """Common method for updating avatar"""
        if "avatar" not in request.data:
            return Response(
                {"detail": "Avatar field is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = UserSerializer(
            request.user, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"avatar": serializer.data.get("avatar")}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        """Remove user avatar"""
        request.user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
