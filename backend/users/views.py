from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from .serializers import UserSerializer, TokenSerializer

User = get_user_model()


class CustomUserCreateView(APIView):
    """View for user registration"""

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """Create a new user"""
        serializer = UserSerializer(data=request.data)
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
